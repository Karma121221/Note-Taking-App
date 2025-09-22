from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables - try multiple paths for different deployment environments
env_paths = [
    os.path.join(os.path.dirname(__file__), "../../../.env"),  # Local development
    os.path.join(os.getcwd(), ".env"),  # Vercel environment
    ".env"  # Current directory
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

def get_allowed_origins() -> List[str]:
    """Get CORS allowed origins dynamically"""
    origins = [
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:5174",
    ]
    
    # Add Vercel URL if available
    vercel_url = os.getenv("VERCEL_URL")
    if vercel_url:
        origins.extend([
            f"https://{vercel_url}",
            vercel_url if vercel_url.startswith("https://") else f"https://{vercel_url}",
        ])
    
    # Add your known production domain
    origins.append("https://note-taking-app-mu-six.vercel.app")
    
    # For development/testing, allow all origins
    if os.getenv("NODE_ENV") != "production":
        origins.append("*")
    
    return list(set(origins))  # Remove duplicates

class Settings(BaseSettings):
    # Database settings
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = "note_taking_app"

    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # CORS settings
    ALLOWED_ORIGINS: List[str] = get_allowed_origins()

    # Security settings
    BCRYPT_ROUNDS: int = 12

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Debug logging for environment variables
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"DEBUG: Settings initialized - MONGO_URI: {self.MONGO_URI[:20]}...")
        logger.info(f"DEBUG: Settings initialized - SECRET_KEY: {self.SECRET_KEY[:10]}...")
        logger.info(f"DEBUG: Settings initialized - DATABASE_NAME: {self.DATABASE_NAME}")

    class Config:
        case_sensitive = True

settings = Settings()