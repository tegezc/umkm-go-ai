# File: backend/app/core/models.py
# Description: Centralized module for initializing and holding shared models.

import vertexai
from vertexai.generative_models import GenerativeModel
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

# Load .env from the parent 'backend' directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# --- Configuration ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "asia-southeast2")
EMBEDDING_MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'

# --- Initialization ---
# This code runs only once when the application starts.

print("[*] CORE: Initializing Vertex AI...")
vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
print("[+] CORE: Vertex AI initialized.")

print(f"[*] CORE: Loading embedding model: '{EMBEDDING_MODEL_NAME}'...")
# embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
embedding_model = SentenceTransformer('/app/embedding_model_files')
print("[+] CORE: Embedding model loaded.")

print("[*] CORE: Loading Gemini model...")
gemini_model = GenerativeModel("gemini-2.5-pro")
print("[+] CORE: Gemini model loaded.")