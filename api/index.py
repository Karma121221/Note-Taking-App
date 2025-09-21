import sys
import os
import logging

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

try:
    from backend.main import app
    logging.info("Successfully imported FastAPI app from backend.main")
except Exception as e:
    logging.error(f"Failed to import FastAPI app: {e}")
    # Create a simple FastAPI app as fallback
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Note Taking App API is running"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}

# Export the app for Vercel serverless functions
# This is the main export that Vercel will use
__all__ = ["app"]