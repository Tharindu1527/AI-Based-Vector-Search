from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# User Models
class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class User(UserBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Chat Models
class ChatBase(BaseModel):
    title: Optional[str] = "New Chat"


class ChatCreate(ChatBase):
    pass


class Chat(ChatBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Message Models
class MessageBase(BaseModel):
    content: str
    sender: str  # "user" or "assistant"


class MessageCreate(MessageBase):
    chat_id: str


class Message(MessageBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    chat_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Space Models
class SpaceBase(BaseModel):
    name: str
    description: Optional[str] = ""


class SpaceCreate(SpaceBase):
    pass


class SpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Space(SpaceBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Document Models
class DocumentBase(BaseModel):
    original_file_name: str
    file_type: str
    file_path: str
    size_in_bytes: int


class DocumentCreate(DocumentBase):
    space_id: str


class Document(DocumentBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    space_id: PyObjectId
    user_id: PyObjectId
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None