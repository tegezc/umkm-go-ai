#
# embed_and_index_marketing.py
#
# Description:
# This script takes the scraped marketing articles, generates a vector embedding for
# each article's content, and indexes the structured data (URL, title, content, embedding)
# into a new, dedicated Elasticsearch index.
#

import os
import json
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# --- Configuration ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Input data configuration
INPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'raw_data')
INPUT_FILENAME = "detik_solusiukm_articles.json" # Our new data file

# Elasticsearch configuration
ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
INDEX_NAME = "umkm_marketing_kb" # NEW index for the Marketing Knowledge Base

# Embedding model configuration (we use the same model for consistency)
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
EMBEDDING_DIMENSION = 384

def connect_to_elasticsearch(endpoint_url: str, api_key: str) -> Elasticsearch | None:
    """Establishes a connection to the Elastic Cloud cluster via Endpoint URL."""
    print("[*] Connecting to Elasticsearch...")
    try:
        client = Elasticsearch(hosts=[endpoint_url], api_key=api_key)
        if client.ping():
            print("[+] Successfully connected to Elasticsearch.")
            return client
        return None
    except Exception as e:
        print(f"[!] Connection error: {e}")
        return None

def create_marketing_index(es_client: Elasticsearch, index_name: str):
    """Creates an Elasticsearch index with a mapping for marketing articles."""
    print(f"[*] Checking/Creating index '{index_name}'...")
    
    # NEW mapping tailored for article data
    mapping = {
        "properties": {
            "url": {"type": "keyword"},
            "title": {
                "type": "text",
                "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }
            },
            "content": {"type": "text"},
            "embedding": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIMENSION
            }
        }
    }
    
    try:
        if es_client.indices.exists(index=index_name):
            print(f"[*] Index '{index_name}' already exists. Deleting it for a fresh start.")
            es_client.indices.delete(index=index_name)
        
        print(f"[*] Creating new index '{index_name}' with marketing mapping.")
        es_client.indices.create(index=index_name, mappings=mapping)
        print("[+] Index created successfully.")
        
    except Exception as e:
        print(f"[!] An error occurred during index creation: {e}")
        raise

def load_scraped_articles(filepath: str) -> list[dict]:
    """Loads the scraped articles from the JSON file."""
    print(f"[*] Loading scraped articles from: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Error loading JSON file: {e}")
        return []

# --- Main Execution ---

def main():
    """Main function to run the marketing data embedding and indexing pipeline."""
    print("--- Starting Marketing KB Embedding and Indexing Pipeline ---")

    es_client = connect_to_elasticsearch(ELASTIC_ENDPOINT, ELASTIC_API_KEY)
    if not es_client: return

    try:
        create_marketing_index(es_client, INDEX_NAME)
    except Exception: return

    print(f"[*] Loading embedding model: '{EMBEDDING_MODEL}'...")
    try:
        model = SentenceTransformer(EMBEDDING_MODEL)
        print("[+] Embedding model loaded.")
    except Exception as e:
        print(f"[!] Failed to load embedding model: {e}")
        return

    articles = load_scraped_articles(os.path.join(INPUT_DIR, INPUT_FILENAME))
    if not articles:
        print("[!] No articles to process.")
        return

    print(f"[*] Generating embeddings and indexing {len(articles)} articles...")
    for article in tqdm(articles, desc="Indexing Marketing Articles"):
        try:
            content_to_embed = article.get("content", "")
            if content_to_embed:
                embedding = model.encode(content_to_embed)
                article['embedding'] = embedding.tolist()
                
                # Index the complete article document
                es_client.index(index=INDEX_NAME, document=article)
            
        except Exception as e:
            print(f"\\n[!] Failed to process or index article '{article.get('title')}': {e}")

    print("[+] All articles have been indexed successfully into the Marketing Knowledge Base!")
    print("--- Pipeline Finished ---")

if __name__ == "__main__":
    main()