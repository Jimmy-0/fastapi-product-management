# tests/integration/test_auth.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_user_registration(client):
    """Test user registration endpoint."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "full_name": "Test User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data  # Password should not be returned

@pytest.mark.asyncio
async def test_user_login(client):
    """Test user login and JWT token generation."""
    # Register a user first
    user_data = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "securepassword123",
        "full_name": "Login User"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Attempt login
    login_data = {
        "username": "loginuser",
        "password": "securepassword123"
    }
    
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_protected_endpoint(client):
    """Test access to protected endpoint with JWT token."""
    # Register and login to get token
    user_data = {
        "username": "protecteduser",
        "email": "protected@example.com",
        "password": "securepassword123",
        "full_name": "Protected User"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "username": "protecteduser",
        "password": "securepassword123"
    }
    
    login_response = client.post("/api/v1/auth/token", data=login_data)
    token = login_response.json()["access_token"]
    
    # Access protected endpoint
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Try to access admin-only endpoint
    response = client.get("/api/v1/admin/products", headers=headers)
    
    # Expected behavior depends on the user's role
    # The test verifies the authentication is working
    # Status 403 means authentication worked but authorization failed
    # Status 200 means both authentication and authorization worked
    assert response.status_code in [200, 403]
