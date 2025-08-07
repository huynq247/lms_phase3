"""
Test script để debug Deck endpoints
"""
import asyncio
import requests
import json

BASE_URL = "http://localhost:8000"

async def test_deck_endpoints():
    """Test all deck endpoints"""
    
    # 1. Login first
    print("🔐 Testing Login...")
    login_data = {
        "email": "admin@flashcard.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"Login Response: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful")
            
            # 2. Test GET /api/v1/decks
            print("\n📚 Testing GET /api/v1/decks...")
            response = requests.get(f"{BASE_URL}/api/v1/decks", headers=headers)
            print(f"GET Decks Response: {response.status_code}")
            print(f"Response Content: {response.text}")
            
            if response.status_code == 200:
                decks = response.json()
                print(f"✅ Found {decks['total_count']} decks")
                
                # 3. Test POST /api/v1/decks - Create deck
                print("\n📝 Testing POST /api/v1/decks...")
                deck_data = {
                    "title": "Test Deck from Python",
                    "description": "A test deck created for Phase 4.4 testing",
                    "privacy_level": "public",
                    "tags": ["test", "python", "phase4"],
                    "difficulty_level": "beginner",
                    "estimated_time_minutes": 15
                }
                
                response = requests.post(f"{BASE_URL}/api/v1/decks", json=deck_data, headers=headers)
                print(f"POST Deck Response: {response.status_code}")
                print(f"Response Content: {response.text}")
                
                if response.status_code == 201:
                    new_deck = response.json()
                    deck_id = new_deck["id"]
                    print(f"✅ Created deck with ID: {deck_id}")
                    
                    # 4. Test GET /api/v1/decks/{id}
                    print(f"\n🔍 Testing GET /api/v1/decks/{deck_id}...")
                    response = requests.get(f"{BASE_URL}/api/v1/decks/{deck_id}", headers=headers)
                    print(f"GET Deck Response: {response.status_code}")
                    print(f"Response Content: {response.text}")
                    
                    # 5. Test PUT /api/v1/decks/{id}
                    print(f"\n✏️ Testing PUT /api/v1/decks/{deck_id}...")
                    update_data = {
                        "title": "Updated Test Deck",
                        "description": "Updated description",
                        "difficulty_level": "intermediate"
                    }
                    
                    response = requests.put(f"{BASE_URL}/api/v1/decks/{deck_id}", json=update_data, headers=headers)
                    print(f"PUT Deck Response: {response.status_code}")
                    print(f"Response Content: {response.text}")
                    
                    # 6. Test DELETE /api/v1/decks/{id}
                    print(f"\n🗑️ Testing DELETE /api/v1/decks/{deck_id}...")
                    response = requests.delete(f"{BASE_URL}/api/v1/decks/{deck_id}", headers=headers)
                    print(f"DELETE Deck Response: {response.status_code}")
                    print(f"Response Content: {response.text}")
                else:
                    print(f"❌ Failed to create deck: {response.text}")
            else:
                print(f"❌ Failed to get decks: {response.text}")
        else:
            print(f"❌ Login failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 DECK ENDPOINTS TESTING")
    print("=" * 50)
    asyncio.run(test_deck_endpoints())
