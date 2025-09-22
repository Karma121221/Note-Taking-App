from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.deps.auth import get_current_user, get_current_parent_user, get_current_child_user
from app.models.user import (
    User, UserRole, FamilyCodeCreate, FamilyCodeResponse, 
    JoinFamilyRequest, ParentDashboard, ChildInfo, generate_family_code
)
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate-code", response_model=FamilyCodeResponse)
async def generate_family_code_endpoint(
    code_data: FamilyCodeCreate,
    current_user: User = Depends(get_current_parent_user),
    db = Depends(get_database)
):
    """Generate a new family code for parents"""
    # Generate unique family code
    family_code = generate_family_code()
    
    # Ensure uniqueness by checking database
    while await db.users.find_one({"family_code": family_code}):
        family_code = generate_family_code()
    
    # Calculate expiration if specified
    expires_at = None
    if code_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=code_data.expires_in_days)
    
    # Update user with new family code
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {
            "$set": {
                "family_code": family_code,
                "family_code_expires": expires_at,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return FamilyCodeResponse(
        family_code=family_code,
        expires_at=expires_at
    )

@router.post("/join-family")
async def join_family(
    join_data: JoinFamilyRequest,
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database)
):
    """Allow a child to join a family using a family code"""
    # Check if child is already linked to a parent
    if current_user.parent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already linked to a parent account"
        )
    
    # Find parent with this family code
    parent = await db.users.find_one({
        "family_code": join_data.family_code,
        "role": UserRole.PARENT
    })
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid family code"
        )
    
    # Check if family code has expired
    if parent.get("family_code_expires") and parent["family_code_expires"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family code has expired"
        )
    
    parent_id = str(parent["_id"])
    
    # Update child's parent_id
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {
            "$set": {
                "parent_id": parent_id,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Add child to parent's children_ids
    await db.users.update_one(
        {"_id": ObjectId(parent_id)},
        {
            "$push": {"children_ids": current_user.id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Successfully joined family", "parent_name": parent["name"]}

@router.post("/leave-family")
async def leave_family(
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database)
):
    """Allow a child to leave their current family"""
    if not current_user.parent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not linked to any parent account"
        )
    
    # Remove child from parent's children_ids
    await db.users.update_one(
        {"_id": ObjectId(current_user.parent_id)},
        {
            "$pull": {"children_ids": current_user.id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    # Remove parent_id from child
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {
            "$unset": {"parent_id": ""},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Successfully left family"}

@router.delete("/remove-child/{child_id}")
async def remove_child(
    child_id: str,
    current_user: User = Depends(get_current_parent_user),
    db = Depends(get_database)
):
    """Allow a parent to remove a child from their family"""
    # Check if child belongs to this parent
    if child_id not in current_user.children_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found in your family"
        )
    
    # Remove child from parent's children_ids
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {
            "$pull": {"children_ids": child_id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    # Remove parent_id from child
    await db.users.update_one(
        {"_id": ObjectId(child_id)},
        {
            "$unset": {"parent_id": ""},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Child removed from family"}

@router.get("/dashboard", response_model=ParentDashboard)
async def get_parent_dashboard(
    current_user: User = Depends(get_current_parent_user),
    db = Depends(get_database)
):
    """Get parent dashboard with family code and children info"""
    # Get children information
    children = []
    if current_user.children_ids:
        children_docs = await db.users.find({
            "_id": {"$in": [ObjectId(child_id) for child_id in current_user.children_ids]},
            "role": UserRole.CHILD
        }).to_list(length=100)
        
        children = [
            ChildInfo(
                id=str(child["_id"]),
                name=child["name"],
                email=child["email"],
                created_at=child["created_at"]
            )
            for child in children_docs
        ]
    
    return ParentDashboard(
        family_code=current_user.family_code or "No code generated",
        family_code_expires=current_user.family_code_expires,
        children=children
    )

@router.get("/my-parent")
async def get_my_parent(
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database)
):
    """Get information about the child's parent"""
    if not current_user.parent_id:
        return {"parent": None, "message": "Not linked to any parent account"}
    
    parent = await db.users.find_one({
        "_id": ObjectId(current_user.parent_id),
        "role": UserRole.PARENT
    })
    
    if not parent:
        # Parent was deleted, cleanup child's parent_id
        await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {
                "$unset": {"parent_id": ""},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return {"parent": None, "message": "Parent account no longer exists"}
    
    return {
        "parent": {
            "id": str(parent["_id"]),
            "name": parent["name"],
            "email": parent["email"]
        }
    }