import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    print("Python version:", sys.version)
    print("Current working directory:", os.getcwd())
    print("Python path:", sys.path)
    
    from fastapi import FastAPI
    print("FastAPI imported successfully")
    
    # Create minimal FastAPI instance
    app = FastAPI(title="Debug API")
    
    @app.get("/")
    async def root():
        return {"message": "Debug API is working", "status": "success"}
    
    @app.get("/debug")
    async def debug():
        return {
            "working_directory": os.getcwd(),
            "python_version": sys.version,
            "environment": dict(os.environ)
        }
    
    print("FastAPI app created successfully")
    
    # For Vercel deployment
    handler = app
    
except Exception as e:
    print(f"Error during initialization: {e}")
    logger.error(f"Initialization error: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal error handler
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def error_root():
        return {"error": str(e), "message": "Initialization failed"}
    
    handler = app