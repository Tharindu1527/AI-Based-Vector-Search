# debug_env.py
import os
from pathlib import Path

print("=== Environment Debug ===")

# Check if .env file exists
env_path = Path('.env')
print(f".env file exists: {env_path.exists()}")

if env_path.exists():
    print(f".env file size: {env_path.stat().st_size} bytes")
    
    # Read raw file content
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"Raw .env content:\n{content[:200]}...")

# Test dotenv loading
from dotenv import load_dotenv
load_dotenv()

# Check environment variables
api_key = os.getenv('PINECONE_API_KEY')
print(f"\nLoaded PINECONE_API_KEY: {api_key}")
print(f"API key length: {len(api_key) if api_key else 0}")
print(f"API key starts with 'pcsk_': {api_key.startswith('pcsk_') if api_key else False}")