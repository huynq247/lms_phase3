"""
Simple Phase 4.7 Flashcard CRUD Test
Test ID standardization với timeout ngắn
"""

import asyncio
import requests
import json
import time

def test_auth_id_standardization():
    """Test auth endpoint ID standardization"""
    print("🔐 Testing auth ID standardization...")
    
    login_data = {'email': 'admin@flashcard.com', 'password': 'admin123'}
    response = requests.post('http://localhost:8000/api/v1/auth/login', json=login_data)
    
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    
    # Check ID standardization
    user = data.get('user', {})
    assert 'id' in user, "User should have 'id' field"
    assert '_id' not in user, "User should not have '_id' field"
    
    print(f"✅ Auth ID standardization: {user['id']}")
    return data['access_token']

def test_deck_creation(token):
    """Test deck creation với ID standardization"""
    print("📚 Testing deck creation ID standardization...")
    
    headers = {'Authorization': f'Bearer {token}'}
    deck_data = {
        'title': 'Test Deck Phase 4.7',
        'description': 'Testing ID standardization',
        'category': 'test',
        'is_public': True
    }
    
    response = requests.post('http://localhost:8000/api/v1/decks', 
                           json=deck_data, headers=headers)
    
    assert response.status_code == 201, f"Deck creation failed: {response.text}"
    deck = response.json()
    
    # Check ID standardization
    assert 'id' in deck, "Deck should have 'id' field"
    assert '_id' not in deck, "Deck should not have '_id' field"
    
    print(f"✅ Deck ID standardization: {deck['id']}")
    return deck['id']

def test_flashcard_creation(token, deck_id):
    """Test flashcard creation với ID standardization"""
    print("🆕 Testing flashcard creation ID standardization...")
    
    headers = {'Authorization': f'Bearer {token}'}
    flashcard_data = {
        'front': {'text': 'What is Python?'},
        'back': {'text': 'Python is a programming language'},
        'difficulty_level': 'easy',
        'tags': ['python', 'test']
    }
    
    response = requests.post(
        f'http://localhost:8000/api/v1/flashcards/deck/{deck_id}',
        json=flashcard_data, headers=headers
    )
    
    assert response.status_code == 201, f"Flashcard creation failed: {response.text}"
    flashcard = response.json()
    
    # Check ID standardization
    assert 'id' in flashcard, "Flashcard should have 'id' field"
    assert '_id' not in flashcard, "Flashcard should not have '_id' field"
    
    print(f"✅ Flashcard ID standardization: {flashcard['id']}")
    return flashcard['id']

def test_flashcard_list(token, deck_id):
    """Test flashcard list với ID standardization"""
    print("📋 Testing flashcard list ID standardization...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'http://localhost:8000/api/v1/flashcards/deck/{deck_id}',
        headers=headers
    )
    
    assert response.status_code == 200, f"Flashcard list failed: {response.text}"
    data = response.json()
    
    # Check list structure and ID standardization
    assert 'flashcards' in data, "Response should have 'flashcards' field"
    flashcards = data['flashcards']
    
    for flashcard in flashcards:
        assert 'id' in flashcard, "Each flashcard should have 'id' field"
        assert '_id' not in flashcard, "Each flashcard should not have '_id' field"
    
    print(f"✅ Flashcard list ID standardization: {len(flashcards)} cards")

def test_flashcard_update(token, flashcard_id):
    """Test flashcard update với ID standardization"""
    print("✏️ Testing flashcard update ID standardization...")
    
    headers = {'Authorization': f'Bearer {token}'}
    update_data = {
        'front': {'text': 'What is Python? (Updated)'},
        'back': {'text': 'Python is a powerful programming language'},
        'difficulty_level': 'medium'
    }
    
    response = requests.put(
        f'http://localhost:8000/api/v1/flashcards/{flashcard_id}',
        json=update_data, headers=headers
    )
    
    assert response.status_code == 200, f"Flashcard update failed: {response.text}"
    flashcard = response.json()
    
    # Check ID standardization
    assert 'id' in flashcard, "Updated flashcard should have 'id' field"
    assert '_id' not in flashcard, "Updated flashcard should not have '_id' field"
    assert flashcard['id'] == flashcard_id, "ID should remain the same"
    
    print(f"✅ Flashcard update ID standardization: {flashcard['id']}")

def test_cleanup(token, deck_id):
    """Cleanup test data"""
    print("🧹 Cleaning up test data...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.delete(f'http://localhost:8000/api/v1/decks/{deck_id}', 
                              headers=headers)
    
    if response.status_code == 200:
        print("✅ Cleanup successful")
    else:
        print(f"⚠️ Cleanup warning: {response.status_code}")

def main():
    """Run all Phase 4.7 tests"""
    print("🚀 Starting Phase 4.7 Flashcard CRUD Tests with ID Standardization")
    print("=" * 60)
    
    try:
        # Test sequence
        token = test_auth_id_standardization()
        deck_id = test_deck_creation(token)
        flashcard_id = test_flashcard_creation(token, deck_id)
        test_flashcard_list(token, deck_id)
        test_flashcard_update(token, flashcard_id)
        test_cleanup(token, deck_id)
        
        print("=" * 60)
        print("🎉 ALL PHASE 4.7 TESTS PASSED!")
        print("✅ ID Standardization working correctly across all endpoints")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
