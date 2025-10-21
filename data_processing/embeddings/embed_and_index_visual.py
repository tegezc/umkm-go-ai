# File: data_processing/embeddings/embed_and_index_visual.py
# Description:
# Generates multimodal embeddings for images using Vertex AI and indexes
# the image path, category, tags, and embedding into a dedicated Elasticsearch index.

import os
import json
from vertexai import init
from vertexai.vision_models import MultiModalEmbeddingModel, Image as VertexImage
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
# from google.cloud import aiplatform # Vertex AI client
# from google.cloud.aiplatform.gapic.schema import predict
from PIL import Image as PILImage # To check image integrity if needed
from tqdm import tqdm
import base64 # To send image data to Vertex AI

# --- Configuration ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Input JSON file with tags and categories
JSON_INPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'processed_data')
JSON_INPUT_FILENAME = "image_tags_categorized.json"

# Root directory where the actual image files are stored (needed to load images)
IMAGE_ROOT_DIR = os.getenv("IMAGE_ROOT_DIR")

# Elasticsearch configuration
ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
INDEX_NAME = "umkm_visual_kb" # NEW index for the Visual Knowledge Base

# Vertex AI configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION")
# The specific Vertex AI endpoint for multimodal embeddings
VERTEX_ENDPOINT_ID = "multimodalembedding@001"
# Dimension of the embeddings produced by this model
EMBEDDING_DIMENSION = 1408

# --- Initialization ---
# Initialize Vertex AI client
try:
    print(f"[*] Initializing Vertex AI client for project '{GCP_PROJECT_ID}' in '{GCP_LOCATION}'...")

    # Inisialisasi koneksi Vertex AI
    init(project=GCP_PROJECT_ID, location=GCP_LOCATION)

    # Load model multimodal embedding
    embedding_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

    print("[+] Vertex AI client initialized successfully.")
except Exception as e:
    print(f"[!] Failed to initialize Vertex AI client: {e}")
    exit()

# Initialize Elasticsearch client (reusing the function)
def connect_to_elasticsearch(endpoint_url: str, api_key: str) -> Elasticsearch | None:
    print("[*] Connecting to Elasticsearch...")
    try:
        client = Elasticsearch(hosts=[endpoint_url], api_key=api_key)
        if client.ping(): print("[+] Successfully connected to Elasticsearch."); return client
        return None
    except Exception as e: print(f"[!] Connection error: {e}"); return None

es_client = connect_to_elasticsearch(ELASTIC_ENDPOINT, ELASTIC_API_KEY)
if not es_client: exit()


def create_visual_index(es_client: Elasticsearch, index_name: str):
    """Creates an Elasticsearch index with a mapping for visual data."""
    print(f"[*] Checking/Creating index '{index_name}'...")
    mapping = {
        "properties": {
            "file_path": {"type": "keyword"}, # Relative path to image
            "category": {"type": "keyword"},
            "tags": {"type": "keyword"},     # List of keywords
            "embedding": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIMENSION, # Dimension for multimodalembedding@001
                "index": True,               # Enable indexing for similarity search
                "similarity": "cosine"       # Use cosine similarity
            }
        }
    }
    try:
        if es_client.indices.exists(index=index_name):
            print(f"[*] Index '{index_name}' exists. Deleting for fresh start.")
            es_client.indices.delete(index=index_name)
        print(f"[*] Creating new index '{index_name}' with visual mapping.")
        es_client.indices.create(index=index_name, mappings=mapping)
        print("[+] Index created successfully.")
    except Exception as e: print(f"[!] Index creation error: {e}"); raise

def load_image_tags(filepath: str) -> dict:
    """Loads the categorized image tags from the JSON file."""
    print(f"[*] Loading image tags from: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e: print(f"[!] Error loading JSON: {e}"); return {}

def get_image_embedding(image_path: str) -> list[float] | None:
    """Gets multimodal embedding for a single image using Vertex AI."""
    try:
        vertex_image = VertexImage.load_from_file(image_path)
        embedding_response = embedding_model.get_embeddings(image=vertex_image)
        return embedding_response.image_embedding
    except Exception as e:
        print(f"\n[!] Error getting embedding for {os.path.basename(image_path)}: {e}")
        return None

if __name__ == "__main__":
    print("--- Starting Visual KB Embedding and Indexing Pipeline ---")

    try: create_visual_index(es_client, INDEX_NAME)
    except Exception: exit()

    image_tags_data = load_image_tags(os.path.join(JSON_INPUT_DIR, JSON_INPUT_FILENAME))
    if not image_tags_data: print("[!] No image tag data found. Exiting."); exit()

    print(f"[*] Processing {len(image_tags_data)} images for embedding and indexing...")
    
    for filename, data in tqdm(image_tags_data.items(), desc="Indexing Visual KB"):
        category = data.get("category", "unknown")
        tags = data.get("tags", [])
        
        # Construct the full path to the image file
        image_path = os.path.join(IMAGE_ROOT_DIR, category, filename)
        # Store relative path for easier reference if needed later
        relative_path = os.path.join(category, filename) 
        
        if not os.path.exists(image_path):
            print(f"\\n[!] Warning: Image file not found at {image_path}. Skipping.")
            continue
            
        # Get the image embedding from Vertex AI
        embedding = get_image_embedding(image_path)
        
        if embedding:
            # Prepare the document for Elasticsearch
            doc = {
                "file_path": relative_path,
                "category": category,
                "tags": tags,
                "embedding": embedding
            }
            
            # Index the document
            try:
                es_client.index(index=INDEX_NAME, document=doc)
            except Exception as e:
                print(f"\\n[!] Failed to index document for {filename}: {e}")
        else:
             print(f"\\n[!] Skipping document for {filename} due to embedding error.")

    print("\\n[+] Visual Knowledge Base indexing complete!")
    print("--- Pipeline Finished ---")