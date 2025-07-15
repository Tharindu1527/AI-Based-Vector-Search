# Backend/debug_env.py
import os
from dotenv import load_dotenv

def debug_environment():
    """Debug environment variable loading"""
    
    print("=== Environment Debug ===")
    
    # Load .env file
    load_dotenv()
    
    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ .env file found: {env_file}")
        
        # Read raw file content
        with open(env_file, 'r') as f:
            content = f.read()
        print(f"📄 .env file content length: {len(content)} characters")
        
        # Show first few lines
        lines = content.split('\n')[:10]
        print("📋 First 10 lines of .env:")
        for i, line in enumerate(lines, 1):
            if line.strip() and not line.startswith('#'):
                # Hide password for security
                if 'MONGODB_URL' in line:
                    print(f"  {i}: MONGODB_URL=mongodb+srv://username:***@cluster...")
                elif 'SECRET_KEY' in line:
                    print(f"  {i}: SECRET_KEY=***")
                elif 'API_KEY' in line:
                    print(f"  {i}: {line.split('=')[0]}=***")
                else:
                    print(f"  {i}: {line}")
            else:
                print(f"  {i}: {line}")
    else:
        print(f"❌ .env file not found: {env_file}")
    
    # Check environment variables
    print("\n=== Environment Variables ===")
    
    mongodb_url = os.getenv('MONGODB_URL')
    print(f"MONGODB_URL loaded: {'Yes' if mongodb_url else 'No'}")
    if mongodb_url:
        print(f"MONGODB_URL length: {len(mongodb_url)} characters")
        print(f"MONGODB_URL starts with: {mongodb_url[:30]}...")
        print(f"MONGODB_URL contains database: {'Beecok' in mongodb_url}")
        
        # Check for problematic characters
        problematic_chars = ['&', '?', '=', ' ']
        issues = []
        for char in problematic_chars:
            if char in mongodb_url:
                count = mongodb_url.count(char)
                issues.append(f"'{char}' appears {count} times")
        
        if issues:
            print(f"⚠️  Special characters found: {', '.join(issues)}")
        else:
            print("✅ No problematic characters detected")
    
    database_name = os.getenv('DATABASE_NAME')
    print(f"DATABASE_NAME: {database_name}")
    
    secret_key = os.getenv('SECRET_KEY')
    print(f"SECRET_KEY loaded: {'Yes' if secret_key else 'No'}")
    
    # Test connection string parsing
    print("\n=== Connection String Test ===")
    if mongodb_url:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(mongodb_url)
            print(f"✅ URL parsing successful")
            print(f"   Scheme: {parsed.scheme}")
            print(f"   Hostname: {parsed.hostname}")
            print(f"   Database: {parsed.path.lstrip('/')}")
            print(f"   Query params: {len(parsed.query.split('&')) if parsed.query else 0}")
        except Exception as e:
            print(f"❌ URL parsing failed: {e}")

if __name__ == "__main__":
    debug_environment()