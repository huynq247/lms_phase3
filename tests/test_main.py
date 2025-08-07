import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Flashcard LMS Backend API"
    assert "version" in data

def test_health_endpoint():
    """Test basic health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data

def test_api_health_endpoint():
    """Test API versioned health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_file_upload_limits():
    """Test file upload limits endpoint."""
    response = client.get("/api/v1/info/limits")
    assert response.status_code == 200
    data = response.json()
    assert "max_file_size" in data
    assert "allowed_image_types" in data
    assert "allowed_audio_types" in data

def test_docs_available():
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200

def test_readiness_probe():
    """Test Kubernetes readiness probe."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code in [200, 503]  # May fail if DB not connected

def test_liveness_probe():
    """Test Kubernetes liveness probe."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
