# tests/integration/test_supplier_management.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_create_supplier(client):
    """Test creating a supplier."""
    supplier_data = {
        "name": "Test Supplier Creation",
        "contact_info": "supplier@test.com",
        "credit_rating": 4
    }
    
    response = client.post("/api/v1/suppliers/", json=supplier_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == supplier_data["name"]
    assert data["contact_info"] == supplier_data["contact_info"]
    assert data["credit_rating"] == supplier_data["credit_rating"]
    assert "id" in data

@pytest.mark.asyncio
async def test_get_suppliers(client):
    """Test retrieving all suppliers."""
    # Create multiple suppliers
    for i in range(3):
        supplier_data = {
            "name": f"Test Supplier {i}",
            "contact_info": f"supplier{i}@test.com",
            "credit_rating": i % 5
        }
        client.post("/api/v1/suppliers/", json=supplier_data)
    
    response = client.get("/api/v1/suppliers/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 3

@pytest.mark.asyncio
async def test_update_supplier(client):
    """Test updating a supplier."""
    # Create a supplier
    supplier_data = {
        "name": "Supplier to Update",
        "contact_info": "update@test.com",
        "credit_rating": 3
    }
    
    create_response = client.post("/api/v1/suppliers/", json=supplier_data)
    supplier_id = create_response.json()["id"]
    
    # Update the supplier
    update_data = {
        "name": "Updated Supplier Name",
        "credit_rating": 5
    }
    
    response = client.put(f"/api/v1/suppliers/{supplier_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["credit_rating"] == update_data["credit_rating"]
    assert data["contact_info"] == supplier_data["contact_info"]  # Unchanged

@pytest.mark.asyncio
async def test_product_with_multiple_suppliers(client):
    """Test creating a product with multiple suppliers (many-to-many relationship)."""
    # Create suppliers
    supplier_ids = []
    for i in range(3):
        supplier_data = {
            "name": f"Multi-Supplier Test {i}",
            "contact_info": f"multi{i}@test.com",
            "credit_rating": 3 + (i % 3)
        }
        response = client.post("/api/v1/suppliers/", json=supplier_data)
        supplier_ids.append(response.json()["id"])
    
    # Create product with multiple suppliers
    product_data = {
        "name": "Multi-Supplier Product",
        "description": "Product with multiple suppliers",
        "price": 99.99,
        "stock_quantity": 100,
        "discount": 0,
        "category": "Test",
        "supplier_ids": supplier_ids
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 201
    product_id = response.json()["id"]
    
    # Get product suppliers
    response = client.get(f"/api/v1/products/{product_id}/suppliers")
    assert response.status_code == 200
    data = response.json()
    assert "suppliers" in data
    assert len(data["suppliers"]) == len(supplier_ids)
    retrieved_supplier_ids = [s["id"] for s in data["suppliers"]]
    for supplier_id in supplier_ids:
        assert supplier_id in retrieved_supplier_ids
