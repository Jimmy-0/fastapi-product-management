# tests/integration/test_advanced_queries.py
import pytest
import asyncio
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_product_pagination(client, sample_data):
    """Test pagination of products."""
    # Create multiple products to ensure pagination
    async def create_product(i):
        product_data = {
            "name": f"Pagination Test Product {i}",
            "description": f"Test description {i}",
            "price": 10.99 + i,
            "stock_quantity": 50 + i,
            "discount": 0,
            "category": f"Category {i % 3}"
        }
        response = await client.post("/api/v1/products/", json=product_data)
        assert response.status_code == 201

    # Create products concurrently
    await asyncio.gather(*[create_product(i) for i in range(15)])

    # Test first page
    response = await client.get("/api/v1/products/?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 10  # Should get exactly 10 items
    assert data["total"] == 15  # Total should reflect all created products
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["pages"] == 2  # 15 items with size 10 = 2 pages

    # Test second page
    response = await client.get("/api/v1/products/?page=2&size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 5  # Should get remaining 5 items
    assert data["page"] == 2

@pytest.mark.asyncio
async def test_product_sorting(client, sample_data):
    """Test sorting products by different fields."""
    # Create products with varying prices
    for i in range(5):
        product_data = {
            "name": f"Sorting Test Product {i}",
            "description": f"Test description {i}",
            "price": 100 - (i * 10),  # Prices: 100, 90, 80, 70, 60
            "stock_quantity": i * 10,  # Quantities: 0, 10, 20, 30, 40
            "discount": 0,
            "category": "Test"
        }
        client.post("/api/v1/products/", json=product_data)
    
    # Test sorting by price (ascending)
    response = client.get("/api/v1/products/?sort=price&order=asc")
    assert response.status_code == 200
    data = response.json()
    prices = [item["price"] for item in data["items"]]
    assert sorted(prices) == prices
    
    # Test sorting by price (descending)
    response = client.get("/api/v1/products/?sort=price&order=desc")
    assert response.status_code == 200
    data = response.json()
    prices = [item["price"] for item in data["items"]]
    assert sorted(prices, reverse=True) == prices
    
    # Test sorting by stock_quantity
    response = client.get("/api/v1/products/?sort=stock_quantity&order=desc")
    assert response.status_code == 200
    data = response.json()
    quantities = [item["stock_quantity"] for item in data["items"]]
    assert sorted(quantities, reverse=True) == quantities

@pytest.mark.asyncio
async def test_product_filtering(client, sample_data):
    """Test filtering products by various criteria."""
    # Create products with different categories and prices
    categories = ["Electronics", "Clothing", "Home"]
    for i in range(9):
        category = categories[i % 3]
        product_data = {
            "name": f"{category} Test Product {i}",
            "description": f"Test description {i}",
            "price": 50 + (i * 10),  # Prices ranging from 50 to 130
            "stock_quantity": 100 - (i * 10),  # Quantities from 100 down to 20
            "discount": i * 5,  # Discounts from 0% to 40%
            "category": category
        }
        client.post("/api/v1/products/", json=product_data)
    
    # Test filtering by category
    response = client.get("/api/v1/products/?category=Electronics")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["category"] == "Electronics"
    
    # Test filtering by price range
    response = client.get("/api/v1/products/?min_price=70&max_price=100")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert 70 <= item["price"] <= 100
    
    # Test filtering by stock range
    response = client.get("/api/v1/products/?min_stock=50&max_stock=80")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert 50 <= item["stock_quantity"] <= 80
    
    # Test combined filters
    response = client.get("/api/v1/products/?category=Clothing&min_price=60&max_price=90")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["category"] == "Clothing"
        assert 60 <= item["price"] <= 90

@pytest.mark.asyncio
async def test_product_search(client, sample_data):
    """Test search functionality for products."""
    # Create products with specific names and descriptions
    products = [
        {
            "name": "Premium Wireless Headphones",
            "description": "Noise-cancelling bluetooth headphones with high fidelity sound",
            "price": 199.99,
            "stock_quantity": 50,
            "discount": 0,
            "category": "Electronics"
        },
        {
            "name": "Basic Wired Earbuds",
            "description": "Simple but effective earbuds for everyday use",
            "price": 19.99,
            "stock_quantity": 200,
            "discount": 0,
            "category": "Electronics"
        },
        {
            "name": "Ergonomic Office Chair",
            "description": "Comfortable chair with lumbar support for long work hours",
            "price": 249.99,
            "stock_quantity": 30,
            "discount": 10,
            "category": "Furniture"
        }
    ]

    # Create products concurrently - FIXED: don't try to await the response again
    async def create_product(product):
        response = await client.post("/api/v1/products/", json=product)
        assert response.status_code == 201
        return response  # Just return the response, don't await it again

    await asyncio.gather(*[create_product(product) for product in products])

    # Test search by name (partial match)
    response = await client.get("/api/v1/products/search?query=headphones")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert any("Headphones" in item["name"] for item in data["items"])

    # Test search by description
    response = await client.get("/api/v1/products/search?query=bluetooth")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert any("bluetooth" in item["description"].lower() for item in data["items"])

    # Test search with multiple matches
    response = await client.get("/api/v1/products/search?query=ear")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 2  # Should match "Headphones" and "Earbuds"