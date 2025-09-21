from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.database import get_database
from app.core.deps.auth import get_current_user, get_current_child_user, verify_note_access
from app.models.note import NoteCreate, NoteUpdate, Note, NotePublic
from app.models.user import User, UserRole
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

router = APIRouter()

@router.get("/", response_model=List[NotePublic])
async def get_notes(
    folder_id: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all notes for current user (or their children if parent)"""
    query = {}
    
    # Determine whose notes to fetch based on user role
    if current_user.role == UserRole.CHILD:
        query["user_id"] = current_user.id
    elif current_user.role == UserRole.PARENT:
        # Get notes from all children
        if current_user.children_ids:
            query["user_id"] = {"$in": current_user.children_ids}
        else:
            return []  # No children linked
    
    # Add folder filter if specified
    if folder_id:
        query["folder_id"] = folder_id
    
    # Add tag filter if specified
    if tag:
        query["tags"] = {"$in": [tag]}
    
    notes = await db.notes.find(query).sort("updated_at", -1).to_list(length=100)
    
    # Get user information for owner names (for parent view)
    user_map = {}
    if current_user.role == UserRole.PARENT and notes:
        user_ids = list(set(note["user_id"] for note in notes))
        users = await db.users.find({
            "_id": {"$in": [ObjectId(uid) for uid in user_ids]}
        }).to_list(length=100)
        user_map = {str(user["_id"]): user["name"] for user in users}
    
    result = []
    for note in notes:
        note["id"] = str(note["_id"])
        note_data = NotePublic(**note)
        
        # Add owner name for parent view
        if current_user.role == UserRole.PARENT:
            note_data.owner_name = user_map.get(note["user_id"])
        
        result.append(note_data)
    
    return result

@router.post("/", response_model=NotePublic)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database)
):
    """Create a new note (children only)"""
    note_dict = note_data.dict()
    note_dict.update({
        "user_id": current_user.id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    result = await db.notes.insert_one(note_dict)
    note_dict["id"] = str(result.inserted_id)
    
    return NotePublic(**note_dict)

@router.get("/{note_id}", response_model=NotePublic)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get a specific note"""
    # Verify access
    await verify_note_access(note_id, current_user, db)
    
    note = await db.notes.find_one({"_id": ObjectId(note_id)})
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    note["id"] = str(note["_id"])
    note_data = NotePublic(**note)
    
    # Add owner name for parent view
    if current_user.role == UserRole.PARENT:
        owner = await db.users.find_one({"_id": ObjectId(note["user_id"])})
        if owner:
            note_data.owner_name = owner["name"]
    
    return note_data

@router.put("/{note_id}", response_model=NotePublic)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database)
):
    """Update a note (children only, own notes only)"""
    # Check if note exists and belongs to current user
    note = await db.notes.find_one({"_id": ObjectId(note_id), "user_id": current_user.id})
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Prepare update data
    update_data = {k: v for k, v in note_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Update note
    await db.notes.update_one(
        {"_id": ObjectId(note_id)},
        {"$set": update_data}
    )
    
    # Get updated note
    updated_note = await db.notes.find_one({"_id": ObjectId(note_id)})
    updated_note["id"] = str(updated_note["_id"])
    
    return NotePublic(**updated_note)

@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database)
):
    """Delete a note (children only, own notes only)"""
    # Check if note exists and belongs to current user
    note = await db.notes.find_one({"_id": ObjectId(note_id), "user_id": current_user.id})
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Delete note
    await db.notes.delete_one({"_id": ObjectId(note_id)})
    
    return {"message": "Note deleted successfully"}

@router.get("/by-folder/{folder_id}", response_model=List[NotePublic])
async def get_notes_by_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all notes in a specific folder"""
    query = {"folder_id": folder_id}
    
    # Determine whose notes to fetch based on user role
    if current_user.role == UserRole.CHILD:
        query["user_id"] = current_user.id
    elif current_user.role == UserRole.PARENT:
        # Get notes from all children
        if current_user.children_ids:
            query["user_id"] = {"$in": current_user.children_ids}
        else:
            return []
    
    notes = await db.notes.find(query).sort("updated_at", -1).to_list(length=100)
    
    # Get user information for owner names (for parent view)
    user_map = {}
    if current_user.role == UserRole.PARENT and notes:
        user_ids = list(set(note["user_id"] for note in notes))
        users = await db.users.find({
            "_id": {"$in": [ObjectId(uid) for uid in user_ids]}
        }).to_list(length=100)
        user_map = {str(user["_id"]): user["name"] for user in users}
    
    result = []
    for note in notes:
        note["id"] = str(note["_id"])
        note_data = NotePublic(**note)
        
        # Add owner name for parent view
        if current_user.role == UserRole.PARENT:
            note_data.owner_name = user_map.get(note["user_id"])
        
        result.append(note_data)
    
    return result

@router.get("/by-tag/{tag}", response_model=List[NotePublic])
async def get_notes_by_tag(
    tag: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all notes with a specific tag"""
    query = {"tags": {"$in": [tag]}}
    
    # Determine whose notes to fetch based on user role
    if current_user.role == UserRole.CHILD:
        query["user_id"] = current_user.id
    elif current_user.role == UserRole.PARENT:
        # Get notes from all children
        if current_user.children_ids:
            query["user_id"] = {"$in": current_user.children_ids}
        else:
            return []
    
    notes = await db.notes.find(query).sort("updated_at", -1).to_list(length=100)
    
    # Get user information for owner names (for parent view)
    user_map = {}
    if current_user.role == UserRole.PARENT and notes:
        user_ids = list(set(note["user_id"] for note in notes))
        users = await db.users.find({
            "_id": {"$in": [ObjectId(uid) for uid in user_ids]}
        }).to_list(length=100)
        user_map = {str(user["_id"]): user["name"] for user in users}
    
    result = []
    for note in notes:
        note["id"] = str(note["_id"])
        note_data = NotePublic(**note)
        
        # Add owner name for parent view
        if current_user.role == UserRole.PARENT:
            note_data.owner_name = user_map.get(note["user_id"])
        
        result.append(note_data)
    
    return result

@router.get("/tags/all", response_model=List[str])
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