# File: backend/app/api/v1/agent_brand.py

import base64
import re
import json
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from app.core.models import gemini_model
from vertexai.generative_models import Part, GenerationConfig

# --- Configuration
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

# --- Helper


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


@router.post("/generate_kit", response_model=BrandAgentResponse)
async def generate_brand_kit(
    business_name: str = "My UMKM",
    file: UploadFile = File(...)
):
    print(
        f"[*] BRAND AGENT: Received image '{file.filename}' for business '{business_name}'")

    if not gemini_model:
        raise HTTPException(
            status_code=503, detail="Generative Model is not available.")
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload an image.")

    image_bytes = await file.read()
    image_part = Part.from_data(data=image_bytes, mime_type=file.content_type)

    # --- Step 1: Brand Analysis & Concept
    print("[*] Step 1: Analyzing image and generating concepts with shared Gemini model...")
    prompt = f"""
    Analyze the attached image of a product for a new UMKM business named "{business_name}".
    Based *only* on the visual information in the image, provide a full brand kit.

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
          "A logo concept description based on the image's style and elements",
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

        response = gemini_model.generate_content(
            [image_part, prompt],
            generation_config=generation_config
        )
        gemini_response_data = extract_json_from_text(response.text)
        if not gemini_response_data:
            raise ValueError(
                "No valid JSON from Gemini. Raw: " + response.text)

        image_analysis_data = gemini_response_data.get("image_analysis", {})
        brand_identity_data = gemini_response_data.get("brand_identity", {})
        image_analysis_result = ImageAnalysis(
            **image_analysis_data)  # Langsung unpack
        print(f"[+] Gemini Analysis Results: {image_analysis_result.labels}")

    except Exception as e:
        print(f"[!] Gemini Generation Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Gemini generation failed: {e}")

    # --- Step 2: Visual Inspiration
    print("[*] Step 2: Finding visual inspiration (Placeholder)...")
    visual_inspirations_result = [VisualInspiration(
        category="logos", file_path="mock/logo.png", tags=["mock_tag"])]

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
