"""
Test login đơn giản cho tất cả 3 roles
"""
import asyncio
import httpx
from app.config import settings

async def test_roles_login_only():
    """Test login cho tất cả 3 roles"""
    
    print("🧪 TESTING LOGIN FOR ALL 3 ROLES")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test users for each role
    test_users = [
        {
            "role": "👑 ADMIN",
            "email": "admin@flashcard.com",
            "password": "admin123"
        },
        {
            "role": "👨‍🏫 TEACHER", 
            "email": "teacher@flashcard.com",
            "password": "teacher123"
        },
        {
            "role": "👤 STUDENT",
            "email": "test@example.com", 
            "password": "test123"
        }
    ]
    
    successful_logins = []
    failed_logins = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        for user in test_users:
            print(f"\n{user['role']} LOGIN TEST")
            print("-" * 30)
            
            try:
                # Test login
                login_response = await client.post(
                    f"{base_url}/api/v1/auth/login",
                    json={"email": user["email"], "password": user["password"]}
                )
                
                print(f"Status: {login_response.status_code}")
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    print(f"✅ SUCCESS!")
                    print(f"Username: {login_data['user']['username']}")
                    print(f"Role: {login_data['user']['role']}")
                    print(f"Email: {login_data['user']['email']}")
                    
                    successful_logins.append({
                        "role": user["role"],
                        "user": login_data["user"]
                    })
                else:
                    print(f"❌ FAILED!")
                    try:
                        error = login_response.json()
                        print(f"Error: {error}")
                    except:
                        print(f"Error: {login_response.text}")
                    
                    failed_logins.append({
                        "role": user["role"],
                        "status": login_response.status_code
                    })
                    
            except Exception as e:
                print(f"❌ EXCEPTION: {e}")
                failed_logins.append({
                    "role": user["role"],
                    "error": str(e)
                })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 LOGIN TEST SUMMARY")
    print("=" * 50)
    
    print(f"✅ Successful: {len(successful_logins)}/3 roles")
    print(f"❌ Failed: {len(failed_logins)}/3 roles")
    
    if successful_logins:
        print("\n✅ SUCCESSFUL LOGINS:")
        for login in successful_logins:
            print(f"  {login['role']}: {login['user']['username']} ({login['user']['email']})")
    
    if failed_logins:
        print("\n❌ FAILED LOGINS:")
        for fail in failed_logins:
            print(f"  {fail['role']}: {fail.get('status', fail.get('error', 'Unknown'))}")
    
    if len(successful_logins) == 3:
        print("\n🎉 ALL 3 ROLES LOGIN WORKING!")
        print("\n📋 WORKING CREDENTIALS:")
        print("👑 Admin: admin@flashcard.com / admin123")
        print("👨‍🏫 Teacher: teacher@flashcard.com / teacher123") 
        print("👤 Student: test@example.com / test123")
    else:
        print(f"\n⚠️ Only {len(successful_logins)}/3 roles working")

if __name__ == "__main__":
    asyncio.run(test_roles_login_only())
