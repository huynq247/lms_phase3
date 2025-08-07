"""
Script tạo Teacher user và test tất cả 3 roles
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.core.security import get_password_hash
from app.models.enums import UserRole
from datetime import datetime

async def create_teacher_user():
    """Tạo Teacher user nếu chưa có"""
    
    # Connect to database
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    users_collection = database.users
    
    print("🔗 Connected to database")
    
    try:
        # Check if teacher already exists
        teacher_email = "teacher@flashcard.com"
        existing_teacher = await users_collection.find_one({"email": teacher_email})
        
        if existing_teacher:
            print(f"👨‍🏫 Teacher user already exists: {teacher_email}")
        else:
            print("📝 Creating teacher user...")
            
            # Create teacher user
            teacher_user = {
                "username": "teacher_user",
                "email": teacher_email,
                "password_hash": get_password_hash("teacher123"),
                "full_name": "Teacher User",
                "role": UserRole.TEACHER,
                "is_active": True,
                "is_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await users_collection.insert_one(teacher_user)
            print(f"✅ Teacher user created with ID: {result.inserted_id}")
            print("📧 Email: teacher@flashcard.com")
            print("🔑 Password: teacher123")
        
        # List all users by role
        print("\n👥 USERS BY ROLE:")
        print("-" * 60)
        
        for role in [UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT]:
            print(f"\n🏷️ {role.upper()} USERS:")
            count = 0
            async for user in users_collection.find({"role": role}):
                count += 1
                username = user.get('username', 'N/A')
                email = user.get('email', 'N/A')
                print(f"  {count}. {username} ({email})")
            
            if count == 0:
                print(f"  ❌ No {role} users found")
        
        print(f"\n📊 Total users: {await users_collection.count_documents({})}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(create_teacher_user())
