"""
Script để kiểm tra và list tất cả users trong database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from datetime import datetime

async def list_database_users():
    """List all users in database and update registry"""
    
    # Connect to database
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    users_collection = database.users
    
    print("🔗 Connected to database")
    print(f"📊 Database: {settings.database_name}")
    print(f"🌐 Host: {settings.mongodb_url}")
    print("-" * 50)
    
    try:
        # Get all users
        users = []
        async for user in users_collection.find({}):
            users.append(user)
        
        print(f"👥 Total users found: {len(users)}")
        print("-" * 50)
        
        if not users:
            print("❌ No users found in database")
            return
        
        # Display users in table format
        print("📋 USERS IN DATABASE:")
        print(f"{'Username':<15} {'Email':<25} {'Role':<10} {'Full Name':<20} {'Created':<12}")
        print("-" * 85)
        
        for user in users:
            username = user.get('username', 'N/A')
            email = user.get('email', 'N/A')
            role = user.get('role', 'N/A')
            full_name = user.get('full_name', 'N/A')
            created = user.get('created_at', 'N/A')
            
            # Format date if available
            if created != 'N/A' and hasattr(created, 'strftime'):
                created = created.strftime('%Y-%m-%d')
            elif created != 'N/A':
                created = str(created)[:10]  # First 10 chars if string
                
            print(f"{username:<15} {email:<25} {role:<10} {full_name:<20} {created:<12}")
        
        print("-" * 85)
        print(f"✅ Listed {len(users)} users successfully")
        
        # Show quick login info
        print("\n🔑 QUICK LOGIN INFO:")
        for user in users:
            if user.get('email') == 'admin@flashcard.com':
                print(f"👑 Admin: {user['email']} / admin123")
            elif user.get('email') == 'test@example.com':
                print(f"👤 Test: {user['email']} / test123")
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        client.close()
        print("\n🔚 Disconnected from database")

async def check_user_exists(email):
    """Check if user with email exists"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    users_collection = database.users
    
    try:
        user = await users_collection.find_one({"email": email})
        client.close()
        return user is not None
    except:
        client.close()
        return False

if __name__ == "__main__":
    print("🗄️ DATABASE USERS CHECKER")
    print("=" * 50)
    asyncio.run(list_database_users())
