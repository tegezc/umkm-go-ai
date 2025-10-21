# File: backend/app/__init__.py
# Description: Main application factory.

from fastapi import FastAPI
from .api.v1 import agent_legal, agent_marketing, agent_operational, agent_proactive, orchestrator, agent_brand
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    """Application factory function."""
    
    # Initialize the main FastAPI app instance
    app = FastAPI(
        title="UMKM-Go AI Backend",
        description="API for the UMKM-Go AI multi-agent system.",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health Check Endpoint
    @app.get("/", tags=["Health Check"])
    async def read_root():
        return {"message": "Welcome to the UMKM-Go AI Backend! The server is running."}

    # Include all agent routers
    app.include_router(agent_legal.router, prefix="/api/v1/agent/legal", tags=["Legal Agent"])
    app.include_router(agent_marketing.router, prefix="/api/v1/agent/marketing", tags=["Marketing Agent"])
    app.include_router(agent_operational.router, prefix="/api/v1/agent/operational", tags=["Operational Agent"])
    app.include_router(agent_proactive.router, prefix="/api/v1/agent/proactive", tags=["Proactive Agent"])
    app.include_router(orchestrator.router, prefix="/api/v1/orchestrator", tags=["Orchestrator"])
    app.include_router(agent_brand.router, prefix="/api/v1/agent/brand", tags=["Brand Agent"])
    
    print("[+] Application assembled with all agent routers.")
    
    return app