"""
Test cases for admin management APIs.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAdminUserManagement:
    """Test admin user management endpoints."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Login with admin user from database
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@flashcard.com", "password": "admin123"}
        )
        assert login_response.status_code == 200
        self.access_token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    def test_get_users_success(self):
        """Test getting user list successfully."""
        response = client.get("/api/v1/admin/users", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "users" in data
        assert "total_count" in data
        assert "page" in data
        assert "limit" in data
        assert "total_pages" in data
        assert "has_next" in data
        assert "has_prev" in data
        
        # Check pagination defaults
        assert data["page"] == 1
        assert data["limit"] == 10
        
        # Should have at least admin, teacher, student users
        assert data["total_count"] >= 3
        assert len(data["users"]) >= 3
        
        # Check user structure
        user = data["users"][0]
        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "role" in user
        assert "is_active" in user
        assert "password_hash" not in user  # Should be filtered out
    
    def test_get_users_with_filters(self):
        """Test user list with search and role filters."""
        # Test search filter
        response = client.get(
            "/api/v1/admin/users?search=admin",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should find admin user
        assert any("admin" in user["username"].lower() or 
                  "admin" in user["email"].lower() 
                  for user in data["users"])
        
        # Test role filter
        response = client.get(
            "/api/v1/admin/users?role=admin",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        # All returned users should be admin role
        assert all(user["role"] == "admin" for user in data["users"])
        
        # Test active filter
        response = client.get(
            "/api/v1/admin/users?is_active=true",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        # All returned users should be active
        assert all(user["is_active"] is True for user in data["users"])
    
    def test_get_users_pagination(self):
        """Test user list pagination."""
        # Test with page 1, limit 2
        response = client.get(
            "/api/v1/admin/users?page=1&limit=2",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["limit"] == 2
        assert len(data["users"]) <= 2
        
        if data["total_count"] > 2:
            assert data["has_next"] is True
        assert data["has_prev"] is False
    
    def test_create_user_success(self):
        """Test creating a new user successfully."""
        new_user_data = {
            "username": "test_admin_created",
            "email": "test_admin@example.com",
            "password": "SecurePass123!",
            "role": "student",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True
        }
        
        response = client.post(
            "/api/v1/admin/users",
            json=new_user_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check created user data
        assert data["username"] == "test_admin_created"
        assert data["email"] == "test_admin@example.com"
        assert data["role"] == "student"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "created_by" in data
        
        # Verify user was actually created by trying to get the user list
        users_response = client.get("/api/v1/admin/users", headers=self.headers)
        users_data = users_response.json()
        created_user_exists = any(
            user["username"] == "test_admin_created" 
            for user in users_data["users"]
        )
        assert created_user_exists
    
    def test_create_user_duplicate_email(self):
        """Test creating user with duplicate email fails."""
        # Try to create user with admin email
        duplicate_user_data = {
            "username": "duplicate_test",
            "email": "admin@flashcard.com",  # Already exists
            "password": "SecurePass123!",
            "role": "student"
        }
        
        response = client.post(
            "/api/v1/admin/users",
            json=duplicate_user_data,
            headers=self.headers
        )
        
        assert response.status_code == 400
    
    def test_reset_user_password_success(self):
        """Test resetting user password successfully."""
        # First get a user ID (use student user)
        users_response = client.get("/api/v1/admin/users", headers=self.headers)
        users_data = users_response.json()
        
        student_user = next(
            user for user in users_data["users"] 
            if user["role"] == "student"
        )
        
        reset_data = {
            "new_password": "NewSecurePass123!",
            "reason": "Admin test password reset"
        }
        
        response = client.put(
            f"/api/v1/admin/users/{student_user['id']}/reset-password",
            json=reset_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == student_user["id"]
        assert data["username"] == student_user["username"]
        assert data["reason"] == "Admin test password reset"
        assert "reset_at" in data
        assert "reset_by" in data
    
    def test_update_user_role_success(self):
        """Test updating user role successfully."""
        # First get a student user
        users_response = client.get("/api/v1/admin/users", headers=self.headers)
        users_data = users_response.json()
        
        student_user = next(
            user for user in users_data["users"] 
            if user["role"] == "student"
        )
        
        role_data = {
            "role": "teacher",
            "reason": "Promoting student to teacher for testing"
        }
        
        response = client.put(
            f"/api/v1/admin/users/{student_user['id']}/role",
            json=role_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == student_user["id"]
        assert data["role"] == "teacher"
        
        # Change back to student
        role_data["role"] = "student"
        role_data["reason"] = "Changing back to student after test"
        
        response = client.put(
            f"/api/v1/admin/users/{student_user['id']}/role",
            json=role_data,
            headers=self.headers
        )
        assert response.status_code == 200
    
    def test_deactivate_user_success(self):
        """Test deactivating user successfully."""
        # First create a test user to deactivate
        new_user_data = {
            "username": "test_deactivate_user",
            "email": "test_deactivate@example.com",
            "password": "SecurePass123!",
            "role": "student"
        }
        
        create_response = client.post(
            "/api/v1/admin/users",
            json=new_user_data,
            headers=self.headers
        )
        created_user = create_response.json()
        
        # Now deactivate the user
        response = client.delete(
            f"/api/v1/admin/users/{created_user['id']}?reason=Test deactivation",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "User deactivated successfully"
        assert data["user_id"] == created_user["id"]
        assert data["reason"] == "Test deactivation"
    
    def test_admin_operations_unauthorized(self):
        """Test admin operations without proper authorization."""
        # Test with teacher user
        teacher_login = client.post(
            "/api/v1/auth/login",
            json={"email": "teacher@flashcard.com", "password": "teacher123"}
        )
        teacher_token = teacher_login.json()["access_token"]
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # Test all admin endpoints with teacher token
        endpoints = [
            ("GET", "/api/v1/admin/users"),
            ("POST", "/api/v1/admin/users", {
                "username": "test", "email": "test@test.com", 
                "password": "test123", "role": "student"
            })
        ]
        
        for method, endpoint, *body in endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=teacher_headers)
            else:
                response = client.post(endpoint, json=body[0], headers=teacher_headers)
            
            assert response.status_code == 403, f"Failed for {method} {endpoint}"
    
    def test_invalid_user_id_format(self):
        """Test operations with invalid user ID format."""
        invalid_id = "invalid_id_format"
        
        # Test password reset with invalid ID
        response = client.put(
            f"/api/v1/admin/users/{invalid_id}/reset-password",
            json={"new_password": "NewPass123!"},
            headers=self.headers
        )
        assert response.status_code == 400
        
        # Test role update with invalid ID
        response = client.put(
            f"/api/v1/admin/users/{invalid_id}/role",
            json={"role": "teacher"},
            headers=self.headers
        )
        assert response.status_code == 400
        
        # Test deactivate with invalid ID
        response = client.delete(
            f"/api/v1/admin/users/{invalid_id}",
            headers=self.headers
        )
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
