"""
Simple authentication endpoint testing
"""
import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def test_auth_flow():
    """Test complete authentication flow"""
    # Setup database
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    users_collection = database.users
    
    print("🔗 Connected to database")
    
    # Test data
    user_data = {
        "username": "test_simple_auth",
        "email": "simple.auth@example.com",
        "password": "StrongPass123!",
        "full_name": "Simple Test User"
    }
    
    # Clean up trước khi test
    await users_collection.delete_one({"email": user_data["email"]})
    print("🧹 Cleaned up test data")
    
    # Base URL
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient() as http_client:
            
            # 1. Test register
            print("\n🔐 Testing Register...")
            register_response = await http_client.post(
                f"{base_url}/api/v1/auth/register",
                json=user_data,
                timeout=30.0
            )
            print(f"Register Status: {register_response.status_code}")
            print(f"Register Response: {register_response.json()}")
            
            if register_response.status_code != 201:
                print("❌ Register failed!")
                return
            
            # 2. Test login
            print("\n🔑 Testing Login...")
            login_data = {
                "username": user_data["username"],  # Dùng username thay vì email
                "password": user_data["password"]
            }
            login_response = await http_client.post(
                f"{base_url}/api/v1/auth/login",
                json=login_data,
                timeout=30.0
            )
            print(f"Login Status: {login_response.status_code}")
            
            try:
                login_response_data = login_response.json()
                print(f"Login Response: {login_response_data}")
            except Exception as e:
                print(f"Login Response Text: {login_response.text}")
                print(f"JSON Error: {e}")
            
            if login_response.status_code != 200:
                print("❌ Login failed!")
                return
                
            login_data = login_response.json()
            access_token = login_data["access_token"]
            
            # 3. Test get current user
            print("\n👤 Testing Get Current User...")
            me_response = await http_client.get(
                f"{base_url}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0
            )
            print(f"Get Me Status: {me_response.status_code}")
            print(f"Get Me Response: {me_response.json()}")
            
            if me_response.status_code != 200:
                print("❌ Get current user failed!")
                return
                
            # 4. Test logout
            print("\n🚪 Testing Logout...")
            logout_response = await http_client.post(
                f"{base_url}/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0
            )
            print(f"Logout Status: {logout_response.status_code}")
            print(f"Logout Response: {logout_response.json()}")
            
            # 5. Test access after logout (should fail)
            print("\n🚫 Testing Access After Logout...")
            after_logout_response = await http_client.get(
                f"{base_url}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0
            )
            print(f"After Logout Status: {after_logout_response.status_code}")
            print(f"After Logout Response: {after_logout_response.json()}")
            
            if after_logout_response.status_code == 401:
                print("✅ All authentication tests passed!")
            else:
                print("❌ Token should be invalid after logout!")
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        # Cleanup
        await users_collection.delete_one({"email": user_data["email"]})
        client.close()
        print("🧹 Cleaned up and disconnected")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
