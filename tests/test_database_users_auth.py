"""
Test authentication với tất cả users có sẵn trong database
Sử dụng thông tin từ DATABASE_USERS.md
"""
import pytest
import httpx

# Base URL cho testing
BASE_URL = "http://localhost:8000"

# Database users từ DATABASE_USERS.md
DATABASE_USERS = [
    {
        "role": "admin",
        "email": "admin@flashcard.com", 
        "password": "admin123",
        "username": "admin",
        "full_name": "System Administrator"
    },
    {
        "role": "teacher",
        "email": "teacher@flashcard.com",
        "password": "teacher123", 
        "username": "teacher_user",
        "full_name": "Teacher User"
    },
    {
        "role": "student",
        "email": "test@example.com",
        "password": "test123",
        "username": "testuser", 
        "full_name": "Test User"
    }
]

@pytest.mark.asyncio
async def test_all_database_users_login():
    """Test login for all users in database"""
    
    results = []
    
    for user in DATABASE_USERS:
        print(f"\n🧪 Testing {user['role'].upper()}: {user['email']}")
        
        # Test login
        login_data = {
            "email": user["email"],
            "password": user["password"]
        }
        
        async with httpx.AsyncClient() as client:
            # Login
            login_response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data
            )
            
            print(f"   Login Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                login_data_response = login_response.json()
                access_token = login_data_response["access_token"]
                
                # Get user info
                me_response = await client.get(
                    f"{BASE_URL}/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                print(f"   Get Me Status: {me_response.status_code}")
                
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    print(f"   ✅ Role: {user_info['role']}, Username: {user_info['username']}")
                    
                    # Verify role matches
                    assert user_info["role"] == user["role"]
                    assert user_info["email"] == user["email"]
                    assert user_info["username"] == user["username"]
                    
                    results.append({
                        "role": user["role"],
                        "email": user["email"],
                        "status": "✅ SUCCESS"
                    })
                    
                    # Test logout (optional - may timeout)
                    try:
                        logout_response = await client.post(
                            f"{BASE_URL}/api/v1/auth/logout",
                            headers={"Authorization": f"Bearer {access_token}"},
                            timeout=5.0
                        )
                        print(f"   Logout Status: {logout_response.status_code}")
                    except Exception as e:
                        print(f"   Logout: ⚠️  Network timeout (expected)")
                    
                else:
                    results.append({
                        "role": user["role"],
                        "email": user["email"], 
                        "status": "❌ GET ME FAILED"
                    })
            else:
                results.append({
                    "role": user["role"],
                    "email": user["email"],
                    "status": "❌ LOGIN FAILED"
                })
    
    # Print summary
    print(f"\n📊 AUTHENTICATION TEST SUMMARY:")
    for result in results:
        print(f"   {result['role'].upper()}: {result['email']} - {result['status']}")
    
    # Assert all successful
    successful_logins = [r for r in results if "SUCCESS" in r["status"]]
    assert len(successful_logins) == 3, f"Expected 3 successful logins, got {len(successful_logins)}"

@pytest.mark.asyncio 
async def test_role_permissions_basic():
    """Test basic role permissions (không cần implement permission system hoàn chỉnh)"""
    
    print(f"\n🔐 Testing basic role access...")
    
    for user in DATABASE_USERS:
        login_data = {
            "email": user["email"],
            "password": user["password"]
        }
        
        async with httpx.AsyncClient() as client:
            # Login
            login_response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data
            )
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                access_token = token_data["access_token"]
                
                # Test token verification
                verify_response = await client.get(
                    f"{BASE_URL}/api/v1/auth/verify",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                print(f"   {user['role'].upper()} token verify: {verify_response.status_code}")
                assert verify_response.status_code == 200
                
                verify_data = verify_response.json()
                assert verify_data["valid"] == True
                assert verify_data["role"] == user["role"]
                
                print(f"   ✅ {user['role'].upper()} role verification successful")

if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        await test_all_database_users_login()
        await test_role_permissions_basic()
        print("\n🎉 All database user tests passed!")
    
    asyncio.run(run_tests())
