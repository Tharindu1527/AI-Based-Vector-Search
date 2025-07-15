# Backend/test_connection.py
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_mongodb_connection():
    """Test MongoDB Atlas connection"""
    
    # Your connection string with database name
    connection_string = "mongodb+srv://tharindubandara15270:2btGHkdsXeejz2F1@cluster0.6rj67vs.mongodb.net/Beecok?retryWrites=true&w=majority&appName=Cluster0"
    
    try:
        print("Testing MongoDB Atlas connection...")
        
        # Create client
        client = AsyncIOMotorClient(connection_string)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB Atlas connection successful!")
        
        # Test database access
        db = client.Beecok
        await db.test_collection.insert_one({"test": "data"})
        print("✅ Database write test successful!")
        
        # Clean up test data
        await db.test_collection.delete_one({"test": "data"})
        print("✅ Database cleanup successful!")
        
        # List databases
        databases = await client.list_database_names()
        print(f"✅ Available databases: {databases}")
        
        # Close connection
        client.close()
        print("✅ Connection closed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check your internet connection")
        print("2. Verify your IP is whitelisted in MongoDB Atlas")
        print("3. Confirm your username/password are correct")
        print("4. Check if the cluster is running")
        return False

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())