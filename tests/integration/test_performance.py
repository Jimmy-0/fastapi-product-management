# tests/integration/test_performance.py
import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.asyncio
async def test_connection_pool(client):
    """Test database connection pool under multiple requests."""
    # Create a product to query
    product_data = {
        "name": "Connection Pool Test Product",
        "description": "Testing database connection pool",
        "price": 29.99,
        "stock_quantity": 100,
        "discount": 0,
        "category": "Test"
    }
    
    create_response = client.post("/api/v1/products/", json=product_data)
    product_id = create_response.json()["id"]
    
    # Function to make a request
    def make_request():
        return client.get(f"/api/v1/products/{product_id}")
    
    # Make multiple concurrent requests
    num_requests = 20
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
        responses = [future.result() for future in futures]
    
    end_time = time.time()
    
    # All requests should be successful
    assert all(response.status_code == 200 for response in responses)
    
    # Time should be reasonable (specific threshold depends on your system)
    # This is a very basic check - real performance tests would be more sophisticated
    execution_time = end_time - start_time
    assert execution_time < num_requests * 0.5  # Assuming each request takes less than 0.5 seconds

@pytest.mark.asyncio
async def test_index_performance(client, sample_data):
    """Test query performance with filters that should use indexes."""
    # Create many products with different attributes
    for i in range(50):  # Creating 50 products
        product_data = {
            "name": f"Performance Test Product {i}",
            "description": f"Product {i} for performance testing",
            "price": 10 + i,
            "stock_quantity": 100 + i,
            "discount": i % 10,
            "category": f"Category {i % 5}"
        }
        client.post("/api/v1/products/", json=product_data)
    
    # Time a category filter query (should use index)
    start_time = time.time()
    response = client.get("/api/v1/products/?category=Category%201&page=1&size=10")
    end_time = time.time()
    
    # Query should be successful
    assert response.status_code == 200
    
    # And reasonably fast
    query_time = end_time - start_time
    assert query_time < 0.5  # Adjust threshold as needed
    
    # Similarly test price range query
    start_time = time.time()
    response = client.get("/api/v1/products/?min_price=20&max_price=40&page=1&size=10")
    end_time = time.time()
    
    assert response.status_code == 200
    query_time = end_time - start_time
    assert query_time < 0.5  # Adjust threshold as needed
