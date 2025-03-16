# tests/integration/test_history_endpoints.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
import time

now = datetime.now(timezone.utc)
one_hour_ago = now - timedelta(hours=1)

@pytest.mark.asyncio
async def test_price_history_date_range(client, sample_data):
    """Test retrieving price history within a specific date range."""
    # Create a product
    product_data = {
        "name": "Price History Test Product",
        "description": "Product for testing price history",
        "price": 29.99,
        "stock_quantity": 100,
        "discount": 0,
        "category": "Test"
    }
    create_response = client.post("/api/v1/products/", json=product_data)
    product_id = create_response.json()["id"]
    
    # Update price multiple times with small delays
    updates = [
        {"price": 34.99},
        {"price": 39.99},
        {"price": 44.99}
    ]
    
    for update in updates:
        time.sleep(1)  # Ensure different timestamps
        client.put(f"/api/v1/products/{product_id}", json=update)
    
    # Get current time for range queries
    from datetime import datetime, timedelta
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    # Query with date range
    response = client.get(
        f"/api/v1/history/price/{product_id}",
        params={
            "start_date": one_hour_ago.isoformat(),
            "end_date": now.isoformat()
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should have all price changes
    assert len(data["items"]) >= 3
    
    # Verify that all the changes are within our requested time range
    for item in data["items"]:
        item_time = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
        assert item_time.timestamp() >= one_hour_ago.timestamp()
        assert item_time.timestamp() <= now.timestamp()

@pytest.mark.asyncio
async def test_stock_history_tracking(client, sample_data):
    """Test stock history is tracked properly."""
    # Create a product
    product_data = {
        "name": "Stock History Test Product",
        "description": "Product for testing stock history",
        "price": 29.99,
        "stock_quantity": 100,
        "discount": 0,
        "category": "Test"
    }
    create_response = client.post("/api/v1/products/", json=product_data)
    product_id = create_response.json()["id"]
    
    # Update stock multiple times
    updates = [
        {"stock_quantity": 90, "change_reason": "Sold 10 units"},
        {"stock_quantity": 110, "change_reason": "Restocked 20 units"},
        {"stock_quantity": 105, "change_reason": "Returned 5 defective units"}
    ]
    
    for update in updates:
        time.sleep(1)  # Ensure different timestamps
        client.put(f"/api/v1/products/{product_id}", json=update)
    
    # Query stock history
    response = client.get(f"/api/v1/history/stock/{product_id}")
    assert response.status_code == 200
    data = response.json()
    
    # Should have all stock changes plus initial
    assert len(data["items"]) >= 3
    
    # Check for specific change reasons
    change_reasons = [item["change_reason"] for item in data["items"]]
    assert "Sold 10 units" in change_reasons
    assert "Restocked 20 units" in change_reasons
    assert "Returned 5 defective units" in change_reasons
