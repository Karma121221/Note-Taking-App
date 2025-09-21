import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from backend.main import app

# This is the entry point for Vercel
def handler(request, response):
    return app(request, response)

# For Vercel, we need to export the app
if __name__ == "__main__":
    # This won't be called in Vercel, but useful for local testing
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)