# app/services/product.py
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.product import ProductRepository
from app.repositories.history import PriceHistoryRepository, StockHistoryRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse


class ProductService:
    """
    Service for handling business logic related to products.
    """
    
    def __init__(
        self,
        product_repository: ProductRepository,
        price_history_repository: PriceHistoryRepository,
        stock_history_repository: StockHistoryRepository
    ):
        self.product_repository = product_repository
        self.price_history_repository = price_history_repository
        self.stock_history_repository = stock_history_repository
    
    async def get_product(self, db: AsyncSession, id: int) -> ProductResponse:
        """
        Get a product by ID with suppliers loaded.
        """
        product = await self.product_repository.get_with_suppliers(db, id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {id} not found"
            )
        return product
    
    async def get_products(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc",
        **filters
    ) -> List[ProductResponse]:
        """
        Get multiple products with filtering, sorting and pagination.
        """
        return await self.product_repository.get_multi_with_suppliers(
            db, 
            skip=skip, 
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            **filters
        )
    
    async def search_products(
        self,
        db: AsyncSession,
        *,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ProductResponse]:
        """
        Search for products by name or description.
        """
        return await self.product_repository.search_products(
            db,
            search_term=search_term,
            skip=skip,
            limit=limit,
            **filters
        )
    
    async def create_product(self, db: AsyncSession, *, product_in: ProductCreate) -> ProductResponse:
        """
        Create a new product.
        """
        # Extract supplier IDs before creating the product
        supplier_ids = product_in.supplier_ids if hasattr(product_in, "supplier_ids") else []
        
        # Create product object without supplier_ids (since it's not a db column)
        product_data = product_in.model_dump(exclude={"supplier_ids"})
        product = await self.product_repository.create(db, obj_in=product_data)
        
        # Add suppliers if provided
        if supplier_ids:
            for supplier_id in supplier_ids:
                try:
                    await self.product_repository.add_supplier(
                        db,
                        product_id=product.id,
                        supplier_id=supplier_id
                    )
                except Exception as e:
                    # Log error but continue with other suppliers
                    print(f"Error adding supplier {supplier_id}: {str(e)}")
        
        # Get the product with its suppliers
        return await self.product_repository.get_with_suppliers(db, id=product.id)
    
    # Modify update_product in app/services/product.py
    async def update_product(
        self,
        db: AsyncSession,
        *,
        id: int,
        product_in: Union[ProductUpdate, Dict[str, Any]],
        change_reason: Optional[str] = None
    ):
        """
        Update a product with tracking price and stock changes.
        """
        # Get current product
        product = await self.product_repository.get(db, id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {id} not found"
            )
        
        # Convert to dict if it's a Pydantic model
        update_data = product_in
        if hasattr(product_in, "model_dump"):
            update_data = product_in.model_dump(exclude_unset=True)
        elif hasattr(product_in, "dict"):
            update_data = product_in.dict(exclude_unset=True)
        
        # Check for price changes
        if 'price' in update_data and update_data['price'] != product.price:
            await self.price_history_repository.add_price_change(
                db,
                product_id=product.id,
                old_price=product.price,
                new_price=update_data['price']
            )
        
        # Check for stock quantity changes
        if 'stock_quantity' in update_data and update_data['stock_quantity'] != product.stock_quantity:
            await self.stock_history_repository.add_stock_change(
                db,
                product_id=product.id,
                old_quantity=product.stock_quantity,
                new_quantity=update_data['stock_quantity'],
                change_reason=change_reason  # Pass the change reason
            )
        
        # Update the product
        updated_product = await self.product_repository.update(
            db,
            db_obj=product,
            obj_in=update_data
        )
        
        return updated_product
    
    async def delete_product(self, db: AsyncSession, *, id: int) -> ProductResponse:
        """
        Delete a product.
        """
        product = await self.product_repository.get(db, id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {id} not found"
            )
        
        # Delete the product
        deleted_product = await self.product_repository.delete(db, id=id)
        return deleted_product
    
    
    async def add_supplier_to_product(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        supplier_id: int
    ) -> ProductResponse:
        """
        Add a supplier to a product.
        """
        # Check if product exists
        product = await self.product_repository.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        # Add supplier (the repository will check if supplier exists)
        updated_product = await self.product_repository.add_supplier(
            db,
            product_id=product_id,
            supplier_id=supplier_id
        )
        
        return updated_product
    
    async def remove_supplier_from_product(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        supplier_id: int
    ) -> ProductResponse:
        """
        Remove a supplier from a product.
        """
        # Check if product exists
        product = await self.product_repository.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        # Remove supplier
        updated_product = await self.product_repository.remove_supplier(
            db,
            product_id=product_id,
            supplier_id=supplier_id
        )
        
        return updated_product
    
    async def get_low_stock_products(
        self,
        db: AsyncSession,
        *,
        threshold: int = 10,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProductResponse]:
        """
        Get products with stock quantity below the specified threshold.
        """
        return await self.product_repository.get_low_stock_products(
            db,
            threshold=threshold,
            skip=skip,
            limit=limit
        )
    
    async def get_product_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Get product statistics.
        """
        # Get product count by category
        category_stats = await self.product_repository.count_by_category(db)
        
        # Get total product count
        total_products = await self.product_repository.count(db)
        
        # Get low stock products count
        low_stock_count = len(await self.product_repository.get_low_stock_products(db, threshold=10, limit=1000))
        
        # Compile statistics
        statistics = {
            "total_products": total_products,
            "products_by_category": category_stats,
            "low_stock_products": low_stock_count
        }
        
        return statistics

    async def get_product_suppliers(self, db: AsyncSession, product_id: int):
        """Get all suppliers for a specific product."""
        product = await self.product_repository.get_with_suppliers(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        # Ensure we have a list, even if empty
        return product.suppliers or []
    
    async def count_search_results(
        self, 
        db: AsyncSession, 
        *, 
        search_term: str,
        **filters
    ) -> int:
        """
        Count the total number of products matching a search term and additional filters.
        """
        # Combine search term with other filters
        filter_conditions = {
            "search_term": search_term,
            **filters
        }
        
        # Use the repository's count method to get the total
        return await self.product_repository.count(db, **filter_conditions)
    

    async def batch_create_products(
        self,
        db: AsyncSession,
        *,
        products_in: List[ProductCreate]
    ) -> List[ProductResponse]:
        """
        Create multiple products in a batch.
        """
        return await self.product_repository.batch_create(db, objs_in=products_in)


    async def batch_update_products(
        self,
        db: AsyncSession,
        *,
        updates: List[Dict[str, Any]]
    ) -> List[ProductResponse]:
        """
        Update multiple products in a batch.
        
        Each update dict must contain an 'id' key and at least one field to update.
        """
        updated_products = []
        missing_products = []
        
        for update_item in updates:
            if "id" not in update_item:
                continue
                
            product_id = update_item["id"]
            product = await self.product_repository.get(db, id=product_id)
            
            if not product:
                missing_products.append(product_id)
                continue
            
            # Create a copy without the id for the update
            update_data = {k: v for k, v in update_item.items() if k != "id"}
            change_reason = update_data.pop("change_reason", None)
            
            # Track price changes
            if "price" in update_data and update_data["price"] != product.price:
                await self.price_history_repository.add_price_change(
                    db,
                    product_id=product.id,
                    old_price=product.price,
                    new_price=update_data["price"]
                )
            
            # Track stock changes
            if "stock_quantity" in update_data and update_data["stock_quantity"] != product.stock_quantity:
                await self.stock_history_repository.add_stock_change(
                    db,
                    product_id=product.id,
                    old_quantity=product.stock_quantity,
                    new_quantity=update_data["stock_quantity"],
                    change_reason=change_reason
                )
            
            # Update the product
            updated_product = await self.product_repository.update(
                db,
                db_obj=product,
                obj_in=update_data
            )
            
            updated_products.append(updated_product)
        
        # If any products were not found, raise an exception
        if missing_products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Products with IDs {missing_products} not found"
            )
        
        return updated_products


    # Improved batch_delete_products method
    async def batch_delete_products(
        self,
        db: AsyncSession,
        *,
        ids: List[int]
    ) -> List[ProductResponse]:
        """
        Delete multiple products in a batch.
        """
        deleted_products = []
        not_found_ids = []
        
        for product_id in ids:
            product = await self.product_repository.get(db, id=product_id)
            if product:
                # Keep a copy of the product before deletion
                deleted_products.append(product)
                await self.product_repository.delete(db, id=product_id)
            else:
                not_found_ids.append(product_id)
        
        # If we couldn't find some products, raise an exception
        if not_found_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Products with IDs {not_found_ids} not found"
            )
        
        return deleted_products

    