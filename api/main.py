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

# Database connection for serverless environments
async def get_mongo_client():
    """Create a new MongoDB client for each request in serverless"""
    try:
        logger.info(f"Creating new MongoDB client for serverless with URI: {settings.MONGO_URI[:50]}...")
        logger.info(f"MongoDB URI length: {len(settings.MONGO_URI)}")

        # Log connection parameters
        connection_params = {
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 20000,
            "socketTimeoutMS": 60000,
            "maxPoolSize": 1,
            "minPoolSize": 0,
            "maxIdleTimeMS": 30000,
            "waitQueueTimeoutMS": 10000,
            "heartbeatFrequencyMS": 10000,
            "maxStalenessSeconds": 30,
            "retryWrites": True,
            "retryReads": True,
        }
        logger.info(f"MongoDB connection parameters: {connection_params}")

        client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=10000,  # 10 second timeout for server selection
            connectTimeoutMS=20000,  # 20 second connection timeout
            socketTimeoutMS=60000,  # 60 second socket timeout (within Vercel limits)
            maxPoolSize=1,  # Single connection for serverless
            minPoolSize=0,  # Don't maintain idle connections
            maxIdleTimeMS=30000,  # Close connections after 30 seconds of inactivity
            waitQueueTimeoutMS=10000,  # 10 second wait queue timeout
            retryWrites=True,
            retryReads=True,
            # Add server monitoring for better connection health
            heartbeatFrequencyMS=10000,  # 10 second heartbeat
            maxStalenessSeconds=30,  # 30 second max staleness
        )

        logger.info("MongoDB client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create MongoDB client: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )

async def get_database():
    """Get database instance optimized for serverless with retry logic"""
    client = None
    max_retries = 2
    retry_count = 0

    while retry_count <= max_retries:
        try:
            client = await get_mongo_client()
            db_name = settings.DATABASE_NAME
            logger.info(f"Getting database: {db_name} (attempt {retry_count + 1}/{max_retries + 1})")
            db = client[db_name]

            # Test connection with ping - this is crucial for serverless
            logger.info("Testing database connection with ping...")
            try:
                ping_result = await client.admin.command('ping')
                logger.info(f"Database ping successful: {ping_result}")
            except Exception as ping_error:
                logger.error(f"Database ping failed: {ping_error}")
                if retry_count < max_retries:
                    logger.info(f"Retrying database connection (attempt {retry_count + 2})...")
                    retry_count += 1
                    if client:
                        client.close()
                    continue
                raise ping_error

            logger.info("Database connection successful")
            return db
        except Exception as e:
            logger.error(f"Database connection error (attempt {retry_count + 1}): {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

            if retry_count < max_retries:
                logger.info(f"Retrying database connection (attempt {retry_count + 2})...")
                retry_count += 1
                if client:
                    client.close()
                continue
            else:
                # Close client on final error
                if client:
                    client.close()
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database service temporarily unavailable"
                )

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

async def get_database_safe():
    """Safe database getter with proper error handling for serverless"""
    client = None
    try:
        client = await get_mongo_client()
        db = client[settings.DATABASE_NAME]

        # Test connection with ping
        logger.info("Testing database connection with ping (safe mode)...")
        await client.admin.command('ping')
        logger.info("Database connection successful (safe mode)")
        return db
    except Exception as e:
        logger.error(f"Failed to get database: {e}")
        # Close client on error
        if client:
            client.close()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service temporarily unavailable"
        )

# Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_database_safe)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    client = None
    try:
        token_data = verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception

        user = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
        if user is None:
            raise credentials_exception

        return User(**user, id=str(user["_id"]))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        # Close the client connection on error
        if client:
            client.close()
        raise credentials_exception

async def get_current_child_user(current_user = Depends(get_current_user)):
    if current_user.role != UserRole.CHILD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only children can perform this action"
        )
    return current_user

async def close_db_connection():
    """Close database connection (no-op in serverless - connections are per-request)"""
    # In serverless environments, connections are created per-request and closed automatically
    # No need for global connection management
    logger.info("close_db_connection called - connections managed per-request in serverless")
    pass

# FastAPI app
app = FastAPI(title="Note Taking App API")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.method} {request.url}: {exc}")
    logger.error(f"Exception traceback: {traceback.format_exc()}")
    
    # Close db connection on error to prevent "Event loop is closed" errors
    await close_db_connection()
    
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
async def signup(user_data: UserCreate, db = Depends(get_database_safe)):
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
        user_id = str(result.inserted_id)
        logger.info(f"User created successfully with ID: {user_id}")
        
        # If this is a child with a parent, update parent's children list
        if user_dict["parent_id"]:
            await db.users.update_one(
                {"_id": ObjectId(user_dict["parent_id"])},
                {"$push": {"children_ids": user_id}}
            )
            logger.info(f"Updated parent's children list")
        
        # Prepare response data
        user_dict["id"] = user_id
        response_data = UserPublic(**user_dict)
        
        logger.info(f"Signup successful for user: {user_data.email}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        logger.error(f"Signup traceback: {traceback.format_exc()}")
        await close_db_connection()  # Clean up connection on error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/api/auth/signin", response_model=Token)
async def signin(login_data: LoginRequest, db = Depends(get_database_safe)):
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
        
        response_data = {"access_token": access_token, "token_type": "bearer"}
        logger.info(f"Signin successful for user: {login_data.email}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signin error: {e}")
        logger.error(f"Signin traceback: {traceback.format_exc()}")
        await close_db_connection()  # Clean up connection on error
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
    db = Depends(get_database_safe)
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
    db = Depends(get_database_safe)
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