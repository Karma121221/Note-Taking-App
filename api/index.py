import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from backend.main import app

# For Vercel serverless functions, we need to export the FastAPI app directly
# Vercel's Python runtime will handle the ASGI interface automatically