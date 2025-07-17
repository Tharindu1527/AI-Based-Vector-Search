import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import Optional

# Load environment variables explicitly with override
load_dotenv(override=True)

# MongoDB connection settings - handle special characters in password
MONGODB_URL = os.getenv('MONGODB_URL')
DATABASE_NAME = os.getenv("DATABASE_NAME", "Beecok")

# Add debugging
print("=" * 50)
print("ENVIRONMENT VARIABLES DEBUG:")
print(f"MONGODB_URL: {'Set' if MONGODB_URL else 'Not Set'}")
print(f"DATABASE_NAME: {DATABASE_NAME}")
print(f"Environment loaded from: {os.path.abspath('.env') if os.path.exists('.env') else 'No .env file found'}")
print("=" * 50)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None
    connected = False

# Global database instance
db = Database()

async def connect_to_mongo():
    """Create database connection with retry logic"""
    if not MONGODB_URL:
        print("⚠️  MONGODB_URL is not set. Using mock database for development.")
        print("🔧 To use MongoDB, set MONGODB_URL in your .env file")
        db.connected = False
        db.database = MockDatabase()
        return True
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to MongoDB (attempt {attempt + 1}/{max_retries})...")
            
            # Create client with timeout settings
            db.client = AsyncIOMotorClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=10000,  # 10 second timeout
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=10,
                minPoolSize=1
            )
            
            # Test the connection
            await db.client.admin.command('ping')
            
            # Set database
            db.database = db.client[DATABASE_NAME]
            db.connected = True
            
            print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
            
            # Create indexes for better performance
            await create_indexes()
            
            return True
            
        except Exception as e:
            print(f"❌ MongoDB connection attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("❌ All MongoDB connection attempts failed!")
                print("🔧 Using mock database for development")
                print("💡 To fix this, check your MONGODB_URL in .env file")
                
                db.connected = False
                db.database = MockDatabase()
                return True

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        db.connected = False
        print("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes"""
    if not db.connected or db.database is None:
        return
        
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
        
        print("✅ Database indexes created successfully")
        
    except Exception as e:
        print(f"⚠️  Error creating indexes: {e}")

def get_database():
    """Get database instance with better error handling"""
    if db.database is None:
        print("⚠️  Database not initialized. Using mock database.")
        return MockDatabase()
    return db.database

def is_connected():
    """Check if database is connected"""
    return db.connected

# Mock database for development when MongoDB is not available
class MockCollection:
    def __init__(self):
        self.data = []
        self._id_counter = 1
    
    async def find_one(self, query):
        for item in self.data:
            if self._match_query(item, query):
                return item
        return None
    
    def find(self, query=None):
        class MockCursor:
            def __init__(self, data, query):
                self.data = data
                self.query = query or {}
            
            def sort(self, *args):
                return self
            
            async def to_list(self, limit=None):
                results = []
                for item in self.data:
                    if self._match_query(item, self.query):
                        results.append(item)
                return results[:limit] if limit else results
            
            def _match_query(self, item, query):
                from bson import ObjectId
                for key, value in query.items():
                    if key == "_id" and isinstance(value, ObjectId):
                        if str(item.get(key, "")) != str(value):
                            return False
                    elif key not in item or item[key] != value:
                        return False
                return True
        
        return MockCursor(self.data, query)
    
    async def insert_one(self, document):
        from bson import ObjectId
        document['_id'] = ObjectId()
        self.data.append(document)
        return type('Result', (), {'inserted_id': document['_id']})()
    
    async def update_one(self, query, update):
        for item in self.data:
            if self._match_query(item, query):
                if '$set' in update:
                    item.update(update['$set'])
                return type('Result', (), {'modified_count': 1})()
        return type('Result', (), {'modified_count': 0})()
    
    async def delete_one(self, query):
        for i, item in enumerate(self.data):
            if self._match_query(item, query):
                self.data.pop(i)
                return type('Result', (), {'deleted_count': 1})()
        return type('Result', (), {'deleted_count': 0})()
    
    async def delete_many(self, query):
        original_length = len(self.data)
        self.data = [item for item in self.data if not self._match_query(item, query)]
        deleted = original_length - len(self.data)
        return type('Result', (), {'deleted_count': deleted})()
    
    async def count_documents(self, query):
        count = 0
        for item in self.data:
            if self._match_query(item, query):
                count += 1
        return count
    
    def aggregate(self, pipeline):
        class MockAggregate:
            async def to_list(self, limit=None):
                return []
        return MockAggregate()
    
    async def create_index(self, *args, **kwargs):
        pass  # Mock index creation
    
    def _match_query(self, item, query):
        from bson import ObjectId
        for key, value in query.items():
            if key == "_id" and isinstance(value, ObjectId):
                if str(item.get(key, "")) != str(value):
                    return False
            elif key == "$in" and isinstance(value, list):
                if item.get(key.replace("$in", "")) not in value:
                    return False
            elif key not in item or item[key] != value:
                return False
        return True

class MockDatabase:
    def __init__(self):
        self.users = MockCollection()
        self.chats = MockCollection()
        self.messages = MockCollection()
        self.spaces = MockCollection()
        self.documents = MockCollection()
        print("✅ Mock database initialized for development")
    
    async def command(self, command):
        return {"ok": 1.0}  # Mock successful ping