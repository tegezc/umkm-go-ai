# File: backend/app/api/v1/agent_marketing.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.application.services.marketing_agent_service import process_marketing_query
from app.core.models import embedding_model, gemini_model
from app.infrastructure.database.elasticsearch_connector import es_client

class QueryRequest(BaseModel):
    query: str
    user_id: str | None = None

MARKETING_INDEX_NAME = "umkm_marketing_kb"

class SourceArticle(BaseModel):
    title: str
    url: str
    score: float

class MarketingQueryResponse(BaseModel):
    answer: str
    retrieved_articles: list[SourceArticle]

router = APIRouter()

@router.post("/query", response_model=MarketingQueryResponse)
async def ask_marketing_agent(request: QueryRequest):
    """Endpoint for the Marketing Agent, now calls the service layer."""
    try:
        result = await process_marketing_query(request.query)
        return MarketingQueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))