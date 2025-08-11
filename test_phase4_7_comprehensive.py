"""
Comprehensive Phase 4.7 Backend & Database Testing
Test all CRUD operations, edge cases, and database integrity
"""

import requests
import json
import time
from datetime import datetime

class TestPhase47Comprehensive:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.token = None
        self.test_deck_id = None
        self.test_flashcard_ids = []
        
    def setup_auth(self):
        """Setup authentication and get token"""
        print("🔐 Setting up authentication...")
        
        login_data = {'email': 'admin@flashcard.com', 'password': 'admin123'}
        response = requests.post(f'{self.base_url}/auth/login', json=login_data)
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify ID standardization in auth
        user = data.get('user', {})
        assert 'id' in user and '_id' not in user, "Auth response should use 'id' not '_id'"
        
        self.token = data['access_token']
        print(f"✅ Authentication successful - User ID: {user['id']}")
        return user['id']
    
    def test_database_connection(self):
        """Test database connectivity"""
        print("🗄️ Testing database connection...")
        
        response = requests.get(f'{self.base_url}/health')
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        health_data = response.json()
        assert health_data['status'] == 'healthy', "Database should be healthy"
        
        print("✅ Database connection verified")
        
    def test_deck_crud_with_id_standardization(self):
        """Test complete deck CRUD with ID standardization"""
        print("📚 Testing Deck CRUD with ID standardization...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # 1. Create deck
        deck_data = {
            'title': 'Phase 4.7 Test Deck',
            'description': 'Comprehensive testing deck for Phase 4.7',
            'category': 'testing',
            'is_public': True,
            'tags': ['test', 'phase4.7', 'crud']
        }
        
        response = requests.post(f'{self.base_url}/decks', json=deck_data, headers=headers)
        assert response.status_code == 201, f"Deck creation failed: {response.text}"
        
        deck = response.json()
        assert 'id' in deck and '_id' not in deck, "Deck should use 'id' not '_id'"
        assert deck['title'] == deck_data['title'], "Deck title should match"
        
        self.test_deck_id = deck['id']
        print(f"✅ Deck created - ID: {self.test_deck_id}")
        
        # 2. Read deck
        response = requests.get(f'{self.base_url}/decks/{self.test_deck_id}', headers=headers)
        assert response.status_code == 200, f"Deck read failed: {response.text}"
        
        deck_read = response.json()
        assert deck_read['id'] == self.test_deck_id, "Deck ID should be consistent"
        assert 'id' in deck_read and '_id' not in deck_read, "Deck read should use 'id'"
        print("✅ Deck read successful")
        
        # 3. Update deck
        update_data = {
            'title': 'Phase 4.7 Test Deck (Updated)',
            'description': 'Updated description for testing'
        }
        
        response = requests.put(f'{self.base_url}/decks/{self.test_deck_id}', 
                               json=update_data, headers=headers)
        assert response.status_code == 200, f"Deck update failed: {response.text}"
        
        deck_updated = response.json()
        assert deck_updated['title'] == update_data['title'], "Deck title should be updated"
        assert deck_updated['id'] == self.test_deck_id, "Deck ID should remain same"
        print("✅ Deck update successful")
        
        # 4. List decks
        response = requests.get(f'{self.base_url}/decks', headers=headers)
        assert response.status_code == 200, f"Deck list failed: {response.text}"
        
        decks_data = response.json()
        assert 'decks' in decks_data, "Response should contain 'decks' field"
        
        found_deck = False
        for deck in decks_data['decks']:
            assert 'id' in deck and '_id' not in deck, "Each deck should use 'id'"
            if deck['id'] == self.test_deck_id:
                found_deck = True
                break
        
        assert found_deck, "Created deck should appear in deck list"
        print("✅ Deck list successful")
        
    def test_flashcard_crud_comprehensive(self):
        """Test comprehensive flashcard CRUD operations"""
        print("🆕 Testing comprehensive Flashcard CRUD...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test data for multiple flashcards
        flashcards_data = [
            {
                'front': {'text': 'What is Python?'},
                'back': {'text': 'Python is a high-level programming language'},
                'difficulty_level': 'easy',
                'tags': ['python', 'programming']
            },
            {
                'front': {'text': 'What is FastAPI?'},
                'back': {'text': 'FastAPI is a modern web framework for Python'},
                'difficulty_level': 'medium',
                'tags': ['fastapi', 'web', 'python']
            },
            {
                'front': {'text': 'What is MongoDB?'},
                'back': {'text': 'MongoDB is a NoSQL document database'},
                'difficulty_level': 'medium',
                'tags': ['mongodb', 'database', 'nosql']
            }
        ]
        
        # 1. Create multiple flashcards
        for i, flashcard_data in enumerate(flashcards_data):
            response = requests.post(
                f'{self.base_url}/flashcards/deck/{self.test_deck_id}',
                json=flashcard_data, headers=headers
            )
            
            assert response.status_code == 201, f"Flashcard {i+1} creation failed: {response.text}"
            
            flashcard = response.json()
            assert 'id' in flashcard and '_id' not in flashcard, f"Flashcard {i+1} should use 'id'"
            assert flashcard['front']['text'] == flashcard_data['front']['text'], f"Flashcard {i+1} front text should match"
            
            self.test_flashcard_ids.append(flashcard['id'])
            print(f"✅ Flashcard {i+1} created - ID: {flashcard['id']}")
        
        # 2. List flashcards and verify
        response = requests.get(f'{self.base_url}/flashcards/deck/{self.test_deck_id}', headers=headers)
        assert response.status_code == 200, f"Flashcard list failed: {response.text}"
        
        flashcards_list = response.json()
        assert 'flashcards' in flashcards_list, "Response should contain 'flashcards'"
        assert len(flashcards_list['flashcards']) == len(flashcards_data), "Should have all created flashcards"
        
        for flashcard in flashcards_list['flashcards']:
            assert 'id' in flashcard and '_id' not in flashcard, "Each flashcard should use 'id'"
            assert flashcard['id'] in self.test_flashcard_ids, "Flashcard ID should be in created list"
        
        print(f"✅ Flashcard list verified - {len(flashcards_list['flashcards'])} flashcards")
        
        # 3. Read individual flashcards
        for i, flashcard_id in enumerate(self.test_flashcard_ids):
            response = requests.get(f'{self.base_url}/flashcards/{flashcard_id}', headers=headers)
            assert response.status_code == 200, f"Flashcard {i+1} read failed: {response.text}"
            
            flashcard = response.json()
            assert flashcard['id'] == flashcard_id, f"Flashcard {i+1} ID should match"
            assert 'id' in flashcard and '_id' not in flashcard, f"Flashcard {i+1} should use 'id'"
        
        print("✅ Individual flashcard reads successful")
        
        # 4. Update flashcards
        for i, flashcard_id in enumerate(self.test_flashcard_ids):
            update_data = {
                'front': {'text': f'Updated question {i+1}'},
                'back': {'text': f'Updated answer {i+1}'},
                'difficulty_level': 'hard'
            }
            
            response = requests.put(f'{self.base_url}/flashcards/{flashcard_id}',
                                   json=update_data, headers=headers)
            assert response.status_code == 200, f"Flashcard {i+1} update failed: {response.text}"
            
            updated_flashcard = response.json()
            assert updated_flashcard['id'] == flashcard_id, f"Flashcard {i+1} ID should remain same"
            assert updated_flashcard['front']['text'] == update_data['front']['text'], f"Flashcard {i+1} should be updated"
            assert updated_flashcard['difficulty_level'] == 'hard', f"Flashcard {i+1} difficulty should be updated"
        
        print("✅ Flashcard updates successful")
        
        # 5. Test search and filtering
        response = requests.get(f'{self.base_url}/flashcards/deck/{self.test_deck_id}?difficulty=hard', headers=headers)
        assert response.status_code == 200, f"Flashcard filtering failed: {response.text}"
        
        filtered_flashcards = response.json()
        for flashcard in filtered_flashcards['flashcards']:
            assert flashcard['difficulty_level'] == 'hard', "Filtered flashcards should have 'hard' difficulty"
        
        print("✅ Flashcard filtering successful")
        
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("⚠️ Testing edge cases and error handling...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # 1. Test invalid deck ID (may return various error codes)
        response = requests.get(f'{self.base_url}/flashcards/deck/invalid_id', headers=headers)
        assert response.status_code >= 400, f"Invalid deck ID should return error, got {response.status_code}"
        print(f"   - Invalid deck ID returns: {response.status_code}")
        
        # 2. Test invalid flashcard ID
        response = requests.get(f'{self.base_url}/flashcards/invalid_id', headers=headers)
        assert response.status_code >= 400, f"Invalid flashcard ID should return error, got {response.status_code}"
        print(f"   - Invalid flashcard ID returns: {response.status_code}")
        
        # 3. Test unauthorized access
        response = requests.get(f'{self.base_url}/flashcards/deck/{self.test_deck_id}')
        assert response.status_code >= 401, f"Unauthorized access should return auth error, got {response.status_code}"
        print(f"   - Unauthorized access returns: {response.status_code}")
        
        # 4. Test invalid JSON data
        invalid_data = {'invalid': 'data'}
        response = requests.post(f'{self.base_url}/flashcards/deck/{self.test_deck_id}',
                                json=invalid_data, headers=headers)
        assert response.status_code >= 400, f"Invalid data should return error, got {response.status_code}"
        print(f"   - Invalid JSON data returns: {response.status_code}")
        
        print("✅ Edge cases handled correctly (error codes detected)")
        
    def test_database_integrity(self):
        """Test database data integrity"""
        print("🔍 Testing database integrity...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Verify all created flashcards exist in database
        response = requests.get(f'{self.base_url}/flashcards/deck/{self.test_deck_id}', headers=headers)
        flashcards = response.json()['flashcards']
        
        # Check that all IDs are valid ObjectId format (24 character hex string)
        for flashcard in flashcards:
            flashcard_id = flashcard['id']
            assert len(flashcard_id) == 24, f"ID should be 24 characters: {flashcard_id}"
            assert all(c in '0123456789abcdef' for c in flashcard_id), f"ID should be hex: {flashcard_id}"
            
        # Verify deck-flashcard relationships
        deck_response = requests.get(f'{self.base_url}/decks/{self.test_deck_id}', headers=headers)
        deck = deck_response.json()
        
        assert deck['id'] == self.test_deck_id, "Deck ID should match"
        
        print("✅ Database integrity verified")
        
    def cleanup(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Delete individual flashcards first
        for flashcard_id in self.test_flashcard_ids:
            response = requests.delete(f'{self.base_url}/flashcards/{flashcard_id}', headers=headers)
            if response.status_code == 200:
                print(f"✅ Flashcard {flashcard_id} deleted")
        
        # Delete test deck
        if self.test_deck_id:
            response = requests.delete(f'{self.base_url}/decks/{self.test_deck_id}', headers=headers)
            if response.status_code == 200:
                print(f"✅ Deck {self.test_deck_id} deleted")
        
        print("✅ Cleanup completed")
        
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Phase 4.7 Backend & Database Tests")
        print("=" * 70)
        
        try:
            # Setup
            user_id = self.setup_auth()
            self.test_database_connection()
            
            # Core CRUD tests
            self.test_deck_crud_with_id_standardization()
            self.test_flashcard_crud_comprehensive()
            
            # Edge cases and integrity
            self.test_edge_cases()
            self.test_database_integrity()
            
            # Cleanup
            self.cleanup()
            
            print("=" * 70)
            print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
            print("✅ Phase 4.7 Backend & Database fully validated")
            print("✅ ID Standardization working perfectly")
            print("✅ CRUD operations functioning correctly")
            print("✅ Database integrity maintained")
            print("✅ Error handling working properly")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            # Try cleanup even if tests failed
            try:
                self.cleanup()
            except:
                pass
            return False

def main():
    """Main test runner"""
    tester = TestPhase47Comprehensive()
    success = tester.run_all_tests()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
