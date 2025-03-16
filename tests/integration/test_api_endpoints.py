# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "product-service"

@pytest.mark.asyncio
async def test_create_product(client):
    """Test creating a product."""
    product_data = {
        "name": "Lifecycle Product",
        "description": "Testing full lifecycle",
        "price": 49.99,
        "stock_quantity": 50,
        "discount": 0,
        "supplier_id": 1
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert "id" in data

@pytest.mark.asyncio
async def test_get_products(client, sample_data):
    """Test retrieving products."""
    response = client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    # Additional checks as needed
    assert len(data["items"]) > 0

@pytest.mark.asyncio
async def test_get_product_by_id(client, sample_data):
    """Test retrieving a product by ID."""
    product_id = sample_data["product"].id
    response = client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == sample_data["product"].name