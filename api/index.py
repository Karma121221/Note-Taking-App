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
    raise

# For Vercel serverless functions, we need to export the FastAPI app directly
# Vercel's Python runtime will handle the ASGI interface automatically