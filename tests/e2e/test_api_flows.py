# test/e2e/test_api_flows.py
import pytest

@pytest.mark.asyncio
async def test_product_lifecycle(client):
    """Test the complete lifecycle of a product."""
    # Create a supplier first
    supplier_data = {
        "name": "Lifecycle Supplier",
        "contact_info": "lifecycle@test.com",
        "credit_rating": 0 
    }
    supplier_response = client.post("/api/v1/suppliers/", json=supplier_data)
    print("Supplier response:", supplier_response.status_code, supplier_response.json())
    assert supplier_response.status_code == 201
    supplier_id = supplier_response.json()["id"]
    
    # Create a product
    product_data = {
        "name": "Lifecycle Product",
        "description": "Testing full lifecycle",
        "price": 49.99,
        "stock_quantity": 50,
        "discount": 0,
        "supplier_id": supplier_id
    }
    create_response = client.post("/api/v1/products/", json=product_data)
    print("Product response:", create_response.status_code, create_response.json())
    print("Response status:", create_response.status_code)
    print("Response body:", create_response.json())  # This will show the validation error details
    assert create_response.status_code == 201
    product_id = create_response.json()["id"]
    
    # Get the product
    get_response = client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == product_data["name"]
    
    # Update the product
    update_data = {
        "name": "Updated Lifecycle Product",
        "price": 39.99
    }
    update_response = client.put(f"/api/v1/products/{product_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == update_data["name"]
    assert update_response.json()["price"] == update_data["price"]
    
    # Check price history was created
    history_response = client.get(f"/api/v1/history/price/{product_id}")
    assert history_response.status_code == 200
    history_data = history_response.json()
    print("History data:", history_data) 
    assert len(history_data) >= 1
    assert history_data["items"][0]["old_price"] == product_data["price"]
    assert history_data["items"][0]["new_price"] == update_data["price"]
    # assert history_data[0]["old_price"] == product_data["price"]
    # assert history_data[0]["new_price"] == update_data["price"]
    
    # Delete the product
    delete_response = client.delete(f"/api/v1/products/{product_id}")
    assert delete_response.status_code == 200
    
    # Verify product is gone
    verify_response = client.get(f"/api/v1/products/{product_id}")
    assert verify_response.status_code == 404