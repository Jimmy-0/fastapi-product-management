# tests/unit/test_validation.py
import pytest
from fastapi.testclient import TestClient

def test_product_validation_name(client):
    """Test product name validation constraints."""
    # Test name too short
    product_data = {
        "name": "ab",  # Less than 3 characters
        "price": 19.99,
        "stock_quantity": 100,
        "discount": 0,
        "category": "Test"
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 422
    data = response.json()
    assert "name" in str(data).lower()
    
    # Test name too long
    product_data = {
        "name": "a" * 101,  # More than 100 characters
        "price": 19.99,
        "stock_quantity": 100,
        "discount": 0,
        "category": "Test"
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 422
    data = response.json()
    assert "name" in str(data).lower()

def test_product_validation_price(client):
    """Test product price validation constraints."""
    # Test negative price
    product_data = {
        "name": "Price Test Product",
        "price": -10.0,  # Negative price
        "stock_quantity": 100,
        "discount": 0,
        "category": "Test"
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 422
    data = response.json()
    assert "price" in str(data).lower()
    
    # Test too many decimal places
    product_data = {
        "name": "Price Test Product",
        "price": 19.999,  # More than 2 decimal places
        "stock_quantity": 100,
        "discount": 0,
        "category": "Test"
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 422
    data = response.json()
    assert "price" in str(data).lower()

def test_product_validation_stock(client):
    """Test product stock validation constraints."""
    # Test negative stock
    product_data = {
        "name": "Stock Test Product",
        "price": 19.99,
        "stock_quantity": -10,  # Negative stock
        "discount": 0,
        "category": "Test"
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 422
    data = response.json()
    assert "stock_quantity" in str(data).lower()

def test_product_validation_discount(client):
    """Test product discount validation constraints."""
    # Test discount below 0%
    product_data = {
        "name": "Discount Test Product",
        "price": 19.99,
        "stock_quantity": 100,
        "discount": -5,  # Negative discount
        "category": "Test"
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 422
    data = response.json()
    assert "discount" in str(data).lower()
    
    # Test discount above 100%
    product_data = {
        "name": "Discount Test Product",
        "price": 19.99,
        "stock_quantity": 100,
        "discount": 110,  # More than 100%
        "category": "Test"
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 422
    data = response.json()
    assert "discount" in str(data).lower()