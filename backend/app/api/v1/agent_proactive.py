# File: backend/app/api/v1/agent_proactive.py (v5 - Final RSS Feed)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import xml.etree.ElementTree as ET

import firebase_admin
from firebase_admin import credentials, messaging

try:
    # The SDK will automatically find the credentials via the GOOGLE_APPLICATION_CREDENTIALS env var.
    cred = credentials.ApplicationDefault() 
    firebase_admin.initialize_app(cred)
    print("[+] Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"[!] Failed to initialize Firebase Admin SDK: {e}")
    # In a real app, you might want to handle this more gracefully
    # For the hackathon, a print statement is fine.

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
    
     # Send FCM Notification if opportunities are found ---
    if found_opportunities:
        print("[*] Preparing to send FCM notification...")
        
        # In the next step, we will get this token from the Flutter app.
        # For now, we will find a test token.
        registration_token = "cvuewHfRQGmF9R7QcN1BKK:APA91bFmiE1xtSjwihS_TI4jsCwO1llq7LIzABc8MuSoMJf1Q8DFaVf55xCRrf37jKsEUMGQG1tExRHfqkBUeO2jb4ac1hcWgJY0CjQWaHFIsxugwiKEBqw"

        # Take the first opportunity as the notification content
        first_opportunity = found_opportunities[0]
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=f"💡 Peluang Baru untuk Bisnis Anda!",
                body=f"{first_opportunity.title[:100]}..." # Truncate for brevity
            ),
            # You can also send custom data to your app
            data={
                "link": first_opportunity.link,
                "source": first_opportunity.source
            },
            token=registration_token,
        )

        try:
            # Send the message
            response = messaging.send(message)
            print('[+] Successfully sent message:', response)
        except Exception as e:
            print(f"[!] Error sending FCM message: {e}")
            # We don't raise an HTTPException here because the core task (scraping) was successful.
            # We just log the notification failure.

    return OpportunityScanResponse(status="success", found_opportunities=found_opportunities)