from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.deps.auth import get_current_user, get_current_child_user, verify_folder_access
from app.models.folder import FolderCreate, FolderUpdate, Folder, FolderPublic
from app.models.user import User, UserRole
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

router = APIRouter()

@router.get("/", response_model=List[FolderPublic])
async def get_folders(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all folders for current user (or their children if parent)"""
    query = {}
    
    # Determine whose folders to fetch based on user role
    if current_user.role == UserRole.CHILD:
        query["user_id"] = current_user.id
    elif current_user.role == UserRole.PARENT:
        # Get folders from all children
        if current_user.children_ids:
            query["user_id"] = {"$in": current_user.children_ids}
        else:
            return []  # No children linked
    
    folders = await db.folders.find(query).sort("name", 1).to_list(length=100)
    
    # Get user information for owner names (for parent view)
    user_map = {}
    if current_user.role == UserRole.PARENT and folders:
        user_ids = list(set(folder["user_id"] for folder in folders))
        users = await db.users.find({
            "_id": {"$in": [ObjectId(uid) for uid in user_ids]}
        }).to_list(length=100)
        user_map = {str(user["_id"]): user["name"] for user in users}
    
    result = []
    for folder in folders:
        folder["id"] = str(folder["_id"])
        folder_data = FolderPublic(**folder)
        
        # Add owner name for parent view
        if current_user.role == UserRole.PARENT:
            folder_data.owner_name = user_map.get(folder["user_id"])
        
        result.append(folder_data)
    
    return result

@router.post("/", response_model=FolderPublic)
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database)
):
    """Create a new folder (children only)"""
    # Check if parent folder exists and belongs to user (if specified)
    if folder_data.parent_folder_id:
        parent_folder = await db.folders.find_one({
            "_id": ObjectId(folder_data.parent_folder_id),
            "user_id": current_user.id
        })
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found"
            )
    
    folder_dict = folder_data.dict()
    folder_dict.update({
        "user_id": current_user.id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    result = await db.folders.insert_one(folder_dict)
    folder_dict["id"] = str(result.inserted_id)
    
    return FolderPublic(**folder_dict)

@router.get("/{folder_id}", response_model=FolderPublic)
async def get_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get a specific folder"""
    # Verify access
    await verify_folder_access(folder_id, current_user, db)
    
    folder = await db.folders.find_one({"_id": ObjectId(folder_id)})
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    folder["id"] = str(folder["_id"])
    folder_data = FolderPublic(**folder)
    
    # Add owner name for parent view
    if current_user.role == UserRole.PARENT:
        owner = await db.users.find_one({"_id": ObjectId(folder["user_id"])})
        if owner:
            folder_data.owner_name = owner["name"]
    
    return folder_data

@router.put("/{folder_id}", response_model=FolderPublic)
async def update_folder(
    folder_id: str,
    folder_data: FolderUpdate,
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database)
):
    """Update a folder (children only, own folders only)"""
    # Check if folder exists and belongs to current user
    folder = await db.folders.find_one({"_id": ObjectId(folder_id), "user_id": current_user.id})
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Check if parent folder exists and belongs to user (if specified)
    if folder_data.parent_folder_id:
        parent_folder = await db.folders.find_one({
            "_id": ObjectId(folder_data.parent_folder_id),
            "user_id": current_user.id
        })
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found"
            )
        
        # Check for circular reference
        if folder_data.parent_folder_id == folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder cannot be its own parent"
            )
    
    # Prepare update data
    update_data = {k: v for k, v in folder_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Update folder
    await db.folders.update_one(
        {"_id": ObjectId(folder_id)},
        {"$set": update_data}
    )
    
    # Get updated folder
    updated_folder = await db.folders.find_one({"_id": ObjectId(folder_id)})
    updated_folder["id"] = str(updated_folder["_id"])
    
    return FolderPublic(**updated_folder)

@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: str,
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database)
):
    """Delete a folder (children only, own folders only)"""
    # Check if folder exists and belongs to current user
    folder = await db.folders.find_one({"_id": ObjectId(folder_id), "user_id": current_user.id})
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Check if folder has child folders
    child_folders = await db.folders.find_one({"parent_folder_id": folder_id})
    if child_folders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete folder that contains subfolders"
        )
    
    # Check if folder has notes
    notes_in_folder = await db.notes.find_one({"folder_id": folder_id})
    if notes_in_folder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete folder that contains notes"
        )
    
    # Delete folder
    await db.folders.delete_one({"_id": ObjectId(folder_id)})
    
    return {"message": "Folder deleted successfully"}

@router.get("/tree/hierarchy", response_model=List[dict])
async def get_folder_hierarchy(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get folder hierarchy as a tree structure"""
    query = {}
    
    # Determine whose folders to fetch based on user role
    if current_user.role == UserRole.CHILD:
        query["user_id"] = current_user.id
    elif current_user.role == UserRole.PARENT:
        if current_user.children_ids:
            query["user_id"] = {"$in": current_user.children_ids}
        else:
            return []
    
    folders = await db.folders.find(query).sort("name", 1).to_list(length=100)
    
    # Get user information for owner names (for parent view)
    user_map = {}
    if current_user.role == UserRole.PARENT and folders:
        user_ids = list(set(folder["user_id"] for folder in folders))
        users = await db.users.find({
            "_id": {"$in": [ObjectId(uid) for uid in user_ids]}
        }).to_list(length=100)
        user_map = {str(user["_id"]): user["name"] for user in users}
    
    # Convert to dict with string IDs
    folder_dict = {}
    for folder in folders:
        folder["id"] = str(folder["_id"])
        folder_dict[folder["id"]] = folder
    
    # Build hierarchy
    def build_tree(parent_id=None):
        children = []
        for folder in folder_dict.values():
            if folder.get("parent_folder_id") == parent_id:
                folder_node = {
                    "id": folder["id"],
                    "name": folder["name"],
                    "user_id": folder["user_id"],
                    "owner_name": user_map.get(folder["user_id"]) if current_user.role == UserRole.PARENT else None,
                    "created_at": folder["created_at"],
                    "children": build_tree(folder["id"])
                }
                children.append(folder_node)
        return children
    
    return build_tree()