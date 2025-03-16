# tests/integration/test_rbac.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_user_roles(client):
    """Test assigning roles to users."""
    # Create a test user
    user_data = {
        "username": "roleuser",
        "email": "role@example.com",
        "password": "securepassword123",
        "full_name": "Role Test User"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Login as admin (assuming admin credentials are set in test environment)
    admin_login = {
        "username": "admin",
        "password": "admin_password"
    }
    admin_login_response = client.post("/api/v1/auth/token", data=admin_login)
    admin_token = admin_login_response.json()["access_token"]
    
    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }
    
    # Assign supplier role to the user
    role_data = {
        "username": "roleuser",
        "role": "supplier"
    }
    
    response = client.post("/api/v1/admin/users/role", json=role_data, headers=admin_headers)
    assert response.status_code == 200
    
    # Verify user has the supplier role
    user_response = client.get("/api/v1/admin/users/roleuser", headers=admin_headers)
    assert user_response.status_code == 200
    user_data = user_response.json()
    assert "roles" in user_data
    assert "supplier" in user_data["roles"]

@pytest.mark.asyncio
async def test_role_based_access(client):
    """Test role-based access control for different endpoints."""
    # Create users with different roles
    users = [
        {"username": "admin_user", "role": "admin"},
        {"username": "supplier_user", "role": "supplier"},
        {"username": "regular_user", "role": "user"}
    ]
    
    tokens = {}
    
    for user in users:
        # Register user
        user_data = {
            "username": user["username"],
            "email": f"{user['username']}@example.com",
            "password": "securepassword123",
            "full_name": f"{user['username'].title()} Test"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Login to get token
        login_data = {
            "username": user["username"],
            "password": "securepassword123"
        }
        login_response = client.post("/api/v1/auth/token", data=login_data)
        tokens[user["username"]] = login_response.json()["access_token"]
    
    # Test admin-only endpoint access
    admin_headers = {"Authorization": f"Bearer {tokens['admin_user']}"}
    supplier_headers = {"Authorization": f"Bearer {tokens['supplier_user']}"}
    user_headers = {"Authorization": f"Bearer {tokens['regular_user']}"}
    
    # Admin should have access to admin endpoints
    admin_response = client.get("/api/v1/admin/users", headers=admin_headers)
    assert admin_response.status_code == 200
    
    # Supplier should NOT have access to admin endpoints
    supplier_response = client.get("/api/v1/admin/users", headers=supplier_headers)
    assert supplier_response.status_code == 403
    
    # Regular user should NOT have access to admin endpoints
    user_response = client.get("/api/v1/admin/users", headers=user_headers)
    assert user_response.status_code == 403
    
    # Test supplier endpoint access (example: bulk product upload)
    # Admin and suppliers should have access
    admin_supplier_response = client.post("/api/v1/suppliers/products/bulk", 
                                       json={"products": []}, 
                                       headers=admin_headers)
    assert admin_supplier_response.status_code in [200, 201, 400]  # 400 is OK if empty list is invalid
    
    supplier_supplier_response = client.post("/api/v1/suppliers/products/bulk", 
                                       json={"products": []}, 
                                       headers=supplier_headers)
    assert supplier_supplier_response.status_code in [200, 201, 400]  # 400 is OK if empty list is invalid
    
    # Regular user should NOT have access to supplier endpoints
    user_supplier_response = client.post("/api/v1/suppliers/products/bulk", 
                                      json={"products": []}, 
                                      headers=user_headers)
    assert user_supplier_response.status_code == 403
