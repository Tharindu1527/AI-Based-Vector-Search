# Backend/models.py - Fixed version to prevent recursion errors
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

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

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            ObjectId: str
        }
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            ObjectId: str
        }
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            ObjectId: str
        }
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            ObjectId: str
        }
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            ObjectId: str
        }
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            ObjectId: str
        }
    )

# Health Check Models
class HealthResponse(BaseModel):
    status: str
    components: dict
    timestamp: str

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

# Stats Models
class UserStats(BaseModel):
    spaces_count: int = 0
    documents_count: int = 0
    chats_count: int = 0
    total_storage_bytes: int = 0

class StatsResponse(BaseModel):
    user_stats: UserStats
    system_info: dict
    pinecone_stats: Optional[dict] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )