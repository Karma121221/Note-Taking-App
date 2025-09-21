from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI instance
app = FastAPI(
    title="Note Taking App API",
    description="A note-taking application for children and parents",
    version="1.0.0"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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