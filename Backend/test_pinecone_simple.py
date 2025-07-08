# test_pinecone_simple.py
from dotenv import load_dotenv
import os

load_dotenv()

try:
    from pinecone import Pinecone
    
    api_key = os.getenv('PINECONE_API_KEY')
    print(f"Testing with API key: {api_key[:10]}..." if api_key else "No API key found")
    
    pc = Pinecone(api_key=api_key)
    indexes = pc.list_indexes()
    print(f"✅ SUCCESS! Found indexes: {indexes.names()}")
    
except Exception as e:
    print(f"❌ FAILED: {e}")