# File: backend/app/application/services/marketing_agent_service.py
# Description: Contains the core business logic for the Marketing Agent.

from app.core.models import embedding_model, gemini_model
from app.infrastructure.database.elasticsearch_connector import es_client

MARKETING_INDEX_NAME = "umkm_marketing_kb"

async def process_marketing_query(query: str) -> dict:
    """
    Handles the entire RAG process for a marketing query.
    """
    if not es_client:
        raise Exception("Elasticsearch client is not available.")

    # Step 1: Generate embedding and perform hybrid search
    query_embedding = embedding_model.encode(query).tolist()
    hybrid_query = { "query": { "match": { "content": { "query": query } } }, "knn": { "field": "embedding", "query_vector": query_embedding, "k": 3, "num_candidates": 20 } }
    
    response = es_client.search(index=MARKETING_INDEX_NAME, body=hybrid_query)
    
    retrieved_articles = []; context_for_gemini = ""
    for hit in response['hits']['hits']:
        source = hit['_source']
        context_for_gemini += f"--- Source Article: {source.get('title', '')} ---\n{source.get('content', '')}\n\n"
        retrieved_articles.append({
            "title": source.get('title', ''),
            "url": source.get('url', ''),
            "score": hit['_score']
        })

    # Step 2: Generate the answer using Gemini
    prompt = f"""
    You are a creative and helpful marketing consultant for Indonesian SMEs (UMKM). 
    Your task is to answer the user's question and provide actionable, creative marketing ideas. 
    Base your answer primarily on the provided context of marketing articles. 
    **Respond ONLY in English.** Use a friendly and encouraging tone.
    
    CONTEXT FROM MARKETING ARTICLES:
    {context_for_gemini}
    
    USER'S QUESTION:
    {query}
    
    MARKETING ADVICE:
    """
    
    generation_response = gemini_model.generate_content(prompt)
    final_answer = generation_response.text
        
    return {"answer": final_answer, "retrieved_articles": retrieved_articles}