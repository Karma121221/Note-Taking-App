from fastapi import APIRouter

api_router = APIRouter()

# Import and include routers
from app.api.endpoints import auth, notes, folders, users, tags, family

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(folders.router, prefix="/folders", tags=["folders"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(family.router, prefix="/family", tags=["family"])