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

# Log basic startup information
logger.info(f"Starting Note Taking App API in {os.getenv('VERCEL_ENV', 'development')} environment")

# Settings
class Settings(BaseSettings):
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = "note_taking_app"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Debug logging for environment variables
        logger.info(f"DEBUG: Settings initialized - MONGO_URI available: {bool(self.MONGO_URI)}")
        logger.info(f"DEBUG: Settings initialized - SECRET_KEY available: {bool(self.SECRET_KEY)}")
        logger.info(f"DEBUG: Settings initialized - DATABASE_NAME: {self.DATABASE_NAME}")
    
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

# Database connection optimized for Vercel serverless
async def get_mongo_client():
    """Create MongoDB client optimized for Vercel serverless environment"""
    try:
        # Use direct connection string instead of relying on environment variables
        # This bypasses potential serverless environment variable issues
        mongo_uri = "mongodb+srv://namit_thing:heyyup@cluster0.xgtzgla.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

        logger.info(f"Creating MongoDB client with direct URI: {mongo_uri[:30]}...")

        # Simplified connection parameters specifically for Vercel serverless
        client = AsyncIOMotorClient(
            mongo_uri,
            serverSelectionTimeoutMS=15000,  # 15 seconds for server selection
            connectTimeoutMS=30000,  # 30 seconds connection timeout
            socketTimeoutMS=30000,  # 30 seconds socket timeout
            maxPoolSize=1,  # Single connection only
            minPoolSize=0,  # No idle connections
            maxIdleTimeMS=10000,  # Close idle connections quickly
            waitQueueTimeoutMS=5000,  # 5 second wait timeout
            retryWrites=True,
            retryReads=True,
        )

        logger.info("MongoDB client created for Vercel serverless")
        return client
    except Exception as e:
        logger.error(f"Failed to create MongoDB client for Vercel: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )

async def get_database():
    """Get database instance specifically optimized for Vercel serverless"""
    client = None
    max_retries = 3  # Increased retries
    retry_count = 0

    while retry_count <= max_retries:
        try:
            client = await get_mongo_client()
            db_name = "note_taking_app"  # Direct database name
            logger.info(f"Getting database: {db_name} (attempt {retry_count + 1})")
            db = client[db_name]

            # Test connection with ping - simplified for serverless
            logger.info("Testing database connection with ping...")
            try:
                ping_result = await client.admin.command('ping')
                logger.info(f"Database ping successful: {ping_result}")
            except Exception as ping_error:
                logger.error(f"Database ping failed: {ping_error}")
                if retry_count < max_retries:
                    logger.info(f"Retrying database connection...")
                    retry_count += 1
                    if client:
                        client.close()
                    # Add a small delay before retry
                    import asyncio
                    await asyncio.sleep(0.5)
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
                logger.info(f"Retrying database connection...")
                retry_count += 1
                if client:
                    client.close()
                # Add delay before retry
                import asyncio
                await asyncio.sleep(0.5)
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

class NoteBase(BaseModel):
    title: str
    content: str
    folder_id: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    folder_id: Optional[str] = None

class NotePublic(NoteBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

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
    """Safe database getter optimized for Vercel serverless"""
    client = None
    try:
        client = await get_mongo_client()
        db = client["note_taking_app"]  # Direct database name

        # Test connection with ping
        logger.info("Testing database connection with ping (safe mode)...")
        await client.admin.command('ping')
        logger.info("Database connection successful (safe mode)")
        return db
    except Exception as e:
        logger.error(f"Failed to get database (safe mode): {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
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

async def get_current_parent_user(current_user = Depends(get_current_user)):
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can perform this action"
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

        # Convert the user object to dict and include family data for parents
        user_dict = current_user.dict()
        if current_user.role == UserRole.PARENT:
            # Ensure family_code is included in response
            user_dict["family_code"] = getattr(current_user, 'family_code', None)
            user_dict["family_code_expires"] = getattr(current_user, 'family_code_expires', None)
            user_dict["children_ids"] = getattr(current_user, 'children_ids', [])

        return UserPublic(**user_dict)
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )

# Family endpoints
@app.post("/api/family/generate-code")
async def generate_family_code_endpoint(
    code_data: dict,
    current_user: User = Depends(get_current_parent_user),
    db = Depends(get_database_safe)
):
    """Generate a new family code for parents"""
    # Generate unique family code
    family_code = generate_family_code()

    # Ensure uniqueness by checking database
    while await db.users.find_one({"family_code": family_code}):
        family_code = generate_family_code()

    # Calculate expiration if specified
    expires_at = None
    if code_data.get("expires_in_days"):
        expires_at = datetime.utcnow() + timedelta(days=code_data["expires_in_days"])

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

    return {"family_code": family_code, "expires_at": expires_at}

@app.post("/api/family/join-family")
async def join_family(
    join_data: dict,
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database_safe)
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
        "family_code": join_data["family_code"],
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

@app.get("/api/family/dashboard")
async def get_parent_dashboard(
    current_user: User = Depends(get_current_parent_user),
    db = Depends(get_database_safe)
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
            {
                "id": str(child["_id"]),
                "name": child["name"],
                "email": child["email"],
                "created_at": child["created_at"]
            }
            for child in children_docs
        ]

    return {
        "family_code": current_user.family_code or "No code generated",
        "family_code_expires": current_user.family_code_expires,
        "children": children
    }

@app.get("/api/family/my-parent")
async def get_my_parent(
    current_user: User = Depends(get_current_child_user),
    db = Depends(get_database_safe)
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

# Notes endpoints
@app.get("/api/notes/", response_model=List[NotePublic])
async def get_notes(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database_safe)
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

    notes = await db.notes.find(query).sort("created_at", -1).to_list(length=100)
    result = []
    for note in notes:
        note["id"] = str(note["_id"])
        result.append(NotePublic(**note))

    return result

@app.post("/api/notes/", response_model=NotePublic)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database_safe)
):
    """Create a new note"""
    # Check if folder exists and belongs to user (if specified)
    if note_data.folder_id:
        folder = await db.folders.find_one({
            "_id": ObjectId(note_data.folder_id),
            "user_id": current_user.id
        })
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )

    note_dict = note_data.dict()
    note_dict.update({
        "user_id": current_user.id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    result = await db.notes.insert_one(note_dict)
    note_dict["id"] = str(result.inserted_id)

    return NotePublic(**note_dict)

@app.get("/api/notes/{note_id}", response_model=NotePublic)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database_safe)
):
    """Get a specific note"""
    try:
        note = await db.notes.find_one({
            "_id": ObjectId(note_id),
            "user_id": current_user.id
        })
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )

        note["id"] = str(note["_id"])
        return NotePublic(**note)
    except Exception as e:
        logger.error(f"Error getting note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get note"
        )

@app.put("/api/notes/{note_id}", response_model=NotePublic)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database_safe)
):
    """Update a note"""
    try:
        # Check if note exists and belongs to user
        note = await db.notes.find_one({
            "_id": ObjectId(note_id),
            "user_id": current_user.id
        })
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )

        # Update only provided fields
        update_dict = {"updated_at": datetime.utcnow()}
        if note_data.title is not None:
            update_dict["title"] = note_data.title
        if note_data.content is not None:
            update_dict["content"] = note_data.content
        if note_data.folder_id is not None:
            # Check if folder exists and belongs to user
            if note_data.folder_id:
                folder = await db.folders.find_one({
                    "_id": ObjectId(note_data.folder_id),
                    "user_id": current_user.id
                })
                if not folder:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Folder not found"
                    )
            update_dict["folder_id"] = note_data.folder_id

        result = await db.notes.update_one(
            {"_id": ObjectId(note_id)},
            {"$set": update_dict}
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update note"
            )

        # Get updated note
        updated_note = await db.notes.find_one({"_id": ObjectId(note_id)})
        updated_note["id"] = str(updated_note["_id"])
        return NotePublic(**updated_note)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update note"
        )

@app.delete("/api/notes/{note_id}")
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database_safe)
):
    """Delete a note"""
    try:
        # Check if note exists and belongs to user
        note = await db.notes.find_one({
            "_id": ObjectId(note_id),
            "user_id": current_user.id
        })
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )

        result = await db.notes.delete_one({"_id": ObjectId(note_id)})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete note"
            )

        return {"message": "Note deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete note"
        )