from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
import secrets
import string

class UserRole(str, Enum):
    CHILD = "child"
    PARENT = "parent"

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole

class UserCreate(UserBase):
    password: str
    family_code: Optional[str] = None  # For children to join families

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str
    children_ids: List[str] = []  # For parents
    parent_id: Optional[str] = None  # For children
    family_code: Optional[str] = None  # Unique code for parents
    family_code_expires: Optional[datetime] = None  # Optional expiration
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class User(UserBase):
    id: str
    children_ids: List[str] = []
    parent_id: Optional[str] = None
    family_code: Optional[str] = None
    family_code_expires: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class UserPublic(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: UserRole
    family_code: Optional[str] = None
    family_code_expires: Optional[datetime] = None
    created_at: datetime

# Utility functions for family code management
def generate_family_code(length: int = 8) -> str:
    """Generate a unique family code"""
    characters = string.ascii_uppercase + string.digits
    # Exclude similar looking characters for clarity
    characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    return ''.join(secrets.choice(characters) for _ in range(length))

class FamilyCodeCreate(BaseModel):
    expires_in_days: Optional[int] = None  # Optional expiration

class FamilyCodeResponse(BaseModel):
    family_code: str
    expires_at: Optional[datetime] = None

class JoinFamilyRequest(BaseModel):
    family_code: str

class ChildInfo(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime

class ParentDashboard(BaseModel):
    family_code: str
    family_code_expires: Optional[datetime]
    children: List[ChildInfo]