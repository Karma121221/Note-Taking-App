#!/usr/bin/env python3
"""
Test script to validate API endpoints locally before deployment
"""
import asyncio
import httpx
import sys
import os

# Add the api directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

async def test_api_endpoints():
    """Test basic API endpoints"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test root endpoint
            print("Testing root endpoint...")
            response = await client.get(f"{base_url}/")
            print(f"Root endpoint: {response.status_code} - {response.json()}")
            
            # Test health endpoint
            print("\nTesting health endpoint...")
            response = await client.get(f"{base_url}/health")
            print(f"Health endpoint: {response.status_code} - {response.json()}")
            
            # Test API test endpoint
            print("\nTesting API test endpoint...")
            response = await client.get(f"{base_url}/test")
            print(f"Test endpoint: {response.status_code} - {response.json()}")
            
        except Exception as e:
            print(f"Error testing endpoints: {e}")

def test_imports():
    """Test that all imports work correctly"""
    try:
        print("Testing imports...")
        
        from api.app.core.config import settings
        print("✓ Settings imported successfully")
        print(f"  Database: {settings.DATABASE_NAME}")
        print(f"  CORS Origins: {len(settings.ALLOWED_ORIGINS)} configured")
        
        from api.app.core.database import get_database
        print("✓ Database module imported successfully")
        
        from api.app.api.main import api_router
        print("✓ API router imported successfully")
        
        from api.index import app
        print("✓ FastAPI app imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("API Validation Test")
    print("=" * 50)
    
    # Test imports first
    if test_imports():
        print("\n" + "=" * 50)
        print("All imports successful! API should work on Vercel.")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("Import errors detected! Fix before deploying.")
        print("=" * 50)
        sys.exit(1)