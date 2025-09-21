from fastapi import APIRouter, Depends
from app.core.database import get_database
from app.core.deps.auth import get_current_user
from app.models.user import User, UserRole
from typing import List

router = APIRouter()

@router.get("/", response_model=List[str])
async def get_all_tags(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all unique tags used by the user (or their children if parent)"""
    match_stage = {}
    
    # Determine whose tags to fetch based on user role
    if current_user.role == UserRole.CHILD:
        match_stage["user_id"] = current_user.id
    elif current_user.role == UserRole.PARENT:
        if current_user.children_ids:
            match_stage["user_id"] = {"$in": current_user.children_ids}
        else:
            return []
    
    pipeline = [
        {"$match": match_stage},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags"}},
        {"$sort": {"_id": 1}}
    ]
    
    tags = await db.notes.aggregate(pipeline).to_list(length=None)
    return [tag["_id"] for tag in tags]