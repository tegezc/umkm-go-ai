# File: backend/app/api/v1/orchestrator.py
# Description: The master agent that routes queries to the correct specialist agent.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.models import gemini_model

from app.application.services import legal_agent_service, marketing_agent_service

class OrchestratorQueryRequest(BaseModel):
    query: str
    user_id: str | None = None

router = APIRouter()

@router.post("/query")
async def orchestrate_query(request: OrchestratorQueryRequest):
    """
    Receives a general query, uses Gemini to classify its intent,
    and then routes it to the appropriate agent service.
    """
    print(f"[*] ORCHESTRATOR: Received query: '{request.query}'")

    # Step 1: Use Gemini to classify the intent of the query
    
    # This is the "meta-prompt" or "router-prompt"
    classification_prompt = f"""
    You are an intelligent routing agent. Your task is to classify the user's query into one of the following categories: 'LEGAL', 'MARKETING', or 'UNKNOWN'.
    - 'LEGAL' is for questions about laws, regulations, permits, licenses, taxes, and legal business requirements.
    - 'MARKETING' is for questions about promotion, social media, branding, content ideas, and sales strategies.
    - 'UNKNOWN' is for anything else (e.g., casual conversation, operational questions about finance/HR, etc.).

    Respond with only one word: LEGAL, MARKETING, or UNKNOWN.

    User's query: "{request.query}"
    Classification:
    """

    try:
        print("[*] Classifying intent with Gemini...")
        response = gemini_model.generate_content(classification_prompt)
        intent = response.text.strip().upper()
        print(f"[+] Intent classified as: {intent}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during intent classification: {e}")

    # Step 2: Route to the appropriate agent based on the intent
    if intent == "LEGAL":
        try:
            result = await legal_agent_service.process_legal_query(request.query)
            result['agent_used'] = 'LEGAL'
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    elif intent == "MARKETING":
        try:
            result = await marketing_agent_service.process_marketing_query(request.query)
            result['agent_used'] = 'MARKETING'
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    else: # UNKNOWN
        return {"answer": "Sorry, I’m not able to answer that question yet. You can ask about legal or marketing aspects for SMEs.", "agent_used": "UNKNOWN"}