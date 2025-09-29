# File: backend/main.py (v1 - RAG with Gemini)
# Description: Final version for the Legal Agent, integrating Gemini for response generation.

import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import vertexai
from vertexai.generative_models import GenerativeModel

# Import our Elasticsearch client
from app.infrastructure.database.elasticsearch_connector import es_client

load_dotenv()

# --- Configuration ---
INDEX_NAME = os.getenv("INDEX_NAME")
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION") 

# --- Initialize Models & Clients ---

# Initialize Vertex AI
print("[*] Initializing Vertex AI...")
vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
print("[+] Vertex AI initialized.")

# Load the embedding model at startup
print("[*] Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)
print("[+] Embedding model loaded.")

# Load the Gemini model
print("[*] Loading Gemini model...")
gemini_model = GenerativeModel("gemini-2.5-pro")
print("[+] Gemini model loaded.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="UMKM-Go AI Backend",
    description="API for the UMKM-Go AI multi-agent system.",
    version="1.0.0",
)

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str
    user_id: str | None = None

class SourceChunk(BaseModel):
    chunk_id: str
    chapter_title: str
    text: str
    score: float

class LegalQueryResponse(BaseModel):
    answer: str # The final, generated answer from Gemini
    retrieved_chunks: list[SourceChunk]

# --- API Endpoints ---

@app.get("/", tags=["Health Check"])
async def read_root():
    return {"message": "Welcome to the UMKM-Go AI Backend! The server is running."}


@app.post("/api/v1/agent/legal/query", tags=["Agents"], response_model=LegalQueryResponse)
async def ask_legal_agent(request: QueryRequest):
    """
    Receives a query, performs hybrid search, and uses Gemini to generate
    a final answer based on the retrieved context (full RAG loop).
    """
    if not es_client:
        raise HTTPException(status_code=503, detail="Elasticsearch client is not available.")

    print(f"[*] Received query: '{request.query}'")

    # Step 1: Generate embedding for the query (Retrieval)
    query_embedding = model.encode(request.query).tolist()

    # Step 2: Perform hybrid search in Elasticsearch (Retrieval)
    hybrid_query = { "query": { "match": { "text": { "query": request.query } } }, "knn": { "field": "embedding", "query_vector": query_embedding, "k": 5, "num_candidates": 50 } }
    
    try:
        response = es_client.search(index=INDEX_NAME, body=hybrid_query)
        
        # Process search results
        retrieved_chunks = []
        context_for_gemini = ""
        for hit in response['hits']['hits']:
            source = hit['_source']
            chunk_text = source.get('text', '')
            
            # Append text to the context string
            context_for_gemini += f"--- Source: {source.get('chunk_id', '')} ---\\n{chunk_text}\\n\\n"
            
            # Format for the response model
            retrieved_chunks.append(SourceChunk(
                chunk_id=source.get('chunk_id', ''),
                chapter_title=source.get('chapter_title', ''),
                text=chunk_text,
                score=hit['_score']
            ))
        print(f"[+] Found {len(retrieved_chunks)} relevant chunks.")

    except Exception as e:
        print(f"[!] An error occurred during Elasticsearch search: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during search: {e}")

    # Step 3: Generate the answer using Gemini (Generation)
    print("[*] Generating final answer with Gemini...")

    # This is our Prompt Engineering
    prompt = f"""
    You are a helpful and professional legal assistant for Indonesian SMEs (UMKM).
    Your task is to answer the user's question based *only* on the provided context from Indonesian law documents.
    Do not use any external knowledge. If the answer is not available in the context, say so.
    Provide the answer in clear, easy-to-understand Indonesian.

    CONTEXT FROM LAW DOCUMENTS:
    {context_for_gemini}

    USER'S QUESTION:
    {request.query}

    ANSWER:
    """

    try:
        # Generate content
        generation_response = gemini_model.generate_content(prompt)
        final_answer = generation_response.text
        print("[+] Gemini finished generating the answer.")
        
    except Exception as e:
        print(f"[!] An error occurred while generating content with Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred with the generation model: {e}")

    return LegalQueryResponse(
        answer=final_answer,
        retrieved_chunks=retrieved_chunks
    )