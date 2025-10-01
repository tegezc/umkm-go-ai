# File: backend/app/api/v1/agent_operational.py
# Description: Endpoint for the Operational Agent, handles CSV file uploads and analysis.

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import io
import json

# Import shared models
from app.core.models import gemini_model

# --- Pydantic Models ---
class OperationalAnalysisResponse(BaseModel):
    insights: str
    statistics: dict

# --- APIRouter Instance ---
router = APIRouter()

@router.post("/analyze", response_model=OperationalAnalysisResponse)
async def analyze_sales_data(file: UploadFile = File(...)):
    """
    Receives a CSV file of sales data, analyzes it with Pandas,
    and uses Gemini to generate business insights.
    """
    print(f"[*] OPERATIONAL AGENT: Received file '{file.filename}'")

    # Step 1: Validate file type
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    try:
        # Step 2: Read file content and process with Pandas
        contents = await file.read()
        # Use io.StringIO to treat the byte string as a file
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        # --- Perform Data Analysis ---
        # Ensure required columns exist
        required_columns = ['product_name', 'quantity', 'price']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")

        # Calculate total revenue for each product
        df['revenue'] = df['quantity'] * df['price']

        total_revenue = df['revenue'].sum()
        total_items_sold = df['quantity'].sum()
        best_selling_product_by_qty = df.loc[df['quantity'].idxmax()]
        highest_revenue_product = df.loc[df['revenue'].idxmax()]

        # Prepare a structured dictionary of the statistics
        statistics = {
            "total_revenue": float(total_revenue),
            "total_items_sold": int(total_items_sold),
            "best_selling_by_quantity": {
                "name": best_selling_product_by_qty['product_name'],
                "quantity": int(best_selling_product_by_qty['quantity'])
            },
            "highest_revenue_product": {
                "name": highest_revenue_product['product_name'],
                "revenue": float(highest_revenue_product['revenue'])
            }
        }
        print(f"[+] Pandas analysis complete: {statistics}")

    except Exception as e:
        print(f"[!] Error processing CSV with Pandas: {e}")
        raise HTTPException(status_code=400, detail=f"Could not process CSV file: {e}")

    # Step 3: Use Gemini to interpret the statistics
    print("[*] Generating insights with Gemini...")
    prompt = f"""
    You are a friendly and insightful business analyst for an Indonesian SME (UMKM).
    Based on the following summary of sales data, provide 2-3 key insights and one actionable recommendation.
    Use a simple, encouraging, and easy-to-understand Indonesian language.

    SALES DATA SUMMARY:
    {json.dumps(statistics, indent=2, ensure_ascii=False)}

    INSIGHTS AND RECOMMENDATION:
    """

    try:
        generation_response = gemini_model.generate_content(prompt)
        insights = generation_response.text
        print("[+] Gemini insights generated.")
    except Exception as e:
        print(f"[!] Error generating content with Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred with the generation model: {e}")

    return OperationalAnalysisResponse(
        insights=insights,
        statistics=statistics
    )