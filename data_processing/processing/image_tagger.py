# File: data_processing/processing/image_tagger.py
# Description:
# Uses Vertex AI Vision API to tag images found recursively within a root directory
# containing subfolders for different image categories (logos, packaging, palettes).

import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Image as VertexImage, Part
from vertexai.vision_models import Image
from vertexai.preview.generative_models import GenerativeModel, Part
from tqdm import tqdm
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- Configuration ---
# NOW points to the PARENT directory containing the subfolders
IMAGE_ROOT_DIR = os.getenv("IMAGE_ROOT_DIR")
JSON_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'processed_data')
JSON_OUTPUT_FILENAME = "image_tags_categorized.json"

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = "us-central1"

CONFIDENCE_THRESHOLD = 0.6
MAX_LABELS = 10
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')

# --- Initialization (same as before) ---
try:
    print(f"[*] Initializing Vertex AI...")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
    # labeling_model = ImageLabelingModel.from_pretrained("imagetext@001")
    print("[+] Vertex AI initialized.")
except Exception as e:
    print(f"[!] Failed to initialize Vertex AI: {e}"); exit()

# --- Main Logic ---

def find_image_files_recursively(root_directory: str) -> list[tuple[str, str]]:
    """
    Finds all supported image files recursively within a directory and its subfolders.
    Returns a list of tuples: (category, full_path).
    """
    image_files = []
    print(f"[*] Recursively searching for image files in: {root_directory}")
    try:
        for subdir, _, files in os.walk(root_directory):
            category = os.path.basename(subdir) # Get the subfolder name as category
            # Ensure we don't process the root directory itself if it contains images
            if subdir == root_directory:
                 category = "uncategorized" # Or skip, depending on preference

            for filename in files:
                if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                    full_path = os.path.join(subdir, filename)
                    image_files.append((category, full_path))
                    
    except FileNotFoundError:
        print(f"[!] Error: Root directory not found at {root_directory}")
    except Exception as e:
        print(f"[!] Error walking directory: {e}")
        
    print(f"[+] Found {len(image_files)} image files across subfolders.")
    return image_files

def get_image_labels(image_path: str, max_tags: int = 8) -> list[str]:
    """
    Using a GenerativeModel (vision-capable Gemini) to generate tags.
    Returns a list of string tags (e.g. ['logo', 'bottle', 'label']).
    """
    try:
        model = GenerativeModel("gemini-2.5-pro")

        vertex_image = VertexImage.load_from_file(image_path)
        image_part = Part.from_image(vertex_image)

        # Prompt:  N tag, output as comma-separated list
        prompt = (
            f"Provide up to {max_tags} short, single-word visual tags describing the main "
            "objects, scene, and attributes visible in the image. "
            "Respond **only** with a comma-separated list of tags, no extra explanation. "
            "Examples: 'logo,drink,bottle,label' "
            "If uncertain, prefer generic tags (e.g., 'food', 'logo', 'packaging')."
        )

        response = model.generate_content([image_part, prompt])

        text = response.text.strip()
        if not text:
            return []

        raw_tags = [t.strip().lower() for t in text.replace("\n", ",").split(",") if t.strip()]
        # Dedup while preserving order
        seen = set()
        tags = []
        for t in raw_tags:
            if t not in seen:
                tags.append(t)
                seen.add(t)
            if len(tags) >= max_tags:
                break

        return tags

    except Exception as e:
        print(f"\n[!] Error processing image {os.path.basename(image_path)}: {e}")
        return []

def save_categorized_results(results: dict, directory: str, filename: str):
    """Saves the categorized tagging results to JSON."""
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    print(f"\\n[*] Saving categorized results to: {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("[+] Results saved successfully.")
    except Exception as e:
        print(f"[!] Error saving JSON: {e}")

# --- Main Execution ---

if __name__ == "__main__":
    print("--- Starting Image Auto-Tagging Script ---")
    
    # 1. Find image files recursively
    image_data = find_image_files_recursively(IMAGE_ROOT_DIR)
    
    if not image_data:
        print("[!] No image files found. Exiting.")
    else:
        # 2. Process each image, now including category
        tagging_results = {}
        for category, img_path in tqdm(image_data, desc="Tagging Images"):
            filename = os.path.basename(img_path)
            labels = get_image_labels(img_path)
            if labels:
                # Store results with category
                tagging_results[filename] = {
                    "category": category,
                    "tags": labels
                }
        
        # 3. Save the results
        save_categorized_results(tagging_results, JSON_OUTPUT_DIR, JSON_OUTPUT_FILENAME)

    print("--- Image Tagging Script Finished ---")