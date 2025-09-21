from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.deps.auth import get_current_user, get_current_parent_user
from app.models.user import User, UserPublic, UserRole
from bson import ObjectId
from typing import List

router = APIRouter()

@router.get("/children", response_model=List[UserPublic])
async def get_children(
    current_user: User = Depends(get_current_parent_user),
    db = Depends(get_database)
):
    """Get list of children for parent user"""
    children = []
    for child_id in current_user.children_ids:
        child = await db.users.find_one({"_id": ObjectId(child_id)})
        if child:
            child["id"] = str(child["_id"])
            children.append(UserPublic(**child))
    
    return children

@router.post("/link-child/{child_email}")
async def link_child(
    child_email: str,
    current_user: User = Depends(get_current_parent_user),
    db = Depends(get_database)
):
    """Link a child to parent account"""
    # Find child by email
    child = await db.users.find_one({"email": child_email, "role": UserRole.CHILD})
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child user not found"
        )
    
    child_id = str(child["_id"])
    
    # Check if already linked
    if child_id in current_user.children_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Child is already linked to this parent"
        )
    
    # Update parent's children list
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$push": {"children_ids": child_id}}
    )
    
    # Update child's parent reference
    await db.users.update_one(
        {"_id": ObjectId(child_id)},
        {"$set": {"parent_id": current_user.id}}
    )
    
    return {"message": "Child linked successfully"}

@router.delete("/unlink-child/{child_id}")
async def unlink_child(
    child_id: str,
    current_user: User = Depends(get_current_parent_user),
    db = Depends(get_database)
):
    """Unlink a child from parent account"""
    if child_id not in current_user.children_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child is not linked to this parent"
        )
    
    # Update parent's children list
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$pull": {"children_ids": child_id}}
    )
    
    # Update child's parent reference
    await db.users.update_one(
        {"_id": ObjectId(child_id)},
        {"$unset": {"parent_id": ""}}
    )
    
    return {"message": "Child unlinked successfully"}