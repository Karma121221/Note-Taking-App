from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app.core.config import settings
from backend.app.api.main import api_router
from backend.app.core.database import connect_to_mongo, close_mongo_connection

# Create FastAPI instance
app = FastAPI(
    title="Note Taking App API",
    description="A note-taking application for children and parents",
    version="1.0.0"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    print("Starting up API...")
    await connect_to_mongo()
    print("Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down API...")
    await close_mongo_connection()

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