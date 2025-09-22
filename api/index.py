from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Starting API import...")

try:
    from app.core.config import settings
    print("Settings imported successfully")
    print(f"MONGO_URI: {settings.MONGO_URI[:20]}...")
    print(f"DATABASE_NAME: {settings.DATABASE_NAME}")
except Exception as e:
    print(f"Failed to import settings: {e}")
    logger.error(f"Settings import error: {e}")
    # Re-raise the error to prevent the app from starting with broken config
    raise

try:
    from app.api.main import api_router
    print("API router imported successfully")
except Exception as e:
    print(f"Failed to import API router: {e}")
    logger.error(f"API router import error: {e}")
    raise

# Create FastAPI instance
app = FastAPI(
    title="Note Taking App API",
    description="A note-taking application for children and parents",
    version="1.0.0"
)

# Set up CORS middleware
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print(f"CORS configured with origins: {settings.ALLOWED_ORIGINS}")
except Exception as e:
    print(f"Failed to configure CORS: {e}")
    logger.error(f"CORS configuration error: {e}")
    raise

# Include API router
try:
    app.include_router(api_router, prefix="/api")
    print("API router included successfully")
except Exception as e:
    print(f"Failed to include API router: {e}")
    logger.error(f"Router inclusion error: {e}")
    raise

# Basic endpoints
@app.get("/")
async def root():
    return {"message": "Note Taking App API is running", "status": "success"}

@app.get("/health")
async def health():
    return {"status": "healthy", "api": "working"}

@app.get("/test")
async def test():
    return {"message": "API test endpoint", "working": True}

# For Vercel deployment
handler = app