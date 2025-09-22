from fastapi import FastAPI

app = FastAPI()

@app.get("/api/")
def read_root():
    return {"message": "Hello from Vercel!"}

@app.get("/api/test")
def test():
    return {"test": "working"}

# For Vercel deployment - this is the standard pattern
from mangum import Mangum
handler = Mangum(app)