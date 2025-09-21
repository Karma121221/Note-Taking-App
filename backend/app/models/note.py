from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class NoteType(str, Enum):
    TEXT = "text"
    CHECKLIST = "checklist"

class ChecklistItem(BaseModel):
    text: str
    completed: bool = False

class NoteBase(BaseModel):
    title: str
    content: str = ""
    type: NoteType = NoteType.TEXT
    checklist_items: List[ChecklistItem] = []
    tags: List[str] = []
    folder_id: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[NoteType] = None
    checklist_items: Optional[List[ChecklistItem]] = None
    tags: Optional[List[str]] = None
    folder_id: Optional[str] = None

class NoteInDB(NoteBase):
    id: str = Field(alias="_id")
    user_id: str  # Owner of the note (child)
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class Note(NoteBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class NotePublic(BaseModel):
    id: str
    title: str
    content: str
    type: NoteType
    checklist_items: List[ChecklistItem]
    tags: List[str]
    folder_id: Optional[str]
    user_id: str
    owner_name: Optional[str] = None  # For parent view
    created_at: datetime
    updated_at: datetime