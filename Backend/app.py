from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
import os
import shutil
from typing import List, Optional, Dict, Any, Union
from bson import ObjectId
import json

# Import our modules
from models import *
from database import connect_to_mongo, close_mongo_connection, get_database
from auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from loader import DocumentLoader
from search import EnhancedSemanticSearcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles ObjectId and datetime objects"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Convert objects with __dict__ to dictionaries, but limit depth
            return str(obj)  # Simple string conversion to avoid recursion
        return super().default(obj)

def safe_serialize(obj, max_depth=3, current_depth=0):
    """Safely serialize objects to JSON-compatible format"""
    if current_depth > max_depth:
        return str(obj)
    
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            try:
                result[str(key)] = safe_serialize(value, max_depth, current_depth + 1)
            except Exception:
                result[str(key)] = str(value)
        return result
    elif isinstance(obj, (list, tuple)):
        result = []
        for item in obj:
            try:
                result.append(safe_serialize(item, max_depth, current_depth + 1))
            except Exception:
                result.append(str(item))
        return result
    else:
        # For any other object type, convert to string to avoid recursion
        return str(obj)

def create_json_response(data: Any, status_code: int = 200) -> JSONResponse:
    """Create a JSON response with safe serialization"""
    try:
        safe_data = safe_serialize(data)
        return JSONResponse(
            content=safe_data,
            status_code=status_code,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        print(f"Serialization error: {e}")
        error_response = {
            "error": "Serialization error",
            "message": str(e),
            "status": "error"
        }
        return JSONResponse(
            content=error_response,
            status_code=500,
            headers={"Content-Type": "application/json"}
        )

# Initialize FastAPI app
app = FastAPI(
    title="Beecok - AI-Powered Semantic Search System",
    description="A semantic search system with user authentication and spaces organization using MongoDB, Pinecone vector database and Google Gemini",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
document_loader = DocumentLoader()
semantic_searcher = EnhancedSemanticSearcher()

# Create necessary directories
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.txt']

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    data = {
        "message": "Beecok - AI-Powered Semantic Search API",
        "version": "2.0.0",
        "description": "Upload documents to spaces and perform semantic search using MongoDB, Pinecone and Google Gemini",
        "features": ["User Authentication", "Document Spaces", "AI Chat", "Semantic Search"],
        "supported_formats": SUPPORTED_EXTENSIONS
    }
    return create_json_response(data)

# Authentication endpoints
@app.post("/auth/register")
async def register_user(user: UserCreate):
    """Register a new user with enhanced error handling"""
    
    # Get database with fallback
    db = get_database()
    if db is None:
        print("Database connection failed, attempting to reconnect...")
        success = await connect_to_mongo()
        if not success:
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable. Please try again later."
            )
        db = get_database()
        if db is None:
            raise HTTPException(
                status_code=503,
                detail="Unable to establish database connection"
            )
    
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        existing_username = await db.users.find_one({"username": user.username})
        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        
        # Hash password and create user
        hashed_password = get_password_hash(user.password)
        user_doc = {
            "username": user.username,
            "email": user.email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.users.insert_one(user_doc)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        response_data = {
            "message": "User registered successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(result.inserted_id),
                "username": user.username,
                "email": user.email
            }
        }
        
        return create_json_response(response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Registration failed due to server error"
        )

@app.post("/auth/login")
async def login_user(user_credentials: UserLogin):
    """Login user"""
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }
    }
    
    return create_json_response(response_data)

@app.get("/auth/me")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    """Get current user information"""
    response_data = {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "email": current_user["email"],
        "created_at": current_user["created_at"].isoformat() if current_user.get("created_at") else None
    }
    return create_json_response(response_data)

# Chat endpoints
@app.get("/chats")
async def get_user_chats(current_user: dict = Depends(get_current_active_user)):
    """Get user's chats"""
    db = get_database()
    chats = await db.chats.find(
        {"user_id": ObjectId(current_user["_id"])}
    ).sort("updated_at", -1).to_list(100)
    
    # Convert ObjectIds to strings and dates to ISO format
    chat_list = []
    for chat in chats:
        chat_data = {
            "id": str(chat["_id"]),
            "user_id": str(chat["user_id"]),
            "title": chat["title"],
            "created_at": chat["created_at"].isoformat() if chat.get("created_at") else None,
            "updated_at": chat["updated_at"].isoformat() if chat.get("updated_at") else None
        }
        chat_list.append(chat_data)
    
    return create_json_response({"chats": chat_list})

@app.post("/chats")
async def create_chat(
    chat: ChatCreate, 
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new chat"""
    db = get_database()
    
    chat_doc = {
        "user_id": ObjectId(current_user["_id"]),
        "title": chat.title,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.chats.insert_one(chat_doc)
    
    response_data = {
        "message": "Chat created successfully",
        "chat": {
            "id": str(result.inserted_id),
            "title": chat.title,
            "user_id": str(current_user["_id"]),
            "created_at": chat_doc["created_at"].isoformat(),
            "updated_at": chat_doc["updated_at"].isoformat()
        }
    }
    
    return create_json_response(response_data)

@app.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str, 
    current_user: dict = Depends(get_current_active_user)
):
    """Get messages for a specific chat"""
    db = get_database()
    
    # Verify chat belongs to user
    chat = await db.chats.find_one({
        "_id": ObjectId(chat_id),
        "user_id": ObjectId(current_user["_id"])
    })
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = await db.messages.find(
        {"chat_id": ObjectId(chat_id)}
    ).sort("timestamp", 1).to_list(1000)
    
    # Convert ObjectIds to strings and dates to ISO format
    message_list = []
    for message in messages:
        message_data = {
            "id": str(message["_id"]),
            "chat_id": str(message["chat_id"]),
            "sender": message["sender"],
            "content": message["content"],
            "timestamp": message["timestamp"].isoformat() if message.get("timestamp") else None
        }
        message_list.append(message_data)
    
    return create_json_response({"messages": message_list})

@app.post("/chats/{chat_id}/messages")
async def send_message(
    chat_id: str,
    message: MessageBase,
    current_user: dict = Depends(get_current_active_user)
):
    """Send a message in a chat"""
    db = get_database()
    
    # Verify chat belongs to user
    chat = await db.chats.find_one({
        "_id": ObjectId(chat_id),
        "user_id": ObjectId(current_user["_id"])
    })
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Save user message
    user_message_doc = {
        "chat_id": ObjectId(chat_id),
        "sender": "user",
        "content": message.content,
        "timestamp": datetime.utcnow()
    }
    
    user_result = await db.messages.insert_one(user_message_doc)
    
    # Process message with AI (if it's a search query)
    ai_response = "I received your message. This is a placeholder response."
    
    # If message contains search intent, perform semantic search
    if any(keyword in message.content.lower() for keyword in ['search', 'find', 'what', 'how', 'when', 'where']):
        try:
            # Get user's spaces for search context
            user_spaces = await db.spaces.find({"user_id": ObjectId(current_user["_id"])}).to_list(100)
            space_ids = [str(space["_id"]) for space in user_spaces]
            
            # Perform search if spaces exist
            if space_ids:
                search_results = semantic_searcher.search_documents_in_spaces(
                    query=message.content,
                    space_ids=space_ids,
                    max_results=5
                )
                ai_response = search_results.get("answer", "I couldn't find relevant information in your documents.")
            else:
                ai_response = "You don't have any documents uploaded yet. Please upload some documents to your spaces first."
        except Exception as e:
            ai_response = f"I encountered an error while searching: {str(e)}"
    
    # Save AI response
    ai_message_doc = {
        "chat_id": ObjectId(chat_id),
        "sender": "assistant",
        "content": ai_response,
        "timestamp": datetime.utcnow()
    }
    
    ai_result = await db.messages.insert_one(ai_message_doc)
    
    # Update chat's updated_at timestamp
    await db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"updated_at": datetime.utcnow()}}
    )
    
    response_data = {
        "user_message": {
            "id": str(user_result.inserted_id),
            "content": message.content,
            "sender": "user",
            "timestamp": user_message_doc["timestamp"].isoformat()
        },
        "ai_message": {
            "id": str(ai_result.inserted_id),
            "content": ai_response,
            "sender": "assistant",
            "timestamp": ai_message_doc["timestamp"].isoformat()
        }
    }
    
    return create_json_response(response_data)

# Spaces endpoints
@app.get("/spaces")
async def list_user_spaces(current_user: dict = Depends(get_current_active_user)):
    """Get user's spaces with document counts"""
    db = get_database()
    
    spaces = await db.spaces.find(
        {"user_id": ObjectId(current_user["_id"])}
    ).sort("created_at", -1).to_list(100)
    
    spaces_with_stats = []
    for space in spaces:
        # Get document count for this space
        doc_count = await db.documents.count_documents({"space_id": space["_id"]})
        
        # Get total file size
        pipeline = [
            {"$match": {"space_id": space["_id"]}},
            {"$group": {"_id": None, "total_size": {"$sum": "$size_in_bytes"}}}
        ]
        size_result = await db.documents.aggregate(pipeline).to_list(1)
        total_size = size_result[0]["total_size"] if size_result else 0
        
        space_with_stats = {
            "id": str(space["_id"]),
            "name": space["name"],
            "description": space["description"],
            "document_count": doc_count,
            "total_size_bytes": total_size,
            "created_at": space["created_at"].isoformat() if space.get("created_at") else None,
            "updated_at": space["updated_at"].isoformat() if space.get("updated_at") else None
        }
        spaces_with_stats.append(space_with_stats)
    
    response_data = {
        "spaces": spaces_with_stats,
        "total_spaces": len(spaces_with_stats)
    }
    
    return create_json_response(response_data)

@app.post("/spaces")
async def create_space(
    space: SpaceCreate, 
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new space"""
    db = get_database()
    
    # Check if space name already exists for this user
    existing_space = await db.spaces.find_one({
        "user_id": ObjectId(current_user["_id"]),
        "name": space.name
    })
    if existing_space:
        raise HTTPException(
            status_code=400,
            detail=f"Space with name '{space.name}' already exists"
        )
    
    space_doc = {
        "user_id": ObjectId(current_user["_id"]),
        "name": space.name,
        "description": space.description,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.spaces.insert_one(space_doc)
    
    response_data = {
        "message": f"Space '{space.name}' created successfully",
        "space": {
            "id": str(result.inserted_id),
            "name": space.name,
            "description": space.description,
            "created_at": space_doc["created_at"].isoformat(),
            "updated_at": space_doc["updated_at"].isoformat()
        }
    }
    
    return create_json_response(response_data)

@app.get("/spaces/{space_id}")
async def get_space(
    space_id: str, 
    current_user: dict = Depends(get_current_active_user)
):
    """Get details of a specific space"""
    db = get_database()
    
    space = await db.spaces.find_one({
        "_id": ObjectId(space_id),
        "user_id": ObjectId(current_user["_id"])
    })
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    
    # Get documents in this space
    documents = await db.documents.find(
        {"space_id": ObjectId(space_id)}
    ).sort("uploaded_at", -1).to_list(100)
    
    # Convert document ObjectIds to strings
    doc_list = []
    total_size = 0
    for doc in documents:
        doc_info = {
            "id": str(doc["_id"]),
            "original_file_name": doc["original_file_name"],
            "file_type": doc["file_type"],
            "size_in_bytes": doc["size_in_bytes"],
            "uploaded_at": doc["uploaded_at"].isoformat() if doc.get("uploaded_at") else None
        }
        doc_list.append(doc_info)
        total_size += doc["size_in_bytes"]
    
    response_data = {
        "id": str(space["_id"]),
        "name": space["name"],
        "description": space["description"],
        "document_count": len(doc_list),
        "total_size_bytes": total_size,
        "documents": doc_list,
        "created_at": space["created_at"].isoformat() if space.get("created_at") else None,
        "updated_at": space["updated_at"].isoformat() if space.get("updated_at") else None
    }
    
    return create_json_response(response_data)

@app.put("/spaces/{space_id}")
async def update_space(
    space_id: str,
    space_update: SpaceUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update space information"""
    db = get_database()
    
    space = await db.spaces.find_one({
        "_id": ObjectId(space_id),
        "user_id": ObjectId(current_user["_id"])
    })
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    
    # Check if new name conflicts with existing spaces
    if space_update.name and space_update.name != space["name"]:
        existing_space = await db.spaces.find_one({
            "user_id": ObjectId(current_user["_id"]),
            "name": space_update.name,
            "_id": {"$ne": ObjectId(space_id)}
        })
        if existing_space:
            raise HTTPException(
                status_code=400,
                detail=f"Space with name '{space_update.name}' already exists"
            )
    
    # Update fields
    update_data = {"updated_at": datetime.utcnow()}
    if space_update.name is not None:
        update_data["name"] = space_update.name
    if space_update.description is not None:
        update_data["description"] = space_update.description
    
    await db.spaces.update_one(
        {"_id": ObjectId(space_id)},
        {"$set": update_data}
    )
    
    return create_json_response({"message": "Space updated successfully"})

@app.delete("/spaces/{space_id}")
async def delete_space(
    space_id: str, 
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a space and all its documents"""
    db = get_database()
    
    space = await db.spaces.find_one({
        "_id": ObjectId(space_id),
        "user_id": ObjectId(current_user["_id"])
    })
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    
    # Get documents to delete from vector index
    documents = await db.documents.find({"space_id": ObjectId(space_id)}).to_list(1000)
    
    # Delete documents from vector index
    for doc in documents:
        try:
            semantic_searcher.delete_document_from_space(
                doc["original_file_name"], 
                space_id
            )
        except Exception as e:
            print(f"Error deleting document from vector index: {e}")
    
    # Delete document files
    for doc in documents:
        try:
            if os.path.exists(doc["file_path"]):
                os.remove(doc["file_path"])
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    # Delete documents from database
    await db.documents.delete_many({"space_id": ObjectId(space_id)})
    
    # Delete space
    await db.spaces.delete_one({"_id": ObjectId(space_id)})
    
    response_data = {
        "message": f"Space '{space['name']}' and all its documents deleted successfully",
        "documents_deleted": len(documents)
    }
    
    return create_json_response(response_data)

# Document upload endpoint
@app.post("/spaces/{space_id}/upload")
async def upload_file_to_space(
    space_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Upload and process documents for a specific space"""
    db = get_database()
    
    # Check if space exists and belongs to user
    space = await db.spaces.find_one({
        "_id": ObjectId(space_id),
        "user_id": ObjectId(current_user["_id"])
    })
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    
    # Validate file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    # Check file size (limit to 50MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum allowed size is 50MB."
        )
    
    # Check if file already exists in this space
    existing_doc = await db.documents.find_one({
        "space_id": ObjectId(space_id),
        "original_file_name": file.filename
    })
    if existing_doc:
        raise HTTPException(
            status_code=400,
            detail=f"File '{file.filename}' already exists in this space."
        )
    
    # Create user-specific upload directory
    user_upload_dir = os.path.join(UPLOAD_DIR, str(current_user["_id"]), space_id)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Save uploaded file
    file_path = os.path.join(user_upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text from document
        extracted_text = document_loader.extract_text(file_path)
        if not extracted_text.strip():
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the document"
            )
        
        # Add document to Pinecone index
        semantic_searcher.add_document_to_space(extracted_text, file.filename, space_id)
        
        # Save document info to database
        doc_doc = {
            "space_id": ObjectId(space_id),
            "user_id": ObjectId(current_user["_id"]),
            "original_file_name": file.filename,
            "file_type": file_extension.replace('.', ''),
            "file_path": file_path,
            "size_in_bytes": file_size,
            "uploaded_at": datetime.utcnow()
        }
        
        result = await db.documents.insert_one(doc_doc)
        
        response_data = {
            "message": f"File uploaded to space '{space['name']}' successfully",
            "document": {
                "id": str(result.inserted_id),
                "filename": file.filename,
                "space_id": space_id,
                "space_name": space["name"],
                "file_size_bytes": file_size,
                "extracted_text_length": len(extracted_text),
                "status": "indexed"
            }
        }
        
        return create_json_response(response_data)
        
    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

# Enhanced search with space selection
@app.get("/search")
async def search_documents(
    q: str = Query(..., description="Search query"),
    space_ids: Optional[str] = Query(None, description="Comma-separated space IDs to search in"),
    filename: Optional[str] = Query(None, description="Filter by specific filename"),
    max_results: Optional[int] = Query(10, description="Maximum number of results", ge=1, le=50),
    current_user: dict = Depends(get_current_active_user)
):
    """Enhanced search through documents in user's selected spaces"""
    db = get_database()
    
    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )
    
    # Parse and validate space IDs
    selected_spaces = []
    if space_ids:
        selected_spaces = [s.strip() for s in space_ids.split(',') if s.strip()]
        
        # Verify all spaces belong to the user
        for space_id in selected_spaces:
            space = await db.spaces.find_one({
                "_id": ObjectId(space_id),
                "user_id": ObjectId(current_user["_id"])
            })
            if not space:
                raise HTTPException(
                    status_code=404,
                    detail=f"Space '{space_id}' not found or access denied"
                )
    else:
        # If no spaces specified, search in all user's spaces
        user_spaces = await db.spaces.find(
            {"user_id": ObjectId(current_user["_id"])}
        ).to_list(100)
        selected_spaces = [str(space["_id"]) for space in user_spaces]
    
    if not selected_spaces:
        response_data = {
            "answer": "You don't have any spaces created yet. Please create a space and upload some documents first.",
            "sources": [],
            "query": q,
            "total_results": 0,
            "documents_searched": 0,
            "spaces_searched": 0
        }
        return create_json_response(response_data)
    
    # Validate filename exists if provided
    if filename:
        doc_exists = await db.documents.find_one({
            "space_id": {"$in": [ObjectId(sid) for sid in selected_spaces]},
            "original_file_name": filename
        })
        if not doc_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{filename}' not found in selected spaces"
            )
    
    try:
        # Perform enhanced semantic search
        results = semantic_searcher.search_documents_in_spaces(
            query=q,
            space_ids=selected_spaces,
            filename_filter=filename,
            max_results=max_results
        )
        
        return create_json_response(results)
        
    except Exception as e:
        response_data = {
            "answer": f"An error occurred while searching: {str(e)}",
            "sources": [],
            "query": q,
            "space_ids": space_ids,
            "filename_filter": filename,
            "document_summary": {},
            "cross_document_insights": [],
            "total_results": 0,
            "documents_searched": 0,
            "spaces_searched": 0,
            "search_scope": 'error'
        }
        return create_json_response(response_data)

# Delete document from space
@app.delete("/spaces/{space_id}/documents/{document_id}")
async def delete_document_from_space(
    space_id: str,
    document_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a specific document from a space"""
    db = get_database()
    
    # Verify space belongs to user
    space = await db.spaces.find_one({
        "_id": ObjectId(space_id),
        "user_id": ObjectId(current_user["_id"])
    })
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    
    # Find document
    document = await db.documents.find_one({
        "_id": ObjectId(document_id),
        "space_id": ObjectId(space_id),
        "user_id": ObjectId(current_user["_id"])
    })
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete from Pinecone index
        semantic_searcher.delete_document_from_space(
            document["original_file_name"], 
            space_id
        )
        
        # Delete file from disk
        if os.path.exists(document["file_path"]):
            os.remove(document["file_path"])
        
        # Delete from database
        await db.documents.delete_one({"_id": ObjectId(document_id)})
        
        response_data = {
            "message": f"Document '{document['original_file_name']}' deleted successfully",
            "filename": document["original_file_name"],
            "space_id": space_id
        }
        
        return create_json_response(response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Check system health and component status"""
    try:
        # Test database connection
        db = get_database()
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Test semantic searcher
    try:
        health_status = semantic_searcher.health_check()
    except Exception as e:
        health_status = {"error": str(e)}
    
    # Overall health determination
    overall_health = "healthy"
    if "error" in health_status.get('gemini_api_status', ''):
        overall_health = "degraded"
    if "error" in health_status.get('pinecone_status', '') or "error" in db_status:
        overall_health = "unhealthy"
    
    response_data = {
        "status": overall_health,
        "components": {
            **health_status,
            "mongodb_status": db_status,
            "authentication": "enabled"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return create_json_response(response_data)

@app.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_active_user)):
    """Get statistics about the user's system usage"""
    db = get_database()
    
    try:
        # Get user's stats
        user_spaces_count = await db.spaces.count_documents(
            {"user_id": ObjectId(current_user["_id"])}
        )
        
        user_documents_count = await db.documents.count_documents(
            {"user_id": ObjectId(current_user["_id"])}
        )
        
        user_chats_count = await db.chats.count_documents(
            {"user_id": ObjectId(current_user["_id"])}
        )
        
        # Get total storage used by user
        pipeline = [
            {"$match": {"user_id": ObjectId(current_user["_id"])}},
            {"$group": {"_id": None, "total_size": {"$sum": "$size_in_bytes"}}}
        ]
        size_result = await db.documents.aggregate(pipeline).to_list(1)
        total_storage = size_result[0]["total_size"] if size_result else 0
        
        # Get Pinecone stats
        index_stats = semantic_searcher.get_index_stats()
        
        response_data = {
            "user_stats": {
                "spaces_count": user_spaces_count,
                "documents_count": user_documents_count,
                "chats_count": user_chats_count,
                "total_storage_bytes": total_storage
            },
            "pinecone_stats": index_stats,
            "system_info": {
                "supported_formats": SUPPORTED_EXTENSIONS,
                "max_file_size_mb": 50
            }
        }
        
        return create_json_response(response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"🚀 Starting Beecok API v2.0")
    print(f"📍 Server will run on: http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    print(f"🔐 Authentication: Enabled")
    
    uvicorn.run(app, host=host, port=port, reload=debug, log_level="info")