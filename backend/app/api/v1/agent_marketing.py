# File: backend/app/api/v1/agent_marketing.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.models import embedding_model, gemini_model
from app.infrastructure.database.elasticsearch_connector import es_client

# Import a shared request model
class QueryRequest(BaseModel):
    query: str
    user_id: str | None = None

MARKETING_INDEX_NAME = "umkm_marketing_kb"

# Pydantic models specific to this agent
class SourceArticle(BaseModel):
    title: str
    url: str
    score: float

class MarketingQueryResponse(BaseModel):
    answer: str
    retrieved_articles: list[SourceArticle]

# Create a new APIRouter instance for this agent
router = APIRouter()

@router.post("/query", response_model=MarketingQueryResponse)
async def ask_marketing_agent(request: QueryRequest):
    """
    Receives a query for the Marketing Agent, performs hybrid search on the
    marketing knowledge base, and uses Gemini to generate marketing advice.
    """
    if not es_client:
        raise HTTPException(status_code=503, detail="Elasticsearch client is not available.")

    query_embedding = embedding_model.encode(request.query).tolist()
    hybrid_query = { "query": { "match": { "content": { "query": request.query } } }, "knn": { "field": "embedding", "query_vector": query_embedding, "k": 3, "num_candidates": 20 } }
    
    try:
        response = es_client.search(index=MARKETING_INDEX_NAME, body=hybrid_query)
        retrieved_articles = []; context_for_gemini = ""
        for hit in response['hits']['hits']:
            source = hit['_source']
            context_for_gemini += f"--- Source Article: {source.get('title', '')} ---\n{source.get('content', '')}\n\n"
            retrieved_articles.append(SourceArticle(title=source.get('title', ''), url=source.get('url', ''), score=hit['_score']))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during marketing search: {e}")

    prompt = f"""You are a creative and helpful marketing consultant for Indonesian SMEs (UMKM). Your task is to answer the user's question and provide actionable, creative marketing ideas. Base your answer primarily on the provided context of marketing articles. Provide the answer in Indonesian, using a friendly and encouraging tone.\n\nCONTEXT FROM MARKETING ARTICLES:\n{context_for_gemini}\n\nUSER'S QUESTION:\n{request.query}\n\nMARKETING ADVICE:"""
    
    try:
        generation_response = gemini_model.generate_content(prompt)
        final_answer = generation_response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred with the generation model: {e}")
        
    return MarketingQueryResponse(answer=final_answer, retrieved_articles=retrieved_articles)