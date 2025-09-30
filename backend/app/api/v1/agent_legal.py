# File: backend/app/api/v1/agent_legal.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.models import embedding_model, gemini_model
from app.infrastructure.database.elasticsearch_connector import es_client

# Import a shared request model if needed, or define locally
class QueryRequest(BaseModel):
    query: str
    user_id: str | None = None

LEGAL_INDEX_NAME = "umkm_legal_docs"

# Pydantic models specific to this agent
class SourceChunk(BaseModel):
    chunk_id: str
    chapter_title: str
    text: str
    score: float

class LegalQueryResponse(BaseModel):
    answer: str
    retrieved_chunks: list[SourceChunk]

# Create a new APIRouter instance for this agent
router = APIRouter()

@router.post("/query", response_model=LegalQueryResponse)
async def ask_legal_agent(request: QueryRequest):
    """
    Receives a query, performs hybrid search, and uses Gemini to generate
    a final answer based on the retrieved context (full RAG loop).
    """
    if not es_client:
        raise HTTPException(status_code=503, detail="Elasticsearch client is not available.")
    
    query_embedding = embedding_model.encode(request.query).tolist()
    hybrid_query = { "query": { "match": { "text": { "query": request.query } } }, "knn": { "field": "embedding", "query_vector": query_embedding, "k": 5, "num_candidates": 50 } }
    
    try:
        response = es_client.search(index=LEGAL_INDEX_NAME, body=hybrid_query)
        retrieved_chunks = []; context_for_gemini = ""
        for hit in response['hits']['hits']:
            source = hit['_source']; chunk_text = source.get('text', '')
            context_for_gemini += f"--- Source: {source.get('chunk_id', '')} ---\n{chunk_text}\n\n"
            retrieved_chunks.append(SourceChunk(chunk_id=source.get('chunk_id', ''), chapter_title=source.get('chapter_title', ''), text=chunk_text, score=hit['_score']))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during search: {e}")

    prompt = f"""You are a helpful and professional legal assistant for Indonesian SMEs (UMKM). Your task is to answer the user's question based *only* on the provided context from Indonesian law documents. Do not use any external knowledge. If the answer is not available in the context, say so. Provide the answer in clear, easy-to-understand Indonesian.\n\nCONTEXT FROM LAW DOCUMENTS:\n{context_for_gemini}\n\nUSER'S QUESTION:\n{request.query}\n\nANSWER:"""
    
    try:
        generation_response = gemini_model.generate_content(prompt)
        final_answer = generation_response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred with the generation model: {e}")
        
    return LegalQueryResponse(answer=final_answer, retrieved_chunks=retrieved_chunks)