from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Vercel!", "status": "working"}

@app.get("/test")
def test():
    return {"test": "endpoint", "working": True}

# Export the app for Vercel
def handler(request, response):
    return app(request, response)

# Also export as app for compatibility
__all__ = ["app", "handler"]