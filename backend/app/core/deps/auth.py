from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security.auth import verify_token
from app.core.database import get_database
from app.models.user import User, UserRole
from app.models.auth import TokenData
from bson import ObjectId

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_database)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
    if user is None:
        raise credentials_exception
    
    return User(**user, id=str(user["_id"]))

async def get_current_child_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user if they are a child"""
    if current_user.role != UserRole.CHILD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only children can perform this action"
        )
    return current_user

async def get_current_parent_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user if they are a parent"""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can perform this action"
        )
    return current_user

async def verify_note_access(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
) -> bool:
    """Verify user has access to a note (owner or parent of owner)"""
    note = await db.notes.find_one({"_id": ObjectId(note_id)})
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # If user is the owner
    if note["user_id"] == current_user.id:
        return True
    
    # If user is a parent and the note belongs to their child
    if current_user.role == UserRole.PARENT and note["user_id"] in current_user.children_ids:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this note"
    )

async def verify_folder_access(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
) -> bool:
    """Verify user has access to a folder (owner or parent of owner)"""
    folder = await db.folders.find_one({"_id": ObjectId(folder_id)})
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # If user is the owner
    if folder["user_id"] == current_user.id:
        return True
    
    # If user is a parent and the folder belongs to their child
    if current_user.role == UserRole.PARENT and folder["user_id"] in current_user.children_ids:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this folder"
    )