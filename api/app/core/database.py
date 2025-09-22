from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global client variable
_client: Optional[AsyncIOMotorClient] = None

def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client"""
    global _client
    if _client is None:
        try:
            _client = AsyncIOMotorClient(settings.MONGO_URI)
            logger.info("Created new MongoDB client")
        except Exception as e:
            logger.error(f"Failed to create MongoDB client: {e}")
            raise
    return _client

async def get_database():
    """Get database instance for the current request"""
    try:
        client = get_mongo_client()
        db = client[settings.DATABASE_NAME]
        
        # Test connection with a simple ping
        await client.admin.command('ping')
        
        return db
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        # Reset client on connection failure
        global _client
        _client = None
        raise

# Legacy connection functions for compatibility (now no-ops in serverless)
async def connect_to_mongo():
    """Legacy function - connection is handled per-request in serverless"""
    logger.info("connect_to_mongo called - using per-request connections in serverless")
    pass

async def close_mongo_connection():
    """Legacy function - connections are managed automatically in serverless"""
    logger.info("close_mongo_connection called - connections managed automatically in serverless")
    pass