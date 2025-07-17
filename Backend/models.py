from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# User Models
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: Optional[str] = None

# Chat Models
class ChatBase(BaseModel):
    title: Optional[str] = Field(default="New Chat", max_length=200)

class ChatCreate(ChatBase):
    pass

class ChatResponse(BaseModel):
    id: str
    title: str
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Message Models
class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    sender: str = Field(default="user", pattern=r'^(user|assistant)$')

class MessageCreate(MessageBase):
    chat_id: str

class MessageResponse(BaseModel):
    id: str
    content: str
    sender: str
    chat_id: str
    timestamp: Optional[str] = None

# Space Models
class SpaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default="", max_length=500)

class SpaceCreate(SpaceBase):
    pass

class SpaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class SpaceResponse(BaseModel):
    id: str
    name: str
    description: str
    document_count: int = 0
    total_size_bytes: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Document Models
class DocumentBase(BaseModel):
    original_file_name: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=10)
    size_in_bytes: int = Field(..., ge=0)

class DocumentResponse(BaseModel):
    id: str
    original_file_name: str
    file_type: str
    size_in_bytes: int
    space_id: str
    uploaded_at: Optional[str] = None

# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# Search Models
class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    space_ids: Optional[List[str]] = None
    filename: Optional[str] = None
    max_results: Optional[int] = Field(default=10, ge=1, le=50)

class SearchResult(BaseModel):
    answer: str
    sources: List[dict] = []
    query: str
    total_results: int = 0
    documents_searched: int = 0
    spaces_searched: int = 0

# Health Check Models
class HealthResponse(BaseModel):
    status: str
    components: dict
    timestamp: str

# Stats Models
class UserStats(BaseModel):
    spaces_count: int = 0
    documents_count: int = 0
    chats_count: int = 0
    total_storage_bytes: int = 0

class SystemInfo(BaseModel):
    supported_formats: List[str] = []
    max_file_size_mb: int = 50

class StatsResponse(BaseModel):
    user_stats: UserStats
    system_info: SystemInfo
    pinecone_stats: Optional[dict] = None