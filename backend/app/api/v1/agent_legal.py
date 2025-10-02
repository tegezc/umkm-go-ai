# File: backend/app/api/v1/agent_legal.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.application.services.legal_agent_service import process_legal_query

from app.core.models import embedding_model, gemini_model
from app.infrastructure.database.elasticsearch_connector import es_client

class QueryRequest(BaseModel):
    query: str
    user_id: str | None = None

LEGAL_INDEX_NAME = "umkm_legal_docs"

class SourceChunk(BaseModel):
    chunk_id: str
    chapter_title: str
    text: str
    score: float

class LegalQueryResponse(BaseModel):
    answer: str
    retrieved_chunks: list[SourceChunk]

router = APIRouter()

@router.post("/query", response_model=LegalQueryResponse)
async def ask_legal_agent(request: QueryRequest):
    """Endpoint for the Legal Agent, now calls the service layer."""
    try:
        result = await process_legal_query(request.query)
        return LegalQueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))