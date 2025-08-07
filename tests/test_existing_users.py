"""
Test authentication với users đã có trong database
"""
import asyncio
import httpx
from app.config import settings

async def test_existing_users():
    """Test với users đã tồn tại trong database"""
    
    print("🧪 Testing Authentication with existing users")
    base_url = "http://localhost:8000"
    
    # Test user credentials
    users = [
        {"email": "admin@flashcard.com", "password": "admin123", "name": "Admin"},
        {"email": "test@example.com", "password": "test123", "name": "Test User"}
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        for user in users:
            print(f"\n🔑 Testing login for {user['name']}...")
            
            # Test login
            login_response = await client.post(
                f"{base_url}/api/v1/auth/login",
                json={"email": user["email"], "password": user["password"]}
            )
            
            print(f"  Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                print(f"  ✅ Login successful!")
                print(f"  User: {login_data['user']['email']}")
                print(f"  Role: {login_data['user']['role']}")
                
                access_token = login_data["access_token"]
                
                # Test get current user
                me_response = await client.get(
                    f"{base_url}/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    print(f"  ✅ Get me successful: {me_data['username']}")
                else:
                    print(f"  ❌ Get me failed: {me_response.status_code}")
                    print(f"     Error: {me_response.json()}")
                
            else:
                print(f"  ❌ Login failed: {login_response.status_code}")
                try:
                    error_data = login_response.json()
                    print(f"     Error: {error_data}")
                except:
                    print(f"     Error: {login_response.text}")

    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_existing_users())
