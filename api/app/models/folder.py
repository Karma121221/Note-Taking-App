from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class FolderBase(BaseModel):
    name: str
    parent_folder_id: Optional[str] = None  # For nested folders

class FolderCreate(FolderBase):
    pass

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_folder_id: Optional[str] = None

class FolderInDB(FolderBase):
    id: str = Field(alias="_id")
    user_id: str  # Owner of the folder (child)
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class Folder(FolderBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class FolderPublic(BaseModel):
    id: str
    name: str
    parent_folder_id: Optional[str]
    user_id: str
    owner_name: Optional[str] = None  # For parent view
    created_at: datetime
    updated_at: datetime