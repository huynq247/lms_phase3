#!/usr/bin/env python3
"""
Test script for flashcard CRUD endpoints
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
            print(f"✅ Using existing deck: {deck['_id']} - {deck.get('title', 'No title')}")
            client.close()
            return str(deck['_id'])
        
        print("❌ No deck found for testing")
        client.close()
        return None
        
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

def test_flashcard_endpoints(token, deck_id):
    """Test all flashcard CRUD endpoints"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n🃏 Testing Flashcard CRUD Endpoints:")
    print("=" * 50)
    
    created_flashcard_id = None
    
    # Test 1: Get deck flashcards (should be empty initially)
    print("\n1️⃣ Testing GET /decks/{deck_id}/flashcards")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/decks/{deck_id}/flashcards", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - Found {data['total_count']} flashcards")
        else:
            print(f"   ❌ FAILED - {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
    
    # Test 2: Create a flashcard
    print(f"\n2️⃣ Testing POST /decks/{deck_id}/flashcards")
    try:
        flashcard_data = {
            "front": {
                "text": "What is Python?",
                "rich_text": {
                    "format": "html",
                    "content": "<p><strong>What</strong> is <em>Python</em>?</p>"
                }
            },
            "back": {
                "text": "Python is a high-level programming language.",
                "rich_text": {
                    "format": "html",
                    "content": "<p>Python is a <strong>high-level</strong> programming language.</p>"
                }
            },
            "hint": "Think about programming languages",
            "explanation": "Python is known for its simplicity and readability.",
            "difficulty_level": "easy",
            "tags": ["python", "programming", "language"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/decks/{deck_id}/flashcards", 
            headers=headers, 
            json=flashcard_data
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")  # Debug: show all keys
            # Use _id since that's what the API returns
            if "_id" in data:
                created_flashcard_id = data["_id"]
                print(f"   ✅ SUCCESS - Created flashcard: {created_flashcard_id}")
            elif "id" in data:
                created_flashcard_id = data["id"]
                print(f"   ✅ SUCCESS - Created flashcard: {created_flashcard_id}")
            else:
                print(f"   ⚠️  SUCCESS but no 'id' or '_id' field - Response: {data}")
        else:
            print(f"   ❌ FAILED - {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
    
    # Test 3: Get specific flashcard
    if created_flashcard_id:
        print(f"\n3️⃣ Testing GET /flashcards/{created_flashcard_id}")
        try:
            response = requests.get(f"{BASE_URL}/api/v1/flashcards/{created_flashcard_id}", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS - Retrieved flashcard: {data['front']['text']}")
            else:
                print(f"   ❌ FAILED - {response.text}")
        except Exception as e:
            print(f"   ❌ ERROR - {e}")
    
    # Test 4: Update flashcard
    if created_flashcard_id:
        print(f"\n4️⃣ Testing PUT /flashcards/{created_flashcard_id}")
        try:
            update_data = {
                "front": {
                    "text": "What is Python programming language?",
                    "rich_text": {
                        "format": "html",
                        "content": "<p><strong>What</strong> is <em>Python programming language</em>?</p>"
                    }
                },
                "difficulty_level": "medium",
                "tags": ["python", "programming", "language", "updated"]
            }
            
            response = requests.put(
                f"{BASE_URL}/api/v1/flashcards/{created_flashcard_id}", 
                headers=headers, 
                json=update_data
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS - Updated flashcard: {data['front']['text']}")
            else:
                print(f"   ❌ FAILED - {response.text}")
        except Exception as e:
            print(f"   ❌ ERROR - {e}")
    
    # Test 5: Bulk create flashcards
    print(f"\n5️⃣ Testing POST /flashcards/deck/{deck_id}/bulk")
    try:
        bulk_data = {
            "flashcards": [
                {
                    "front": {"text": "What is a variable?"},
                    "back": {"text": "A variable is a container for storing data values."},
                    "difficulty_level": "easy",
                    "tags": ["python", "variables"]
                },
                {
                    "front": {"text": "What is a function?"},
                    "back": {"text": "A function is a block of code which only runs when it is called."},
                    "difficulty_level": "easy",
                    "tags": ["python", "functions"]
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/flashcards/deck/{deck_id}/bulk", 
            headers=headers, 
            json=bulk_data
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ SUCCESS - Bulk created {data['created_count']} flashcards")
        else:
            print(f"   ❌ FAILED - {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
    
    # Test 6: Get deck flashcards again (should have more now)
    print(f"\n6️⃣ Testing GET /decks/{deck_id}/flashcards (after creation)")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/decks/{deck_id}/flashcards", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - Now found {data['total_count']} flashcards")
            for i, card in enumerate(data['flashcards'][:3]):  # Show first 3
                print(f"      Card {i+1}: {card['front']['text']}")
        else:
            print(f"   ❌ FAILED - {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
    
    # Test 7: Test filtering
    print(f"\n7️⃣ Testing GET /decks/{deck_id}/flashcards?tags=python&difficulty=easy")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/decks/{deck_id}/flashcards?tags=python&difficulty=easy", 
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - Filtered to {data['total_count']} easy Python flashcards")
        else:
            print(f"   ❌ FAILED - {response.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
    
    # Test 8: Delete flashcard (optional - only if we created one)
    if created_flashcard_id:
        print(f"\n8️⃣ Testing DELETE /flashcards/{created_flashcard_id}")
        try:
            response = requests.delete(f"{BASE_URL}/api/v1/flashcards/{created_flashcard_id}", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - Deleted flashcard")
            else:
                print(f"   ❌ FAILED - {response.text}")
        except Exception as e:
            print(f"   ❌ ERROR - {e}")

async def main():
    """Main test function"""
    print("🃏 Flashcard CRUD Endpoints Test")
    print("=" * 35)
    
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
    print("\n📋 Step 3: Test Flashcard CRUD Endpoints")
    test_flashcard_endpoints(token, deck_id)
    
    print("\n" + "=" * 50)
    print("🎯 Flashcard CRUD endpoints testing completed!")

if __name__ == "__main__":
    asyncio.run(main())
