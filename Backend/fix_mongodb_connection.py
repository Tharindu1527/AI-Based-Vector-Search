# Backend/fix_mongodb_connection.py
import os
import re
from urllib.parse import quote_plus
from dotenv import load_dotenv

def fix_mongodb_connection():
    """Fix MongoDB connection string formatting issues"""
    
    load_dotenv()
    
    print("=== MongoDB Connection String Fixer ===")
    
    # Get current connection string
    mongodb_url = os.getenv('MONGODB_URL')
    
    if not mongodb_url:
        print("❌ MONGODB_URL not found in .env file")
        return
    
    print(f"Current URL: {mongodb_url}")
    print(f"URL Length: {len(mongodb_url)}")
    
    # Common issues and fixes
    print("\n🔧 Analyzing connection string...")
    
    # Check for common issues
    issues = []
    
    # 1. Check for unencoded special characters in password
    if '@' in mongodb_url:
        # Extract password part
        pattern = r'mongodb\+srv://([^:]+):([^@]+)@'
        match = re.search(pattern, mongodb_url)
        if match:
            username = match.group(1)
            password = match.group(2)
            
            print(f"Username: {username}")
            print(f"Password: {password}")
            
            # Check for special characters that need encoding
            special_chars = ['@', '#', '%', '&', '=', '?', '/', '\\', ' ', '+']
            found_special = [char for char in special_chars if char in password]
            
            if found_special:
                issues.append(f"Password contains special characters: {found_special}")
                
                # URL encode the password
                encoded_password = quote_plus(password)
                print(f"Encoded password: {encoded_password}")
                
                # Create fixed URL
                fixed_url = mongodb_url.replace(f":{password}@", f":{encoded_password}@")
                print(f"\n✅ Fixed URL: {fixed_url}")
                
                return fixed_url
    
    # 2. Check for malformed query parameters
    if '?' in mongodb_url:
        query_part = mongodb_url.split('?')[1]
        params = query_part.split('&')
        
        malformed_params = []
        for param in params:
            if '=' not in param:
                malformed_params.append(param)
        
        if malformed_params:
            issues.append(f"Malformed query parameters: {malformed_params}")
    
    # 3. Check for double encoding
    if '%25' in mongodb_url:
        issues.append("Possible double encoding detected")
    
    # 4. Check for invalid characters
    invalid_chars = [' ', '\n', '\r', '\t']
    found_invalid = [char for char in invalid_chars if char in mongodb_url]
    if found_invalid:
        issues.append(f"Invalid characters found: {repr(found_invalid)}")
    
    if issues:
        print("⚠️  Issues found:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("✅ No obvious issues found with connection string format")
    
    return None

def create_correct_connection_string():
    """Interactive helper to create correct connection string"""
    
    print("\n=== Create Correct Connection String ===")
    print("Let's build a correct MongoDB Atlas connection string step by step:")
    
    # Get components
    username = input("Enter your MongoDB username: ").strip()
    password = input("Enter your MongoDB password: ").strip()
    cluster = input("Enter your cluster name (e.g., cluster0.abc123.mongodb.net): ").strip()
    database = input("Enter your database name (default: Beecok): ").strip() or "Beecok"
    
    # URL encode the password
    encoded_password = quote_plus(password)
    
    # Build connection string
    connection_string = f"mongodb+srv://{username}:{encoded_password}@{cluster}/{database}?retryWrites=true&w=majority"
    
    print(f"\n✅ Generated connection string:")
    print(connection_string)
    
    # Write to .env file
    update_env = input("\nDo you want to update your .env file? (y/n): ").strip().lower()
    if update_env == 'y':
        update_env_file(connection_string)
    
    return connection_string

def update_env_file(new_mongodb_url):
    """Update .env file with new MongoDB URL"""
    
    env_file = ".env"
    
    if os.path.exists(env_file):
        # Read current content
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update MONGODB_URL line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('MONGODB_URL='):
                lines[i] = f"MONGODB_URL={new_mongodb_url}\n"
                updated = True
                break
        
        # If not found, add it
        if not updated:
            lines.append(f"MONGODB_URL={new_mongodb_url}\n")
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Updated {env_file}")
    else:
        # Create new .env file
        with open(env_file, 'w') as f:
            f.write(f"MONGODB_URL={new_mongodb_url}\n")
            f.write("DATABASE_NAME=Beecok\n")
            f.write("SECRET_KEY=your-secret-key-here\n")
        
        print(f"✅ Created {env_file}")

def test_connection_string(mongodb_url):
    """Test a MongoDB connection string"""
    
    print(f"\n=== Testing Connection String ===")
    
    try:
        import asyncio
        from motor.motor_asyncio import AsyncIOMotorClient
        
        async def test_connection():
            client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=5000)
            await client.admin.command('ping')
            print("✅ Connection successful!")
            client.close()
            return True
        
        return asyncio.run(test_connection())
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("MongoDB Connection String Troubleshooter")
    print("=" * 50)
    
    # Try to fix current connection string
    fixed_url = fix_mongodb_connection()
    
    if fixed_url:
        print(f"\n🔧 Testing fixed connection string...")
        if test_connection_string(fixed_url):
            update_env = input("\nConnection successful! Update .env file? (y/n): ").strip().lower()
            if update_env == 'y':
                update_env_file(fixed_url)
        else:
            print("❌ Fixed connection string still doesn't work")
    
    # Option to create new connection string
    create_new = input("\nDo you want to create a new connection string from scratch? (y/n): ").strip().lower()
    if create_new == 'y':
        new_url = create_correct_connection_string()
        if new_url:
            test_connection_string(new_url)