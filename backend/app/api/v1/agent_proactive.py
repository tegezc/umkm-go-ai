# File: backend/app/api/v1/agent_proactive.py (v5 - Final RSS Feed)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import xml.etree.ElementTree as ET

class OpportunityInfo(BaseModel):
    source: str
    title: str
    link: str
    description: str

class OpportunityScanResponse(BaseModel):
    status: str
    found_opportunities: list[OpportunityInfo]

# --- APIRouter Instance ---
router = APIRouter()

@router.post("/scan_opportunities", response_model=OpportunityScanResponse)
async def scan_news_for_opportunities():
    """
    Scans a business news RSS feed for articles containing relevant keywords for SMEs.
    This endpoint is designed to be triggered by a scheduler.
    """
    print("[*] PROACTIVE AGENT: Starting opportunity scan from RSS feed...")
 
    target_rss_url = "https://www.antaranews.com/rss/ekonomi-bisnis.xml"
    
    # Keywords that signify an opportunity for an SME
    keywords = ["umkm", "peluang", "ekspor", "bantuan", "pameran", "bazar", "subsidi", "kredit usaha"]
    
    found_opportunities = []

    try:
        headers = {'User-Agent': 'UMKM-Go-AI-Bot/1.0'}
        response = requests.get(target_rss_url, headers=headers, timeout=15)
        response.raise_for_status()

        # Parse the XML content of the RSS feed
        root = ET.fromstring(response.content)
        
        print(f"[+] Successfully fetched and parsed RSS feed.")

        # RSS structure is typically <channel><item>...</item></channel>
        for item in root.findall('./channel/item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            description = item.find('description').text if item.find('description') is not None else ""
            
            # Check if any of our keywords are in the title or description (case-insensitive)
            full_text_to_search = f"{title.lower()} {description.lower()}"
            if any(keyword in full_text_to_search for keyword in keywords):
                opportunity = OpportunityInfo(
                    source="Antara News Bisnis",
                    title=title.strip(),
                    link=link.strip(),
                    description=description.strip()
                )
                found_opportunities.append(opportunity)

    except requests.exceptions.RequestException as e:
        print(f"[!] Error fetching RSS feed: {e}")
        raise HTTPException(status_code=500, detail=f"RSS fetch failed: {e}")
    except ET.ParseError as e:
        print(f"[!] Error parsing XML: {e}")
        raise HTTPException(status_code=500, detail=f"XML parse failed: {e}")
    except Exception as e:
        print(f"[!] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    print(f"[*] Scan finished. Found {len(found_opportunities)} relevant opportunities.")
    return OpportunityScanResponse(status="success", found_opportunities=found_opportunities)