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

class Settings(BaseSettings):
    # Database settings
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = "note_taking_app"
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    
    # CORS settings - Include both local development and production URLs
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:5174",
        "https://*.vercel.app",  # Vercel preview deployments
        os.getenv("VERCEL_URL", ""),  # Production Vercel URL
        f"https://{os.getenv('VERCEL_URL', '')}" if os.getenv('VERCEL_URL') else "",
    ]
    
    # Security settings
    BCRYPT_ROUNDS: int = 12

    class Config:
        case_sensitive = True

settings = Settings()