#
# embed_and_index.py
#
# Description:
# This script is the final step in the data pipeline. It performs the following:
# 1. Loads the structured JSON data created by the text_processor.
# 2. Connects to the Elastic Cloud cluster using credentials from a .env file.
# 3. Creates a new Elasticsearch index with a specific mapping designed for our data,
#    including a dense_vector field for embeddings.
# 4. Initializes a SentenceTransformer model to generate embeddings.
# 5. Iterates through each data chunk, generates its embedding, and indexes the
#    complete document (data + embedding) into Elasticsearch.
#

import os
import json
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm # For a nice progress bar

# --- Configuration ---
# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Input data configuration
INPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'processed_data')
INPUT_FILENAME = "uu_no_20_tahun_2008.json"

# Elasticsearch configuration
ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
INDEX_NAME = "umkm_legal_docs" # Name index in Elasticsearch

# Embedding model configuration
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
EMBEDDING_DIMENSION = 384 # Crucial: dimensions of the chosen model's vectors

# --- Functions ---

def connect_to_elasticsearch(endpoint_url: str, api_key: str) -> Elasticsearch | None:
    """Establishes a connection to the Elastic Cloud cluster via Endpoint URL."""
    print("[*] Connecting to Elasticsearch via Endpoint URL...")
    try:
        client = Elasticsearch(
            hosts=[endpoint_url],
            api_key=api_key
        )
        if client.ping():
            print("[+] Successfully connected to Elasticsearch.")
            return client
        else:
            print("[!] Could not connect to Elasticsearch.")
            return None
    except Exception as e:
        print(f"[!] An error occurred during connection: {e}")
        return None

def create_index_with_mapping(es_client: Elasticsearch, index_name: str):
    """Creates an Elasticsearch index with a specific mapping for our legal docs."""
    print(f"[*] Checking/Creating index '{index_name}'...")
    
    # Define the structure (mapping) of our index
    mapping = {
        "properties": {
            "source": {"type": "keyword"},
            "chunk_type": {"type": "keyword"},
            "chunk_id": {"type": "keyword"},
            "chapter_id": {"type": "keyword"},
            "chapter_title": {"type": "text"},
            "text": {"type": "text"},
            "embedding": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIMENSION # Must match the model's output dimension
            }
        }
    }
    
    try:
        # Delete the index if it already exists to start fresh
        if es_client.indices.exists(index=index_name):
            print(f"[*] Index '{index_name}' already exists. Deleting it.")
            es_client.indices.delete(index=index_name)
        
        # Create the new index with our defined mapping
        print(f"[*] Creating new index '{index_name}' with mapping.")
        es_client.indices.create(index=index_name, mappings=mapping)
        print("[+] Index created successfully.")
        
    except Exception as e:
        print(f"[!] An error occurred during index creation: {e}")
        raise # Stop the script if index creation fails

def load_processed_data(filepath: str) -> list[dict]:
    """Loads the structured chunks from the JSON file."""
    print(f"[*] Loading processed data from: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Error loading JSON file: {e}")
        return []

# --- Main Execution ---

def main():
    """Main function to run the embedding and indexing pipeline."""
    print("--- Starting Embedding and Indexing Pipeline ---")

    # Step 1: Connect to Elasticsearch
    es_client = connect_to_elasticsearch(ELASTIC_ENDPOINT, ELASTIC_API_KEY)
    if not es_client:
        return # Stop if connection fails

    # Step 2: Create the index with the correct mapping
    try:
        create_index_with_mapping(es_client, INDEX_NAME)
    except Exception:
        return # Stop if index creation fails

    # Step 3: Load the sentence transformer model
    print(f"[*] Loading embedding model: '{EMBEDDING_MODEL}'...")
    try:
        model = SentenceTransformer(EMBEDDING_MODEL)
        print("[+] Embedding model loaded successfully.")
    except Exception as e:
        print(f"[!] Failed to load embedding model: {e}")
        return

    # Step 4: Load our processed data
    chunks = load_processed_data(os.path.join(INPUT_DIR, INPUT_FILENAME))
    if not chunks:
        print("[!] No data to process.")
        return

    # Step 5: Generate embeddings and index documents
    print(f"[*] Starting to generate embeddings and index {len(chunks)} documents...")
    for chunk in tqdm(chunks, desc="Indexing Documents"):
        try:
            # Generate the embedding for the main text content
            text_to_embed = chunk.get("text", "")
            embedding = model.encode(text_to_embed)
            
            # Add the embedding to the document
            chunk['embedding'] = embedding.tolist()
            
            # Index the document into Elasticsearch
            es_client.index(index=INDEX_NAME, document=chunk)
            
        except Exception as e:
            print(f"\\n[!] Failed to process or index chunk {chunk.get('chunk_id')}: {e}")

    print("[+] All documents have been indexed successfully!")
    print("--- Pipeline Finished ---")

if __name__ == "__main__":
    main()