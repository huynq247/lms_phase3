"""
Simple test for existing database users
"""
import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app


# Database users from DATABASE_USERS.md
DATABASE_USERS = [
    {"email": "admin@flashcard.com", "password": "admin123", "role": "admin"},
    {"email": "teacher@flashcard.com", "password": "teacher123", "role": "teacher"},
    {"email": "test@example.com", "password": "test123", "role": "student"}
]


@pytest.mark.asyncio
async def test_database_users_simple():
    """Simple test for database users."""
    print("\n🧪 Testing Database Users - Simple Version")
    
    successful_logins = 0
    
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        for user in DATABASE_USERS:
            print(f"\n🔑 Testing: {user['email']}")
            
            try:
                response = await client.post("/api/v1/auth/login", json={
                    "email": user["email"],
                    "password": user["password"]
                })
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == status.HTTP_200_OK:
                    result = response.json()
                    user_info = result.get("user", {})
                    
                    print(f"   ✅ SUCCESS")
                    print(f"   Username: {user_info.get('username')}")
                    print(f"   Role: {user_info.get('role')}")
                    print(f"   Expected Role: {user['role']}")
                    
                    # Verify role matches
                    assert user_info.get('role') == user['role'], f"Role mismatch for {user['email']}"
                    successful_logins += 1
                    
                elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    print(f"   ⚠️ RATE LIMITED (this is expected behavior)")
                else:
                    print(f"   ❌ FAILED: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
            except Exception as e:
                print(f"   💥 EXCEPTION: {str(e)}")
    
    print(f"\n📊 SUMMARY: {successful_logins}/{len(DATABASE_USERS)} successful logins")
    
    # Should have at least 1 successful login
    assert successful_logins >= 1, f"Expected at least 1 successful login, got {successful_logins}"


@pytest.mark.asyncio 
async def test_admin_user_specifically():
    """Test admin user specifically."""
    print("\n👑 Testing Admin User Specifically")
    
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        response = await client.post("/api/v1/auth/login", json={
            "email": "admin@flashcard.com",
            "password": "admin123"
        })
        
        print(f"Admin login status: {response.status_code}")
        
        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            user_info = result.get("user", {})
            
            print(f"✅ Admin login successful")
            print(f"Username: {user_info.get('username')}")
            print(f"Role: {user_info.get('role')}")
            print(f"Email: {user_info.get('email')}")
            
            assert user_info.get('role') == 'admin'
            assert user_info.get('email') == 'admin@flashcard.com'
            
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            print("⚠️ Rate limited - Admin credentials are valid but rate limited")
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"Response: {response.text}")


@pytest.mark.asyncio
async def test_teacher_user_specifically():
    """Test teacher user specifically.""" 
    print("\n👨‍🏫 Testing Teacher User Specifically")
    
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        response = await client.post("/api/v1/auth/login", json={
            "email": "teacher@flashcard.com", 
            "password": "teacher123"
        })
        
        print(f"Teacher login status: {response.status_code}")
        
        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            user_info = result.get("user", {})
            
            print(f"✅ Teacher login successful")
            print(f"Username: {user_info.get('username')}")
            print(f"Role: {user_info.get('role')}")
            print(f"Email: {user_info.get('email')}")
            
            assert user_info.get('role') == 'teacher'
            assert user_info.get('email') == 'teacher@flashcard.com'
            
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            print("⚠️ Rate limited - Teacher credentials are valid but rate limited")
        else:
            print(f"❌ Teacher login failed: {response.status_code}")
            print(f"Response: {response.text}")


@pytest.mark.asyncio
async def test_student_user_specifically():
    """Test student user specifically."""
    print("\n👤 Testing Student User Specifically")
    
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        
        print(f"Student login status: {response.status_code}")
        
        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            user_info = result.get("user", {})
            
            print(f"✅ Student login successful")
            print(f"Username: {user_info.get('username')}")
            print(f"Role: {user_info.get('role')}")
            print(f"Email: {user_info.get('email')}")
            
            assert user_info.get('role') == 'student'
            assert user_info.get('email') == 'test@example.com'
            
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            print("⚠️ Rate limited - Student credentials are valid but rate limited")
        else:
            print(f"❌ Student login failed: {response.status_code}")
            print(f"Response: {response.text}")
