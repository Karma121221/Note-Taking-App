from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, ValidationError
from pydantic_settings import BaseSettings
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List, Optional, Union
from bson import ObjectId
from enum import Enum
import os
import logging
import string
import random
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Settings
class Settings(BaseSettings):
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = "note_taking_app"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        origins = [
            "http://localhost:3000", 
            "http://localhost:5173", 
            "http://localhost:5174",
            "https://note-taking-app-mu-six.vercel.app"
        ]
        
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            origins.append(f"https://{vercel_url}")
        
        if os.getenv("NODE_ENV") != "production":
            origins.append("*")
        
        return list(set(origins))

settings = Settings()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database
_client = None

def get_mongo_client():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client

async def get_database():
    try:
        client = get_mongo_client()
        db = client[settings.DATABASE_NAME]
        await client.admin.command('ping')
        return db
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        global _client
        _client = None
        raise

# Models
class UserRole(str, Enum):
    PARENT = "parent"
    CHILD = "child"

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole

class UserCreate(UserBase):
    password: str
    family_code: Optional[str] = None

class UserPublic(UserBase):
    id: str
    children_ids: List[str] = []
    parent_id: Optional[str] = None
    family_code: Optional[str] = None
    created_at: datetime

class User(UserPublic):
    hashed_password: str
    updated_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class FolderBase(BaseModel):
    name: str
    parent_folder_id: Optional[str] = None

class FolderCreate(FolderBase):
    pass

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_folder_id: Optional[str] = None

class FolderPublic(FolderBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    owner_name: Optional[str] = None

# Utility functions
def generate_family_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return TokenData(user_id=user_id)
    except JWTError as e:
        logger.error(f"JWT verification error: {e}")
        return None

# Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_database)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
        
        user = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
        if user is None:
            raise credentials_exception
        
        return User(**user, id=str(user["_id"]))
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise credentials_exception

async def get_current_child_user(current_user = Depends(get_current_user)):
    if current_user.role != UserRole.CHILD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only children can perform this action"
        )
    return current_user

# FastAPI app
app = FastAPI(title="Note Taking App API")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.method} {request.url}: {exc}")
    logger.error(f"Exception traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Validation exception handler
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/api/")
async def root():
    return {"message": "Note Taking App API is running", "status": "success"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "api": "working"}

@app.post("/api/test-post")
async def test_post(data: dict):
    """Test POST endpoint to verify request handling"""
    logger.info(f"Test POST received: {data}")
    return {"received": data, "status": "success"}

# Auth endpoints
@app.post("/api/auth/signup", response_model=UserPublic)
async def signup(user_data: UserCreate, db = Depends(get_database)):
    """Register a new user"""
    try:
        logger.info(f"Signup attempt for email: {user_data.email}")
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            logger.warning(f"Email already registered: {user_data.email}")
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
            logger.info(f"Generated family code for parent: {family_code}")
        
        # Handle family code linking for children
        if user_data.family_code and user_data.role == UserRole.CHILD:
            parent = await db.users.find_one({
                "family_code": user_data.family_code, 
                "role": UserRole.PARENT
            })
            if parent:
                user_dict["parent_id"] = str(parent["_id"])
                logger.info(f"Linked child to parent with family code: {user_data.family_code}")
            else:
                logger.warning(f"Invalid family code: {user_data.family_code}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid family code"
                )
        
        # Insert user
        result = await db.users.insert_one(user_dict)
        logger.info(f"User created successfully with ID: {result.inserted_id}")
        
        # If this is a child with a parent, update parent's children list
        if user_dict["parent_id"]:
            await db.users.update_one(
                {"_id": ObjectId(user_dict["parent_id"])},
                {"$push": {"children_ids": str(result.inserted_id)}}
            )
            logger.info(f"Updated parent's children list")
        
        # Return user data
        user_dict["id"] = str(result.inserted_id)
        return UserPublic(**user_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        logger.error(f"Signup traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/api/auth/signin", response_model=Token)
async def signin(login_data: LoginRequest, db = Depends(get_database)):
    """Authenticate user and return access token"""
    try:
        logger.info(f"Signin attempt for email: {login_data.email}")
        
        # Find user by email
        user = await db.users.find_one({"email": login_data.email})
        if not user:
            logger.warning(f"User not found: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user["hashed_password"]):
            logger.warning(f"Invalid password for user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "role": user["role"]}
        )
        
        logger.info(f"Signin successful for user: {login_data.email}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signin error: {e}")
        logger.error(f"Signin traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.get("/api/auth/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    try:
        logger.info(f"Getting user info for: {current_user.email}")
        return current_user
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )

# Folders endpoints
@app.get("/api/folders/", response_model=List[FolderPublic])
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

@app.post("/api/folders/", response_model=FolderPublic)
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