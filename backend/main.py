# File: backend/main.py (v3 - Refactored with APIRouter)
# Description: Main entry point that assembles the application from different agent routers.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router modules
from app.api.v1 import agent_legal, agent_marketing, agent_operational, orchestrator, agent_proactive

# --- FastAPI App Initialization ---
app = FastAPI(
    title="UMKM-Go AI Backend",
    description="API for the UMKM-Go AI multi-agent system.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

app.include_router(
    agent_operational.router,
    prefix="/api/v1/agent/operational",
    tags=["Operational Agent"],
)

app.include_router(
    orchestrator.router,
    prefix="/api/v1/orchestrator",
    tags=["Orchestrator"],
)

app.include_router(
    agent_proactive.router,
    prefix="/api/v1/agent/proactive",
    tags=["Proactive Agent"],
)

print("[+] Application assembled with all agent routers.")