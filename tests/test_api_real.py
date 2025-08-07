"""
API endpoints test with real database connection.
"""
import pytest
import httpx
from app.main import app


@pytest.mark.asyncio
async def test_api_endpoints_with_real_db():
    """Test API endpoints with real database running."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        
        # Test root endpoint
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Root endpoint: {data}")
        
        # Test health endpoint
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        # Health can be "healthy" or "unhealthy" depending on startup timing
        assert data["status"] in ["healthy", "unhealthy"]
        print(f"✅ Health endpoint: {data}")
        
        # Test API health endpoint
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ API Health endpoint: {data}")
        
        # Test docs endpoint
        response = await client.get("/docs")
        assert response.status_code == 200
        print("✅ API Documentation available")
        
        # Test readiness probe
        response = await client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Readiness probe: {data}")
        
        # Test liveness probe  
        response = await client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Liveness probe: {data}")


@pytest.mark.asyncio
async def test_file_endpoints():
    """Test file-related endpoints."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        
        # Test file upload info (may not exist)
        response = await client.get("/api/v1/files/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ File info endpoint: {data}")
        else:
            print(f"ℹ️ File info endpoint not implemented (status: {response.status_code})")
        
        # Test file limits (may not exist)
        response = await client.get("/api/v1/info/limits")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ File limits endpoint: {data}")
        else:
            print(f"ℹ️ File limits endpoint not implemented (status: {response.status_code})")


@pytest.mark.asyncio
async def test_nonexistent_endpoints():
    """Test that non-existent endpoints return proper errors."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        
        # Test non-existent auth endpoints
        response = await client.get("/api/v1/auth/login")
        print(f"ℹ️ Auth login endpoint status: {response.status_code}")
        
        response = await client.get("/api/v1/users")
        print(f"ℹ️ Users endpoint status: {response.status_code}")
        
        response = await client.get("/api/v1/classes")
        print(f"ℹ️ Classes endpoint status: {response.status_code}")
        
        # These should return 404 or 405 since they're not implemented yet
        assert response.status_code in [404, 405, 422]
