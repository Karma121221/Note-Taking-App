from fastapi import FastAPI

app = FastAPI()

@app.get("/api/")
def read_root():
    return {"message": "Hello from Vercel FastAPI!", "status": "working"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.get("/api/test")
def test():
    return {"test": "endpoint working", "success": True}