# tests/integration/test_concurrency.py
import pytest
import asyncio
import time
import json
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.asyncio
async def test_concurrent_updates(client):
    """Test concurrent updates to the same product."""
    # Create a test product
    product_data = {
        "name": "Concurrency Test Product",
        "description": "Testing concurrent updates",
        "price": 29.99,
        "stock_quantity": 100,
        "discount": 0,
        "category": "Test"
    }
    
    create_response = client.post("/api/v1/products/", json=product_data)
    product_id = create_response.json()["id"]
    
    # Function to update stock
    def update_stock(amount):
        update_data = {"stock_quantity": amount}
        return client.put(f"/api/v1/products/{product_id}", json=update_data)
    
    # Make concurrent update requests
    updates = [90, 80, 70, 60, 50]
    
    with ThreadPoolExecutor(max_workers=len(updates)) as executor:
        futures = [executor.submit(update_stock, amount) for amount in updates]
        responses = [future.result() for future in futures]
    
    # All requests should succeed
    assert all(response.status_code == 200 for response in responses)
    
    # Get the final product state
    get_response = client.get(f"/api/v1/products/{product_id}")
    final_product = get_response.json()
    
    # Final stock should match one of our update values
    assert final_product["stock_quantity"] in updates
    
    # Check that stock history records all changes
    history_response = client.get(f"/api/v1/history/stock/{product_id}")
    assert history_response.status_code == 200
    history_data = history_response.json()
    
    # Should have multiple history entries
    assert len(history_data["items"]) >= 5  # One for initial creation plus our updates

@pytest.mark.asyncio
async def test_high_load(client):
    """Test system behavior under high load with mixed operations."""
    # Create some initial products
    product_ids = []
    for i in range(10):
        product_data = {
            "name": f"High Load Test Product {i}",
            "description": f"Product {i} for high load testing",
            "price": 10 + i,
            "stock_quantity": 100,
            "discount": 0,
            "category": "Load Test"
        }
        response = client.post("/api/v1/products/", json=product_data)
        product_ids.append(response.json()["id"])
    
    # Define different operations
    def get_all_products():
        return client.get("/api/v1/products/?page=1&size=10")
    
    def get_product(product_id):
        return client.get(f"/api/v1/products/{product_id}")
    
    def update_product(product_id):
        new_price = 20 + (int(time.time()) % 10)  # Dynamic price to avoid duplicates
        return client.put(f"/api/v1/products/{product_id}", 
                        json={"price": new_price})
    
    def create_product():
        index = int(time.time() * 1000) % 1000  # Unique index
        return client.post("/api/v1/products/", json={
            "name": f"New Load Test Product {index}",
            "description": "Created during load test",
            "price": 15.99,
            "stock_quantity": 50,
            "discount": 0,
            "category": "Load Test"
        })
    
    # Build a mix of operations
    operations = []
    for _ in range(20):  # 20 get_all operations
        operations.append(get_all_products)
    
    for product_id in product_ids:
        # 2 get and 1 update per product
        operations.append(lambda pid=product_id: get_product(pid))
        operations.append(lambda pid=product_id: get_product(pid))
        operations.append(lambda pid=product_id: update_product(pid))
    
    for _ in range(5):  # 5 create operations
        operations.append(create_product)
    
    # Shuffle operations to simulate random access
    import random
    random.shuffle(operations)
    
    # Execute all operations concurrently
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(operation) for operation in operations]
        responses = [future.result() for future in futures]
    
    end_time = time.time()
    
    # All requests should complete successfully
    # Some operations might fail due to validation or concurrency issues, which is fine
    success_rate = sum(1 for resp in responses if resp.status_code < 400) / len(responses)
    assert success_rate > 0.95  # At least 95% success rate
    
    # Overall performance check
    execution_time = end_time - start_time
    operations_per_second = len(operations) / execution_time
    print(f"Performed {operations_per_second:.2f} operations per second")
    # The exact threshold depends on your hardware, but it should be reasonably fast
    assert operations_per_second > 5  # At least 5 operations per second