# File: backend/app/infrastructure/database/elasticsearch_connector.py
# Description: Manages the connection to the Elasticsearch cluster.

import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# Load environment variables from .env file in the backend directory
load_dotenv()

class ElasticsearchConnector:
    """A singleton class to manage the Elasticsearch client connection."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("[*] Creating new Elasticsearch client instance...")
            try:
                cls._instance = super(ElasticsearchConnector, cls).__new__(cls)
                
                endpoint = os.getenv("ELASTIC_ENDPOINT")
                api_key = os.getenv("ELASTIC_API_KEY")

                if not endpoint or not api_key:
                    raise ValueError("ELASTIC_ENDPOINT and ELASTIC_API_KEY must be set in .env file")

                cls.client = Elasticsearch(
                    hosts=[endpoint],
                    api_key=api_key
                )
                if not cls.client.ping():
                    raise ConnectionError("Could not connect to Elasticsearch.")
                
                print("[+] Elasticsearch client initialized and connected.")

            except Exception as e:
                print(f"[!] Failed to connect to Elasticsearch: {e}")
                cls._instance = None # Ensure instance is not set on failure
                
        return cls._instance

    def get_client(self) -> Elasticsearch:
        """Returns the active Elasticsearch client."""
        return self.client

# Create a single, reusable instance of the connector
es_connector = ElasticsearchConnector()
es_client = es_connector.get_client() if es_connector._instance else None