# tests/integration/test_batch_operations.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_batch_create_products(client):
    """Test creating multiple products in a single request."""
    batch_data = {
        "products": [
            {
                "name": "Batch Product 1",
                "description": "First batch product",
                "price": 29.99,
                "stock_quantity": 100,
                "discount": 0,
                "category": "Batch Test"
            },
            {
                "name": "Batch Product 2",
                "description": "Second batch product",
                "price": 39.99,
                "stock_quantity": 50,
                "discount": 5,
                "category": "Batch Test"
            },
            {
                "name": "Batch Product 3",
                "description": "Third batch product",
                "price": 49.99,
                "stock_quantity": 75,
                "discount": 10,
                "category": "Batch Test"
            }
        ]
    }
    
    response = client.post("/api/v1/products/batch", json=batch_data)
    assert response.status_code == 201
    data = response.json()
    assert "products" in data
    assert isinstance(data["products"], list)
    assert len(data["products"]) == 3
    assert all("id" in product for product in data["products"])
    
    # Verify products were created
    for product in data["products"]:
        get_response = client.get(f"/api/v1/products/{product['id']}")
        assert get_response.status_code == 200

@pytest.mark.asyncio
async def test_batch_update_products(client, sample_data):
    """Test updating multiple products in a single request."""
    # Create several products first
    product_ids = []
    for i in range(3):
        product_data = {
            "name": f"Update Batch Product {i}",
            "description": "Product for batch update test",
            "price": 19.99,
            "stock_quantity": 100,
            "discount": 0,
            "category": "Test"
        }
        response = client.post("/api/v1/products/", json=product_data)
        product_ids.append(response.json()["id"])
    
    # Batch update
    update_data = {
        "updates": [
            {
                "id": product_ids[0],
                "price": 24.99,
                "discount": 5
            },
            {
                "id": product_ids[1],
                "price": 29.99,
                "stock_quantity": 75
            },
            {
                "id": product_ids[2],
                "description": "Updated description",
                "price": 34.99
            }
        ]
    }
    
    response = client.put("/api/v1/products/batch", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert "updated" in data
    assert len(data["updated"]) == 3
    
    # Verify changes
    response = client.get(f"/api/v1/products/{product_ids[0]}")
    assert response.json()["price"] == 24.99
    assert response.json()["discount"] == 5
    
    response = client.get(f"/api/v1/products/{product_ids[1]}")
    assert response.json()["price"] == 29.99
    assert response.json()["stock_quantity"] == 75
    
    response = client.get(f"/api/v1/products/{product_ids[2]}")
    assert response.json()["description"] == "Updated description"
    assert response.json()["price"] == 34.99
    
    # Check that price history was created for all products
    for product_id in product_ids:
        history_response = client.get(f"/api/v1/history/price/{product_id}")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data["items"]) >= 1

@pytest.mark.asyncio
async def test_batch_delete_products(client):
    """Test deleting multiple products in a single request."""
    # Create several products first
    product_ids = []
    for i in range(3):
        product_data = {
            "name": f"Delete Batch Product {i}",
            "description": "Product for batch delete test",
            "price": 19.99,
            "stock_quantity": 100,
            "discount": 0,
            "category": "Test"
        }
        response = client.post("/api/v1/products/", json=product_data)
        product_ids.append(response.json()["id"])
    
    # Batch delete
    delete_query = ",".join(str(id) for id in product_ids)
    response = client.delete(f"/api/v1/products/batch?product_ids={delete_query}")
    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data
    assert len(data["deleted"]) == 3
    
    # Verify products were deleted
    for product_id in product_ids:
        response = client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 404