"""
Test authentication với tất cả 3 roles: Admin, Teacher, Student
"""
import asyncio
import httpx
from app.config import settings

async def test_all_roles():
    """Test authentication với tất cả 3 roles"""
    
    print("🧪 TESTING AUTHENTICATION WITH ALL ROLES")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test users for each role
    test_users = [
        {
            "role": "ADMIN",
            "email": "admin@flashcard.com",
            "password": "admin123",
            "icon": "👑"
        },
        {
            "role": "TEACHER", 
            "email": "teacher@flashcard.com",
            "password": "teacher123",
            "icon": "👨‍🏫"
        },
        {
            "role": "STUDENT",
            "email": "test@example.com", 
            "password": "test123",
            "icon": "👤"
        }
    ]
    
    successful_logins = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        for user in test_users:
            print(f"\n{user['icon']} TESTING {user['role']} ROLE")
            print("-" * 40)
            
            # Test login
            print(f"🔑 Logging in as {user['role']}...")
            login_response = await client.post(
                f"{base_url}/api/v1/auth/login",
                json={"email": user["email"], "password": user["password"]}
            )
            
            print(f"  Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                print(f"  ✅ Login successful!")
                print(f"  User: {login_data['user']['username']}")
                print(f"  Email: {login_data['user']['email']}")
                print(f"  Role: {login_data['user']['role']}")
                
                access_token = login_data["access_token"]
                successful_logins.append({
                    "role": user["role"],
                    "token": access_token,
                    "user_data": login_data["user"]
                })
                
                # Test get current user
                print(f"👤 Testing get current user...")
                me_response = await client.get(
                    f"{base_url}/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    print(f"  ✅ Get me successful!")
                    print(f"  Full Name: {me_data.get('first_name', 'N/A')} {me_data.get('last_name', 'N/A')}")
                    print(f"  Active: {me_data['is_active']}")
                    print(f"  Verified: {me_data['is_verified']}")
                else:
                    print(f"  ❌ Get me failed: {me_response.status_code}")
                
                # Test logout
                print(f"🚪 Testing logout...")
                logout_response = await client.post(
                    f"{base_url}/api/v1/auth/logout",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if logout_response.status_code == 200:
                    print(f"  ✅ Logout successful!")
                else:
                    print(f"  ❌ Logout failed: {logout_response.status_code}")
                
            else:
                print(f"  ❌ Login failed: {login_response.status_code}")
                try:
                    error_data = login_response.json()
                    print(f"     Error: {error_data}")
                except:
                    print(f"     Error: {login_response.text}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print(f"✅ Successful logins: {len(successful_logins)}/3")
    
    for login in successful_logins:
        role_icon = {"ADMIN": "👑", "TEACHER": "👨‍🏫", "STUDENT": "👤"}
        print(f"  {role_icon[login['role']]} {login['role']}: {login['user_data']['username']} ({login['user_data']['email']})")
    
    if len(successful_logins) == 3:
        print("\n🎉 ALL ROLES AUTHENTICATION WORKING PERFECTLY!")
        print("\n📋 CREDENTIALS FOR REFERENCE:")
        print("👑 Admin: admin@flashcard.com / admin123")
        print("👨‍🏫 Teacher: teacher@flashcard.com / teacher123") 
        print("👤 Student: test@example.com / test123")
    else:
        print(f"\n⚠️  Only {len(successful_logins)}/3 roles working correctly")
    
    print("\n🔚 Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_all_roles())
