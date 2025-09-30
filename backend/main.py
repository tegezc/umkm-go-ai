# File: backend/main.py (v2 - Refactored with APIRouter)
# Description: Main entry point that assembles the application from different agent routers.

from fastapi import FastAPI

# Import the router modules
from app.api.v1 import agent_legal, agent_marketing

# --- FastAPI App Initialization ---
app = FastAPI(
    title="UMKM-Go AI Backend",
    description="API for the UMKM-Go AI multi-agent system.",
    version="1.0.0",
)

# --- Health Check Endpoint ---
@app.get("/", tags=["Health Check"])
async def read_root():
    return {"message": "Welcome to the UMKM-Go AI Backend! The server is running."}

app.include_router(
    agent_legal.router,
    prefix="/api/v1/agent/legal", # All routes in this module will start with this path
    tags=["Legal Agent"],
)

app.include_router(
    agent_marketing.router,
    prefix="/api/v1/agent/marketing",
    tags=["Marketing Agent"],
)

print("[+] Application assembled with all agent routers.")