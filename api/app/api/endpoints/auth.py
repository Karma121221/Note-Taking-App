from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.core.database import get_database
from app.core.security.auth import verify_password, get_password_hash, create_access_token
from app.core.deps.auth import get_current_user
from app.models.auth import Token, LoginRequest
from app.models.user import UserCreate, User, UserPublic, UserRole, generate_family_code
from bson import ObjectId
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/signup", response_model=UserPublic)
async def signup(user_data: UserCreate, db = Depends(get_database)):
    """Register a new user"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Prepare user data
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "role": user_data.role,
        "hashed_password": hashed_password,
        "children_ids": [],
        "parent_id": None,
        "family_code": None,
        "family_code_expires": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Generate family code for parents
    if user_data.role == UserRole.PARENT:
        family_code = generate_family_code()
        # Ensure uniqueness
        while await db.users.find_one({"family_code": family_code}):
            family_code = generate_family_code()
        user_dict["family_code"] = family_code
    
    # Handle family code linking for children
    if user_data.family_code and user_data.role == UserRole.CHILD:
        parent = await db.users.find_one({
            "family_code": user_data.family_code, 
            "role": UserRole.PARENT
        })
        if parent:
            # Check if family code has expired
            if not parent.get("family_code_expires") or parent["family_code_expires"] > datetime.utcnow():
                user_dict["parent_id"] = str(parent["_id"])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid family code"
            )
    
    # Insert user
    result = await db.users.insert_one(user_dict)
    
    # If this is a child with a parent, update parent's children list
    if user_dict["parent_id"]:
        await db.users.update_one(
            {"_id": ObjectId(user_dict["parent_id"])},
            {"$push": {"children_ids": str(result.inserted_id)}}
        )
    
    # Return user data
    user_dict["id"] = str(result.inserted_id)
    return UserPublic(**user_dict)

@router.post("/signin", response_model=Token)
async def signin(login_data: LoginRequest, db = Depends(get_database)):
    """Authenticate user and return access token"""
    # Find user by email
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "role": user["role"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    access_token = create_access_token(
        data={"sub": current_user.id, "role": current_user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}