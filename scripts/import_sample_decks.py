"""
Script để import sample decks vào database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from datetime import datetime
from bson import ObjectId

async def import_sample_decks():
    """Import sample decks with different privacy levels"""
    
    # Connect to database
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    decks_collection = database.decks
    users_collection = database.users
    
    print("🔗 Connected to database")
    print(f"📊 Database: {settings.database_name}")
    print("-" * 50)
    
    try:
        # Get existing users to use as owners
        users = []
        async for user in users_collection.find({}):
            users.append(user)
        
        if not users:
            print("❌ No users found! Please run user creation first.")
            return
        
        # Find specific users for deck ownership
        admin_user = None
        teacher_user = None
        student_user = None
        
        for user in users:
            if user.get('role') == 'admin' and not admin_user:
                admin_user = user
            elif user.get('role') == 'teacher' and not teacher_user:
                teacher_user = user
            elif user.get('role') == 'student' and not student_user:
                student_user = user
        
        print(f"👥 Found {len(users)} users:")
        if admin_user:
            print(f"   👑 Admin: {admin_user.get('username', 'N/A')}")
        if teacher_user:
            print(f"   🎓 Teacher: {teacher_user.get('username', 'N/A')}")
        if student_user:
            print(f"   👤 Student: {student_user.get('username', 'N/A')}")
        
        # Clear existing decks
        existing_count = await decks_collection.count_documents({})
        if existing_count > 0:
            print(f"\n🗑️ Found {existing_count} existing decks. Clearing...")
            await decks_collection.delete_many({})
            print("✅ Cleared existing decks")
        
        # Sample decks data
        sample_decks = [
            # Public Decks (Everyone can access)
            {
                "title": "Basic English Vocabulary",
                "description": "Essential English words for beginners",
                "privacy_level": "public",
                "tags": ["english", "vocabulary", "beginner"],
                "difficulty_level": "beginner",
                "estimated_time_minutes": 20,
                "owner": admin_user or users[0],
                "assigned_class_ids": [],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            },
            {
                "title": "Python Programming Basics",
                "description": "Learn Python fundamentals with flashcards",
                "privacy_level": "public",
                "tags": ["python", "programming", "coding"],
                "difficulty_level": "beginner",
                "estimated_time_minutes": 45,
                "owner": teacher_user or users[1],
                "assigned_class_ids": [],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            },
            {
                "title": "Mathematics Formulas",
                "description": "Important mathematical formulas and equations",
                "privacy_level": "public",
                "tags": ["math", "formulas", "equations"],
                "difficulty_level": "intermediate",
                "estimated_time_minutes": 30,
                "owner": teacher_user or users[1],
                "assigned_class_ids": [],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            },
            
            # Private Decks (Owner only)
            {
                "title": "My Personal Study Notes",
                "description": "Private notes for personal study",
                "privacy_level": "private",
                "tags": ["personal", "notes", "study"],
                "difficulty_level": "intermediate",
                "estimated_time_minutes": 15,
                "owner": student_user or users[2],
                "assigned_class_ids": [],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            },
            {
                "title": "Admin Training Material",
                "description": "Internal training materials for administrators",
                "privacy_level": "private",
                "tags": ["admin", "training", "internal"],
                "difficulty_level": "advanced",
                "estimated_time_minutes": 60,
                "owner": admin_user or users[0],
                "assigned_class_ids": [],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            },
            
            # Class-assigned Decks
            {
                "title": "Computer Science 101",
                "description": "Introduction to Computer Science concepts",
                "privacy_level": "class-assigned",
                "tags": ["computer-science", "cs101", "intro"],
                "difficulty_level": "beginner",
                "estimated_time_minutes": 40,
                "owner": teacher_user or users[1],
                "assigned_class_ids": ["class_cs101", "class_intro"],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            },
            {
                "title": "Advanced JavaScript",
                "description": "Advanced JavaScript concepts and patterns",
                "privacy_level": "class-assigned",
                "tags": ["javascript", "advanced", "patterns"],
                "difficulty_level": "advanced",
                "estimated_time_minutes": 75,
                "owner": teacher_user or users[1],
                "assigned_class_ids": ["class_webdev", "class_advanced"],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            },
            
            # Course-assigned Decks
            {
                "title": "Database Design Principles",
                "description": "Core principles of database design and normalization",
                "privacy_level": "course-assigned",
                "tags": ["database", "design", "normalization"],
                "difficulty_level": "intermediate",
                "estimated_time_minutes": 50,
                "owner": teacher_user or users[1],
                "assigned_class_ids": [],
                "assigned_course_ids": ["course_database", "course_backend"],
                "assigned_lesson_ids": []
            },
            
            # Lesson-assigned Decks
            {
                "title": "React Hooks Deep Dive",
                "description": "Understanding React Hooks in detail",
                "privacy_level": "lesson-assigned",
                "tags": ["react", "hooks", "frontend"],
                "difficulty_level": "intermediate",
                "estimated_time_minutes": 35,
                "owner": teacher_user or users[1],
                "assigned_class_ids": [],
                "assigned_course_ids": [],
                "assigned_lesson_ids": ["lesson_react_hooks", "lesson_frontend"]
            },
            
            # More variety for testing
            {
                "title": "Spanish Conversation Starters",
                "description": "Common phrases for Spanish conversations",
                "privacy_level": "public",
                "tags": ["spanish", "conversation", "phrases"],
                "difficulty_level": "beginner",
                "estimated_time_minutes": 25,
                "owner": student_user or users[2],
                "assigned_class_ids": [],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            }
        ]
        
        print(f"\n📝 Creating {len(sample_decks)} sample decks...")
        print("-" * 50)
        
        created_decks = []
        for i, deck_data in enumerate(sample_decks, 1):
            owner = deck_data.pop("owner")
            
            # Prepare deck document
            deck_doc = {
                "title": deck_data["title"],
                "description": deck_data["description"],
                "privacy_level": deck_data["privacy_level"],
                "tags": deck_data["tags"],
                "difficulty_level": deck_data["difficulty_level"],
                "estimated_time_minutes": deck_data["estimated_time_minutes"],
                "owner_id": str(owner["_id"]),
                "owner_username": owner.get("username", "unknown"),
                "assigned_class_ids": deck_data["assigned_class_ids"],
                "assigned_course_ids": deck_data["assigned_course_ids"],
                "assigned_lesson_ids": deck_data["assigned_lesson_ids"],
                "total_cards": 0,  # Will be updated when cards are added
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert deck
            result = await decks_collection.insert_one(deck_doc)
            deck_doc["_id"] = result.inserted_id
            created_decks.append(deck_doc)
            
            print(f"✅ {i:2d}. {deck_data['title']:<30} | {deck_data['privacy_level']:<15} | Owner: {owner.get('username', 'N/A')}")
        
        print("-" * 50)
        print(f"🎉 Successfully created {len(created_decks)} decks!")
        
        # Summary by privacy level
        privacy_summary = {}
        for deck in created_decks:
            privacy = deck["privacy_level"]
            privacy_summary[privacy] = privacy_summary.get(privacy, 0) + 1
        
        print("\n📊 DECKS BY PRIVACY LEVEL:")
        for privacy, count in privacy_summary.items():
            print(f"   {privacy:<15}: {count} decks")
        
        # Show testing info
        print("\n🧪 TESTING INFO:")
        print("   🔓 Public decks: Accessible to everyone")
        print("   🔒 Private decks: Owner only")
        print("   🎓 Class-assigned: Users with matching class_ids")
        print("   📚 Course-assigned: Users with matching course_ids")
        print("   📖 Lesson-assigned: Users with matching lesson_ids")
        
        return created_decks
        
    except Exception as e:
        print(f"❌ Error creating decks: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        client.close()
        print("\n🔚 Disconnected from database")

async def check_decks_count():
    """Check how many decks exist in database"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    decks_collection = database.decks
    
    try:
        count = await decks_collection.count_documents({})
        print(f"📊 Total decks in database: {count}")
        return count
    except Exception as e:
        print(f"❌ Error checking decks: {e}")
        return 0
    finally:
        client.close()

if __name__ == "__main__":
    print("📚 DECK DATA IMPORTER")
    print("=" * 50)
    
    # Check current count
    current_count = asyncio.run(check_decks_count())
    
    if current_count > 0:
        print(f"\n⚠️ Found {current_count} existing decks.")
        print("This script will replace them with sample data.")
        confirm = input("Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Cancelled by user")
            exit(0)
    
    # Import sample decks
    decks = asyncio.run(import_sample_decks())
    
    if decks:
        print(f"\n✅ Import completed! {len(decks)} decks ready for testing Phase 4.4")
    else:
        print("\n❌ Import failed!")
