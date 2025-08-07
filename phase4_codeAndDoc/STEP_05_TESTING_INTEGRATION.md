# 🧪 STEP 5: TESTING & INTEGRATION
*Comprehensive API testing and system integration*

## 🎯 OBJECTIVES
- Comprehensive testing of all Phase 4 components
- Integration testing between components
- Performance testing and optimization
- API documentation generation
- Deployment preparation

## 📋 IMPLEMENTATION CHECKLIST

### **A. Unit Testing Complete** ⏳
- [ ] User management tests
- [ ] Deck management tests
- [ ] Flashcard management tests
- [ ] File upload tests
- [ ] Service layer tests

### **B. Integration Testing** ⏳
- [ ] End-to-end workflow tests
- [ ] Cross-component integration tests
- [ ] Authentication integration tests
- [ ] Database integration tests
- [ ] File system integration tests

### **C. API Testing** ⏳
- [ ] Complete API endpoint testing
- [ ] Error handling validation
- [ ] Permission and authorization tests
- [ ] Input validation tests
- [ ] Response format validation

### **D. Performance Testing** ⏳
- [ ] Load testing for critical endpoints
- [ ] Database query optimization
- [ ] File upload performance testing
- [ ] Response time optimization
- [ ] Memory usage optimization

### **E. Documentation & Deployment** ⏳
- [ ] API documentation generation
- [ ] Postman collection update
- [ ] Deployment scripts
- [ ] Environment configuration
- [ ] Health check endpoints

## 🏗️ TESTING IMPLEMENTATION

### **1. Integration Test Suite**
```python
# tests/test_integration_phase4.py - New file
import pytest
from httpx import AsyncClient

class TestPhase4Integration:
    """Integration tests for Phase 4 components"""
    
    async def test_complete_deck_workflow(self, client: AsyncClient, auth_headers):
        """Test complete deck creation and management workflow"""
        # 1. Create deck
        deck_data = {
            "title": "Test Integration Deck",
            "description": "Integration test deck",
            "category": "Test",
            "privacy": "private"
        }
        response = await client.post("/api/v1/decks", json=deck_data, headers=auth_headers)
        assert response.status_code == 201
        deck = response.json()
        deck_id = deck["id"]
        
        # 2. Upload image for flashcard
        with open("tests/fixtures/test_image.jpg", "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response = await client.post("/api/v1/upload/image", files=files, headers=auth_headers)
        assert response.status_code == 201
        image_upload = response.json()
        
        # 3. Create flashcard with uploaded image
        flashcard_data = {
            "front_content": [
                {"type": "plain_text", "content": "What is this image?"}
            ],
            "back_content": [
                {"type": "image_url", "content": image_upload["file_url"]},
                {"type": "plain_text", "content": "Test image description"}
            ],
            "flashcard_type": "mixed"
        }
        response = await client.post(f"/api/v1/decks/{deck_id}/flashcards", json=flashcard_data, headers=auth_headers)
        assert response.status_code == 201
        flashcard = response.json()
        
        # 4. Update deck privacy to public
        update_data = {"privacy": "public"}
        response = await client.put(f"/api/v1/decks/{deck_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        # 5. Verify deck appears in public listings
        response = await client.get("/api/v1/decks/public")
        assert response.status_code == 200
        public_decks = response.json()
        assert any(d["id"] == deck_id for d in public_decks["items"])
        
        # 6. Clone the deck as different user
        response = await client.post(f"/api/v1/decks/{deck_id}/clone", headers=auth_headers)
        assert response.status_code == 201
        cloned_deck = response.json()
        assert cloned_deck["title"] == f"Copy of {deck['title']}"
        
        # 7. Cleanup
        await client.delete(f"/api/v1/decks/{deck_id}", headers=auth_headers)
        await client.delete(f"/api/v1/decks/{cloned_deck['id']}", headers=auth_headers)
        await client.delete(f"/api/v1/files/{image_upload['id']}", headers=auth_headers)
    
    async def test_permission_inheritance(self, client: AsyncClient, auth_headers_teacher, auth_headers_student):
        """Test permission inheritance from deck to flashcards"""
        # Teacher creates private deck
        deck_data = {"title": "Private Teacher Deck", "privacy": "private"}
        response = await client.post("/api/v1/decks", json=deck_data, headers=auth_headers_teacher)
        deck = response.json()
        deck_id = deck["id"]
        
        # Teacher creates flashcard
        flashcard_data = {
            "front_content": [{"type": "plain_text", "content": "Teacher question"}],
            "back_content": [{"type": "plain_text", "content": "Teacher answer"}]
        }
        response = await client.post(f"/api/v1/decks/{deck_id}/flashcards", json=flashcard_data, headers=auth_headers_teacher)
        flashcard = response.json()
        flashcard_id = flashcard["id"]
        
        # Student should NOT be able to access flashcard
        response = await client.get(f"/api/v1/flashcards/{flashcard_id}", headers=auth_headers_student)
        assert response.status_code == 403
        
        # Teacher shares deck with student
        share_data = {"user_emails": ["student@test.com"]}
        response = await client.post(f"/api/v1/decks/{deck_id}/share", json=share_data, headers=auth_headers_teacher)
        assert response.status_code == 200
        
        # Now student should be able to access flashcard
        response = await client.get(f"/api/v1/flashcards/{flashcard_id}", headers=auth_headers_student)
        assert response.status_code == 200
        
        # But student should NOT be able to edit flashcard
        update_data = {"front_content": [{"type": "plain_text", "content": "Modified question"}]}
        response = await client.put(f"/api/v1/flashcards/{flashcard_id}", json=update_data, headers=auth_headers_student)
        assert response.status_code == 403
```

### **2. Performance Test Suite**
```python
# tests/test_performance_phase4.py - New file
import asyncio
import time
import pytest
from httpx import AsyncClient

class TestPhase4Performance:
    """Performance tests for Phase 4 endpoints"""
    
    async def test_deck_listing_performance(self, client: AsyncClient, auth_headers):
        """Test deck listing performance with large datasets"""
        # Create multiple decks for testing
        deck_ids = []
        for i in range(50):
            deck_data = {"title": f"Performance Test Deck {i}", "privacy": "public"}
            response = await client.post("/api/v1/decks", json=deck_data, headers=auth_headers)
            deck_ids.append(response.json()["id"])
        
        # Test public deck listing performance
        start_time = time.time()
        response = await client.get("/api/v1/decks/public?limit=20")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should complete within 1 second
        
        # Cleanup
        for deck_id in deck_ids:
            await client.delete(f"/api/v1/decks/{deck_id}", headers=auth_headers)
    
    async def test_bulk_flashcard_creation_performance(self, client: AsyncClient, auth_headers):
        """Test bulk flashcard creation performance"""
        # Create deck
        deck_data = {"title": "Bulk Test Deck"}
        response = await client.post("/api/v1/decks", json=deck_data, headers=auth_headers)
        deck_id = response.json()["id"]
        
        # Prepare bulk flashcard data
        flashcards = []
        for i in range(100):
            flashcards.append({
                "front_content": [{"type": "plain_text", "content": f"Question {i}"}],
                "back_content": [{"type": "plain_text", "content": f"Answer {i}"}]
            })
        
        bulk_data = {"flashcards": flashcards}
        
        # Test bulk creation performance
        start_time = time.time()
        response = await client.post(f"/api/v1/decks/{deck_id}/flashcards/bulk", json=bulk_data, headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == 201
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds
        
        # Cleanup
        await client.delete(f"/api/v1/decks/{deck_id}", headers=auth_headers)
    
    async def test_concurrent_file_uploads(self, client: AsyncClient, auth_headers):
        """Test concurrent file upload performance"""
        async def upload_file(client, auth_headers, file_content):
            files = {"file": ("test.jpg", file_content, "image/jpeg")}
            return await client.post("/api/v1/upload/image", files=files, headers=auth_headers)
        
        # Prepare test file content
        test_image_content = b"fake_image_content_for_testing" * 100
        
        # Test concurrent uploads
        start_time = time.time()
        tasks = [upload_file(client, auth_headers, test_image_content) for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All uploads should succeed
        for response in responses:
            assert response.status_code == 201
        
        assert (end_time - start_time) < 10.0  # Should complete within 10 seconds
        
        # Cleanup uploaded files
        for response in responses:
            file_id = response.json()["id"]
            await client.delete(f"/api/v1/files/{file_id}", headers=auth_headers)
```

### **3. API Documentation Generation**
```python
# scripts/generate_api_docs.py - New file
import json
from fastapi.openapi.utils import get_openapi
from app.main import app

def generate_openapi_schema():
    """Generate OpenAPI schema for API documentation"""
    openapi_schema = get_openapi(
        title="LMS Phase 4 API",
        version="1.0.0",
        description="Learning Management System API - Phase 4 Core Endpoints",
        routes=app.routes,
    )
    
    # Save schema to file
    with open("docs/openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print("API documentation generated: docs/openapi.json")

if __name__ == "__main__":
    generate_openapi_schema()
```

### **4. Health Check Endpoints**
```python
# app/routers/v1/health.py - New file
from fastapi import APIRouter, Depends
from app.utils.database import get_database

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "lms-api", "version": "1.0.0"}

@router.get("/detailed")
async def detailed_health_check(db = Depends(get_database)):
    """Detailed health check including database connectivity"""
    try:
        # Test database connection
        await db.command("ping")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "lms-api",
        "version": "1.0.0",
        "components": {
            "database": db_status,
            "file_storage": "healthy"  # Add actual file storage check
        }
    }
```

### **5. Test Configuration**
```python
# tests/conftest.py - Update existing file
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def test_db():
    """Test database fixture"""
    # Setup test database
    from app.utils.database import get_database
    db = await get_database()
    
    # Create test collections
    await db.create_collection("test_users")
    await db.create_collection("test_decks")
    await db.create_collection("test_flashcards")
    await db.create_collection("test_files")
    
    yield db
    
    # Cleanup test data
    await db.drop_collection("test_users")
    await db.drop_collection("test_decks")
    await db.drop_collection("test_flashcards")
    await db.drop_collection("test_files")

@pytest.fixture
async def auth_headers_teacher(client: AsyncClient):
    """Teacher authentication headers"""
    login_data = {"email": "teacher@test.com", "password": "password123"}
    response = await client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def auth_headers_student(client: AsyncClient):
    """Student authentication headers"""
    login_data = {"email": "student@test.com", "password": "password123"}
    response = await client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def auth_headers_admin(client: AsyncClient):
    """Admin authentication headers"""
    login_data = {"email": "admin@test.com", "password": "password123"}
    response = await client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## 🧪 TESTING EXECUTION PLAN

### **1. Run All Tests**
```bash
# Run all Phase 4 tests
pytest tests/test_*_phase4.py -v

# Run integration tests
pytest tests/test_integration_phase4.py -v

# Run performance tests
pytest tests/test_performance_phase4.py -v

# Generate coverage report
pytest --cov=app --cov-report=html
```

### **2. Load Testing with Locust**
```python
# tests/load_test.py - New file
from locust import HttpUser, task, between

class LMSUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before running tasks"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(3)
    def view_decks(self):
        """Simulate viewing deck list"""
        self.client.get("/api/v1/decks")
    
    @task(2)
    def view_public_decks(self):
        """Simulate browsing public decks"""
        self.client.get("/api/v1/decks/public")
    
    @task(1)
    def create_deck(self):
        """Simulate creating a deck"""
        self.client.post("/api/v1/decks", json={
            "title": "Load Test Deck",
            "description": "Created during load testing"
        })
```

## 📊 SUCCESS METRICS

### **Testing Coverage Goals**
- [ ] Unit test coverage > 90%
- [ ] Integration test coverage > 80%
- [ ] All critical paths tested
- [ ] Error scenarios covered

### **Performance Goals**
- [ ] API response time < 200ms (95th percentile)
- [ ] File upload < 5s for 10MB files
- [ ] Database queries optimized
- [ ] Memory usage stable under load

### **Quality Goals**
- [ ] Zero critical security vulnerabilities
- [ ] API documentation complete
- [ ] Error messages user-friendly
- [ ] Logging comprehensive

## 📝 FILES TO CREATE/UPDATE

### **New Files**
- `tests/test_integration_phase4.py` - Integration tests
- `tests/test_performance_phase4.py` - Performance tests
- `tests/load_test.py` - Load testing with Locust
- `scripts/generate_api_docs.py` - Documentation generator
- `app/routers/v1/health.py` - Health check endpoints
- `docs/api_testing_guide.md` - Testing guide

### **Updated Files**
- `tests/conftest.py` - Additional test fixtures
- `app/main.py` - Include health router
- `requirements.txt` - Add testing dependencies

### **Dependencies to Add**
```txt
pytest-asyncio==0.21.1
pytest-cov==4.1.0
locust==2.17.0
faker==19.12.0
```

## ⏱️ ESTIMATED TIMELINE
**Total**: 1 day (8 hours)
- Integration tests: 3 hours
- Performance tests: 2 hours
- Documentation: 2 hours
- Load testing setup: 1 hour

## ✅ COMPLETION CRITERIA
- [ ] All unit tests passing (>90% coverage)
- [ ] All integration tests passing
- [ ] Performance benchmarks met
- [ ] API documentation generated
- [ ] Health check endpoints working
- [ ] Load testing configuration ready

---

## 🎉 PHASE 4 COMPLETION
After completing Step 5, **Phase 4 is complete!**

### **Phase 4 Deliverables**
✅ User Management APIs  
✅ Deck Management APIs  
✅ Flashcard APIs  
✅ Multimedia Upload Support  
✅ Comprehensive Testing Suite  

**Ready for Phase 5: Study System & Spaced Repetition**

*Congratulations on completing Phase 4!*
