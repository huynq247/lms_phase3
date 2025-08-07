#!/usr/bin/env python3
"""
Test script for assignment endpoints
"""
import asyncio
import requests
import json
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
DB_URL = "mongodb://admin:Root%40123@113.161.118.17:27017"
DB_NAME = "flashcard_lms_dev"

# Admin credentials
ADMIN_EMAIL = "admin@flashcard.com"
ADMIN_PASSWORD = "admin123"

async def get_sample_deck_id():
    """Get a sample deck ID from database for testing"""
    try:
        client = AsyncIOMotorClient(DB_URL)
        db = client[DB_NAME]
        
        # Try to find any existing deck
        deck = await db.decks.find_one()
        
        if deck:
            print(f"✅ Found existing deck: {deck['_id']} - {deck.get('title', 'No title')}")
            client.close()
            return str(deck['_id'])
        
        # If no deck exists, create a sample deck for testing
        print("📝 No existing deck found, creating sample deck...")
        
        # First get admin user ID
        admin_user = await db.users.find_one({"email": ADMIN_EMAIL})
        if not admin_user:
            print("❌ Admin user not found!")
            client.close()
            return None
            
        # Create sample deck
        sample_deck = {
            "title": "Test Assignment Deck",
            "description": "A test deck for assignment endpoint testing",
            "privacy_level": "private",
            "created_by": admin_user["_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "assigned_class_ids": [],
            "assigned_course_ids": [],
            "assigned_lesson_ids": [],
            "flashcards": [],
            "category_id": None,
            "tags": ["test", "assignment"]
        }
        
        result = await db.decks.insert_one(sample_deck)
        deck_id = str(result.inserted_id)
        
        print(f"✅ Created sample deck: {deck_id}")
        client.close()
        return deck_id
        
    except Exception as e:
        print(f"❌ Error getting deck ID: {e}")
        return None

def login_admin():
    """Login as admin and get token"""
    try:
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Admin login successful")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_assignment_endpoints(token, deck_id):
    """Test all assignment endpoints"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n🧪 Testing Assignment Endpoints:")
    print("=" * 50)
    
    # Test 1: Get deck assignments
    print("\n1️⃣ Testing GET /assignments/decks/{deck_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/assignments/decks/{deck_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ SUCCESS - Get deck assignments")
            data = response.json()
            print(f"   📊 Found {data.get('total', 0)} assignments")
        else:
            print(f"   ❌ FAILED - {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
    
    # Test 2: Update deck privacy
    print("\n2️⃣ Testing PUT /assignments/decks/{deck_id}/privacy")
    try:
        privacy_data = {
            "privacy_level": "public",
            "assigned_class_ids": [],
            "assigned_course_ids": [],
            "assigned_lesson_ids": []
        }
        response = requests.put(
            f"{BASE_URL}/api/v1/assignments/decks/{deck_id}/privacy", 
            headers=headers, 
            json=privacy_data
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ SUCCESS - Update deck privacy")
        else:
            print(f"   ❌ FAILED - {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
    
    # Test 3: Test assignment to class (will fail without real class ID, but endpoint should exist)
    print("\n3️⃣ Testing POST /assignments/decks/{deck_id}/assign/class/{class_id}")
    try:
        fake_class_id = "65a1b2c3d4e5f6789abcdef0"  # Valid ObjectId format
        response = requests.post(
            f"{BASE_URL}/api/v1/assignments/decks/{deck_id}/assign/class/{fake_class_id}", 
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 400, 404]:  # 400/404 expected without real class
            print("   ✅ SUCCESS - Endpoint exists and responds")
        else:
            print(f"   ❌ FAILED - {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {e}")

async def main():
    """Main test function"""
    print("🚀 Assignment Endpoints Test")
    print("=" * 30)
    
    # Step 1: Get admin token
    print("\n📋 Step 1: Admin Login")
    token = login_admin()
    if not token:
        print("❌ Cannot continue without admin token")
        return
    
    # Step 2: Get sample deck ID
    print("\n📋 Step 2: Get Sample Deck")
    deck_id = await get_sample_deck_id()
    if not deck_id:
        print("❌ Cannot continue without deck ID")
        return
    
    # Step 3: Test endpoints
    print("\n📋 Step 3: Test Assignment Endpoints")
    test_assignment_endpoints(token, deck_id)
    
    print("\n" + "=" * 50)
    print("🎯 Assignment endpoints testing completed!")

if __name__ == "__main__":
    asyncio.run(main())
