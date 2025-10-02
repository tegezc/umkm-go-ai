# File: backend/app/application/services/legal_agent_service.py
# Description: Contains the core business logic for the Legal Agent.

from app.core.models import embedding_model, gemini_model
from app.infrastructure.database.elasticsearch_connector import es_client

LEGAL_INDEX_NAME = "umkm_legal_docs"

async def process_legal_query(query: str) -> dict:
    """
    Handles the entire RAG process for a legal query.
    This function can be called by any part of the application.
    """
    if not es_client:
        raise Exception("Elasticsearch client is not available.")

    # Step 1: Generate embedding and perform hybrid search
    query_embedding = embedding_model.encode(query).tolist()
    hybrid_query = { "query": { "match": { "text": { "query": query } } }, "knn": { "field": "embedding", "query_vector": query_embedding, "k": 5, "num_candidates": 50 } }
    
    response = es_client.search(index=LEGAL_INDEX_NAME, body=hybrid_query)
    
    retrieved_chunks = []; context_for_gemini = ""
    for hit in response['hits']['hits']:
        source = hit['_source']; chunk_text = source.get('text', '')
        context_for_gemini += f"--- Source: {source.get('chunk_id', '')} ---\n{chunk_text}\n\n"
        retrieved_chunks.append({
            "chunk_id": source.get('chunk_id', ''),
            "chapter_title": source.get('chapter_title', ''),
            "text": chunk_text,
            "score": hit['_score']
        })

    # Step 2: Generate the answer using Gemini
    prompt = f"""You are a helpful and professional legal assistant for Indonesian SMEs (UMKM). Your task is to answer the user's question based *only* on the provided context from Indonesian law documents. Do not use any external knowledge. If the answer is not available in the context, say so. Provide the answer in clear, easy-to-understand Indonesian.\n\nCONTEXT FROM LAW DOCUMENTS:\n{context_for_gemini}\n\nUSER'S QUESTION:\n{query}\n\nANSWER:"""
    
    generation_response = gemini_model.generate_content(prompt)
    final_answer = generation_response.text
        
    return {"answer": final_answer, "retrieved_chunks": retrieved_chunks}