"""
Test multimedia upload endpoints for flashcards.
Tests image and audio file uploads with validation.
"""

import requests
import json
import os
from io import BytesIO
from PIL import Image

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@flashcard.com"
ADMIN_PASSWORD = "admin123"

# Global variables
access_token = None
test_deck_id = "6894f7d942907590250f3fb9"  # Using existing deck
test_flashcard_id = None

def login_admin():
    """Login as admin and get access token."""
    global access_token
    
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        print("✅ Admin login successful")
        return True
    else:
        print(f"❌ Admin login failed: {response.status_code} - {response.text}")
        return False

def get_auth_headers():
    """Get authorization headers."""
    return {"Authorization": f"Bearer {access_token}"}

def create_test_flashcard():
    """Create a test flashcard for multimedia testing."""
    global test_flashcard_id
    
    flashcard_data = {
        "front": {
            "text": "Test Flashcard for Multimedia",
            "format": "text"
        },
        "back": {
            "text": "This flashcard is for testing multimedia uploads",
            "format": "text"
        },
        "difficulty_level": "easy",
        "tags": ["test", "multimedia"]
    }
    
    response = requests.post(
        f"{BASE_URL}/decks/{test_deck_id}/flashcards",
        json=flashcard_data,
        headers=get_auth_headers()
    )
    
    if response.status_code == 201:
        result = response.json()
        test_flashcard_id = result["_id"]
        print(f"✅ Created test flashcard: {test_flashcard_id}")
        return True
    else:
        print(f"❌ Failed to create test flashcard: {response.status_code} - {response.text}")
        return False

def create_test_image():
    """Create a test image file."""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def create_test_audio():
    """Create a test audio file (mock)."""
    # Create a simple mock audio file
    audio_data = b"FAKE_AUDIO_DATA_FOR_TESTING" * 100
    return BytesIO(audio_data)

def test_upload_question_image():
    """Test uploading image for question side."""
    print("\n📸 Testing Question Image Upload...")
    
    test_image = create_test_image()
    
    files = {
        'file': ('test_question.png', test_image, 'image/png')
    }
    
    response = requests.post(
        f"{BASE_URL}/multimedia/flashcards/{test_flashcard_id}/upload/question-image",
        files=files,
        headers=get_auth_headers()
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCCESS - Question image uploaded: {result['file_url']}")
        return True
    else:
        print(f"   ❌ ERROR - {response.text}")
        return False

def test_upload_answer_image():
    """Test uploading image for answer side."""
    print("\n📸 Testing Answer Image Upload...")
    
    test_image = create_test_image()
    
    files = {
        'file': ('test_answer.png', test_image, 'image/png')
    }
    
    response = requests.post(
        f"{BASE_URL}/multimedia/flashcards/{test_flashcard_id}/upload/answer-image",
        files=files,
        headers=get_auth_headers()
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCCESS - Answer image uploaded: {result['file_url']}")
        return True
    else:
        print(f"   ❌ ERROR - {response.text}")
        return False

def test_upload_question_audio():
    """Test uploading audio for question side."""
    print("\n🎵 Testing Question Audio Upload...")
    
    test_audio = create_test_audio()
    
    files = {
        'file': ('test_question.mp3', test_audio, 'audio/mpeg')
    }
    
    response = requests.post(
        f"{BASE_URL}/multimedia/flashcards/{test_flashcard_id}/upload/question-audio",
        files=files,
        headers=get_auth_headers()
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCCESS - Question audio uploaded: {result['file_url']}")
        return True
    else:
        print(f"   ❌ ERROR - {response.text}")
        return False

def test_upload_answer_audio():
    """Test uploading audio for answer side."""
    print("\n🎵 Testing Answer Audio Upload...")
    
    test_audio = create_test_audio()
    
    files = {
        'file': ('test_answer.mp3', test_audio, 'audio/mpeg')
    }
    
    response = requests.post(
        f"{BASE_URL}/multimedia/flashcards/{test_flashcard_id}/upload/answer-audio",
        files=files,
        headers=get_auth_headers()
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCCESS - Answer audio uploaded: {result['file_url']}")
        return True
    else:
        print(f"   ❌ ERROR - {response.text}")
        return False

def test_delete_media():
    """Test deleting media from flashcard."""
    print("\n🗑️ Testing Media Deletion...")
    
    response = requests.delete(
        f"{BASE_URL}/multimedia/flashcards/{test_flashcard_id}/media/question_image",
        headers=get_auth_headers()
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCCESS - Media deleted: {result['message']}")
        return True
    else:
        print(f"   ❌ ERROR - {response.text}")
        return False

def test_file_validation():
    """Test file validation (size and type)."""
    print("\n🔍 Testing File Validation...")
    
    # Test invalid file type
    invalid_file = BytesIO(b"This is not an image")
    files = {
        'file': ('test.txt', invalid_file, 'text/plain')
    }
    
    response = requests.post(
        f"{BASE_URL}/multimedia/flashcards/{test_flashcard_id}/upload/question-image",
        files=files,
        headers=get_auth_headers()
    )
    
    if response.status_code == 400:
        print("   ✅ SUCCESS - Invalid file type rejected")
        return True
    else:
        print(f"   ❌ ERROR - Invalid file type not rejected: {response.status_code}")
        return False

def cleanup_test_flashcard():
    """Delete the test flashcard."""
    if test_flashcard_id:
        response = requests.delete(
            f"{BASE_URL}/flashcards/{test_flashcard_id}",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            print(f"✅ Cleaned up test flashcard: {test_flashcard_id}")
        else:
            print(f"⚠️ Failed to cleanup test flashcard: {response.status_code}")

def main():
    """Run all multimedia tests."""
    print("🎬 Multimedia Upload Endpoints Test")
    print("=" * 50)
    
    # Step 1: Login
    print("📋 Step 1: Admin Login")
    if not login_admin():
        return
    
    # Step 2: Create test flashcard
    print("\n📋 Step 2: Create Test Flashcard")
    if not create_test_flashcard():
        return
    
    # Step 3: Test multimedia uploads
    print("\n📋 Step 3: Test Multimedia Uploads")
    print("🎬 Testing Multimedia Upload Endpoints:")
    print("=" * 50)
    
    test_results = []
    
    # Test each endpoint
    test_results.append(("Question Image Upload", test_upload_question_image()))
    test_results.append(("Answer Image Upload", test_upload_answer_image()))
    test_results.append(("Question Audio Upload", test_upload_question_audio()))
    test_results.append(("Answer Audio Upload", test_upload_answer_audio()))
    test_results.append(("Media Deletion", test_delete_media()))
    test_results.append(("File Validation", test_file_validation()))
    
    # Step 4: Cleanup
    print("\n📋 Step 4: Cleanup")
    cleanup_test_flashcard()
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    print(f"🎯 Multimedia upload endpoints testing completed!")
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED!")
    else:
        print("⚠️ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
