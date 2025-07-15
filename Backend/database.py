# Backend/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config

# MongoDB connection settings
MONGODB_URL = config("MONGODB_URL", default="mongodb://localhost:27017")
DATABASE_NAME = config("DATABASE_NAME", default="Beecok")

class Database:
    client: AsyncIOMotorClient = None
    database = None

# Global database instance
db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(MONGODB_URL)
        db.database = db.client[DATABASE_NAME]
        
        # Test the connection
        await db.client.admin.command('ismaster')
        print(f"Connected to MongoDB: {DATABASE_NAME}")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes"""
    try:
        # Users collection indexes
        await db.database.users.create_index("email", unique=True)
        await db.database.users.create_index("username", unique=True)
        
        # Chats collection indexes
        await db.database.chats.create_index([("user_id", 1), ("created_at", -1)])
        
        # Messages collection indexes
        await db.database.messages.create_index([("chat_id", 1), ("timestamp", 1)])
        
        # Spaces collection indexes
        await db.database.spaces.create_index([("user_id", 1), ("created_at", -1)])
        
        # Documents collection indexes
        await db.database.documents.create_index([("space_id", 1), ("uploaded_at", -1)])
        await db.database.documents.create_index([("user_id", 1), ("uploaded_at", -1)])
        
        print("Database indexes created successfully")
        
    except Exception as e:
        print(f"Error creating indexes: {e}")

def get_database():
    """Get database instance"""
    return db.database