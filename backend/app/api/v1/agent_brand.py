# File: backend/app/api/v1/agent_brand.py (Final Integration)

import base64
import re
import json
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from app.core.models import gemini_model  # Shared Gemini
from app.infrastructure.database.elasticsearch_connector import es_client
# For embedding
from vertexai.vision_models import MultiModalEmbeddingModel, Image as VertexImage
from vertexai.generative_models import Part, GenerationConfig  # For Gemini call

# --- Model Embedding Initialization
try:
    print("[*] BRAND AGENT: Loading Multimodal Embedding Model...")
    embedding_model = MultiModalEmbeddingModel.from_pretrained(
        "multimodalembedding@001")
    print("[+] BRAND AGENT: Multimodal Embedding Model loaded.")
except Exception as e:
    print(f"[!] BRAND AGENT: Failed to load embedding model: {e}")
    embedding_model = None

# --- Configuration ---
VISUAL_KB_INDEX = "umkm_visual_kb"

# --- Pydantic Models
class ImageAnalysis(BaseModel):
    labels: List[str]
    dominant_colors: List[str]


class VisualInspiration(BaseModel):
    category: str
    file_path: str
    tags: List[str]


class LogoConcept(BaseModel):
    description: str
    image_url: Optional[str] = None


class BrandKit(BaseModel):
    suggested_names: List[str]
    suggested_taglines: List[str]
    logo_concepts: List[LogoConcept]
    instagram_bio: str
    image_analysis: ImageAnalysis
    visual_inspirations: List[VisualInspiration]


class BrandAgentResponse(BaseModel):
    status: str
    brand_kit: Optional[BrandKit] = None


# --- APIRouter Instance ---
router = APIRouter()

# --- Helper Functions
def extract_json_from_text(text: str) -> Optional[dict]:
    match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(1)
    else:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        json_str = match.group(0)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"[!] Helper: Failed decode: {e}")
        return None


def get_image_embedding_bytes(image_bytes: bytes) -> list[float] | None:
    if not embedding_model:
        return None
    try:
        vertex_image = VertexImage(image_bytes=image_bytes)
        embedding_response = embedding_model.get_embeddings(image=vertex_image)
        return embedding_response.image_embedding
    except Exception as e:
        print(f"[!] Helper: Error getting embedding: {e}")
        return None


@router.post("/generate_kit", response_model=BrandAgentResponse)
async def generate_brand_kit(
    business_name: str = "My UMKM",
    file: UploadFile = File(...)
):
    print(
        f"[*] BRAND AGENT: Received image '{file.filename}' for business '{business_name}'")
    if not gemini_model:
        raise HTTPException(
            status_code=503, detail="Generative Model not available.")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    image_bytes = await file.read()
    image_part = Part.from_data(data=image_bytes, mime_type=file.content_type)

    # --- Step 1a: Initial Analysis
    initial_analysis_prompt = """
    Analyze the attached image. Provide ONLY a comma-separated list of up to 5 relevant single-word tags describing the main objects and attributes. Example: food, bottle, spicy, traditional, red
    """
    try:
        initial_response = gemini_model.generate_content(
            [image_part, initial_analysis_prompt])
        initial_labels = [tag.strip().lower()
                          for tag in initial_response.text.split(',') if tag.strip()]
        if not initial_labels:
            initial_labels = ["product"]
        print(f"[+] Initial labels from Gemini: {initial_labels}")
    except Exception as e:
        print(
            f"[!] Initial Gemini analysis failed: {e}. Using fallback labels.")
        initial_labels = ["product"]

    # --- Step 2: Visual Inspiration
    print("[*] Step 2: Finding visual inspiration in Elasticsearch...")
    visual_inspirations_result = []
    try:
        input_image_embedding = get_image_embedding_bytes(image_bytes)
        search_tags = initial_labels

        if input_image_embedding and search_tags:
            knn_query = {
                "field": "embedding", "query_vector": input_image_embedding, "k": 5, "num_candidates": 50,
                "filter": {"terms": {"tags": search_tags}}
            }
            response = es_client.search(index=VISUAL_KB_INDEX, knn=knn_query, size=3,
                                        _source=["category", "file_path", "tags"])

            for hit in response['hits']['hits']:
                source = hit['_source']
                visual_inspirations_result.append(
                    VisualInspiration(**source))
            print(
                f"[+] Found {len(visual_inspirations_result)} visual inspirations via KNN.")
        else:
            print(
                "[!] Skipping Elasticsearch search: Missing input embedding or search tags.")
    except Exception as e:
        print(f"[!] Elasticsearch Search Error: {e}")  # Non-critical

    # --- Step 1b: Brand Concept Generation---
    print("[*] Step 1b: Generating full brand concepts with Gemini (with inspiration)...")

    inspiration_context = ""
    if visual_inspirations_result:
        inspiration_context += "\n\nConsider these visual inspirations found based on the product image:\n"
        for insp in visual_inspirations_result:
            inspiration_context += f"- A {insp.category} example with themes like: {', '.join(insp.tags[:3])}\n"

    final_prompt = f"""
    Analyze the attached image of a product for a new UMKM business named "{business_name}".
    Based on the visual information in the image AND considering the visual inspiration context provided below, provide a full brand kit.
    {inspiration_context}
    Your response MUST be in the following JSON format. Do not add any text outside the JSON block.
    ```json
    {{
      "image_analysis": {{
        "labels": ["label1", "label2", "label3", "A descriptive label", "Another label"],
        "dominant_colors": ["main color 1", "complementary color 2", "accent color 3"]
      }},
      "brand_identity": {{
        "suggested_names": ["Brand Name 1", "Brand Name 2", "Brand Name 3"],
        "suggested_taglines": ["Tagline 1 that fits the product", "Tagline 2"],
        "logo_concepts_desc": [
          "A logo concept description based on the image's style and elements, considering the inspiration context",
          "A second, different logo concept description"
        ],
        "instagram_bio": "A short, catchy Instagram bio for this product. Max 150 chars."
      }}
    }}
    ```
    """
    try:
        generation_config = GenerationConfig(
            response_mime_type="application/json")
        final_response = gemini_model.generate_content(
            [image_part, final_prompt],
            generation_config=generation_config
        )
        gemini_response_data = extract_json_from_text(final_response.text)
        if not gemini_response_data:
            raise ValueError(
                "No valid JSON from final Gemini call. Raw: " + final_response.text)

        image_analysis_data = gemini_response_data.get("image_analysis", {})
        brand_identity_data = gemini_response_data.get("brand_identity", {})
        image_analysis_result = ImageAnalysis(**image_analysis_data)
        print(
            f"[+] Final Gemini Analysis Results: {image_analysis_result.labels}")

    except Exception as e:
        print(f"[!] Final Gemini Generation Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Final Gemini generation failed: {e}")

    # --- Step 3: Logo Image
    print("[*] Step 3: Generating logo images (Placeholder)...")
    logo_concepts_final = []
    logo_descs = brand_identity_data.get("logo_concepts_desc", [])
    for desc in logo_descs:
        logo_concepts_final.append(LogoConcept(
            description=desc, image_url="https://via.placeholder.com/150"))

   # --- Step 4: Assemble Brand Kit
    final_brand_kit = BrandKit(
        suggested_names=brand_identity_data.get("suggested_names", []),
        suggested_taglines=brand_identity_data.get("suggested_taglines", []),
        logo_concepts=logo_concepts_final,
        instagram_bio=brand_identity_data.get(
            "instagram_bio", "Bio generated by AI"),
        image_analysis=image_analysis_result,
        visual_inspirations=visual_inspirations_result
    )

    return BrandAgentResponse(status="success", brand_kit=final_brand_kit)
