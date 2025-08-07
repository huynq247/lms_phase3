"""
Script để kiểm tra và tạo admin user đầu tiên
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.core.security import get_password_hash
from app.models.enums import UserRole
from datetime import datetime

async def check_and_create_admin():
    """Kiểm tra database và tạo admin user đầu tiên nếu cần"""
    
    # Kết nối database
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    users_collection = database.users
    
    print(f"🔗 Connected to database: {settings.database_name}")
    print(f"🌐 MongoDB URL: {settings.mongodb_url}")
    
    try:
        # Kiểm tra xem có user nào không
        user_count = await users_collection.count_documents({})
        print(f"👥 Current users in database: {user_count}")
        
        if user_count == 0:
            print("📝 No users found. Creating admin user...")
            
            # Tạo admin user
            admin_user = {
                "username": "admin",
                "email": "admin@flashcard.com",
                "password_hash": get_password_hash("admin123"),
                "full_name": "System Administrator",
                "role": UserRole.ADMIN,
                "is_active": True,
                "is_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await users_collection.insert_one(admin_user)
            print(f"✅ Admin user created with ID: {result.inserted_id}")
            print("📧 Email: admin@flashcard.com")
            print("🔑 Password: admin123")
            
        else:
            print("📋 Existing users:")
            async for user in users_collection.find({}, {"username": 1, "email": 1, "role": 1, "is_active": 1}):
                print(f"  - {user['username']} ({user['email']}) - {user.get('role', 'unknown')} - Active: {user.get('is_active', False)}")
        
        # Tạo thêm test user
        test_user_email = "test@example.com"
        existing_test = await users_collection.find_one({"email": test_user_email})
        
        if not existing_test:
            print("\n👤 Creating test user...")
            test_user = {
                "username": "testuser",
                "email": test_user_email,
                "password_hash": get_password_hash("test123"),
                "full_name": "Test User",
                "role": UserRole.STUDENT,
                "is_active": True,
                "is_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await users_collection.insert_one(test_user)
            print(f"✅ Test user created with ID: {result.inserted_id}")
            print("📧 Email: test@example.com")
            print("🔑 Password: test123")
        else:
            print("👤 Test user already exists")
            
        print(f"\n📊 Total users: {await users_collection.count_documents({})}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(check_and_create_admin())
