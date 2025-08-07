"""
Test email verification functionality
"""
import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app


class TestEmailVerification:
    """Test email verification endpoints."""
    
    @pytest.mark.asyncio
    async def test_verify_email_with_valid_token(self):
        """Test email verification with valid token."""
        async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
            # Use existing user ID as token for testing
            user_id = "674f3e0b0b48e60bfc9dc7f7"  # Admin user from DATABASE_USERS.md
            
            response = await client.post(
                f"/api/v1/auth/verify-email?token={user_id}"
            )
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert "message" in result
            assert "verified" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_verify_email_with_invalid_token(self):
        """Test email verification with invalid token."""
        async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
            response = await client.post(
                "/api/v1/auth/verify-email?token=invalid_token"
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            result = response.json()
            assert "detail" in result
            assert "invalid" in result["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_on_login(self):
        """Test rate limiting on login endpoint."""
        async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
            login_data = {
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
            
            # Make multiple rapid login attempts
            responses = []
            for i in range(7):  # Exceed the 5/minute limit
                response = await client.post("/api/v1/auth/login", json=login_data)
                responses.append(response.status_code)
            
            # Should get rate limited after 5 attempts
            assert status.HTTP_429_TOO_MANY_REQUESTS in responses
