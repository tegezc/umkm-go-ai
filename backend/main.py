# File: backend/main.py (Final Refactored)
# Description: Main entry point for the Uvicorn server.

from app import create_app

# This is the main application instance that Uvicorn will run.
app = create_app()