# app/repositories/product.py
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Product, ProductSupplier
from app.schemas.product import ProductCreate, ProductUpdate
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    """
    Repository for Product entity with custom methods specific to products.
    """
    
    def __init__(self):
        super().__init__(Product)
    
    async def get_with_suppliers(self, db: AsyncSession, id: Any) -> Optional[Product]:
        """
        Get a product by ID with its suppliers loaded.
        """
        query = select(Product).where(Product.id == id).options(
            selectinload(Product.suppliers)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_multi_with_suppliers(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        **kwargs
    ) -> List[Product]:
        """
        Get multiple products with their suppliers loaded, with pagination and filtering.
        """
        query = select(Product).options(
            selectinload(Product.suppliers)
        )
        
        # Apply filters
        if kwargs:
            filter_conditions = []
            for key, value in kwargs.items():
                if key == "category" and value:
                    filter_conditions.append(Product.category == value)
                elif key == "price_range" and isinstance(value, dict):
                    if "min" in value and value["min"] is not None:
                        filter_conditions.append(Product.price >= value["min"])
                    if "max" in value and value["max"] is not None:
                        filter_conditions.append(Product.price <= value["max"])
                elif key == "stock_range" and isinstance(value, dict):
                    if "min" in value and value["min"] is not None:
                        filter_conditions.append(Product.stock_quantity >= value["min"])
                    if "max" in value and value["max"] is not None:
                        filter_conditions.append(Product.stock_quantity <= value["max"])
                elif hasattr(Product, key) and value is not None:
                    filter_conditions.append(getattr(Product, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))

        # Apply sorting
        if sort_by and hasattr(Product, sort_by):
            column = getattr(Product, sort_by)
            if sort_order and sort_order.lower() == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        else:
            query = query.order_by(Product.id.asc())

        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count(self, db: AsyncSession, **kwargs) -> int:
        """
        Count total products with filters applied.
        """
        query = select(func.count(Product.id))
        
        # Apply filters
        if kwargs:
            filter_conditions = []
            for key, value in kwargs.items():
                if key == "category" and value:
                    filter_conditions.append(Product.category == value)
                elif key == "price_range" and isinstance(value, dict):
                    if "min" in value and value["min"] is not None:
                        filter_conditions.append(Product.price >= value["min"])
                    if "max" in value and value["max"] is not None:
                        filter_conditions.append(Product.price <= value["max"])
                elif key == "stock_range" and isinstance(value, dict):
                    if "min" in value and value["min"] is not None:
                        filter_conditions.append(Product.stock_quantity >= value["min"])
                    if "max" in value and value["max"] is not None:
                        filter_conditions.append(Product.stock_quantity <= value["max"])
                elif key == "search_term" and value:
                    # For search functionality
                    filter_conditions.append(
                        or_(
                            Product.name.ilike(f"%{value}%"),
                            Product.description.ilike(f"%{value}%")
                        )
                    )
                elif hasattr(Product, key) and value is not None:
                    filter_conditions.append(getattr(Product, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        result = await db.execute(query)
        return result.scalar_one()


    async def search_products(
        self,
        db: AsyncSession,
        *,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        **kwargs
    ) -> List[Product]:
        """
        Search for products by name or description.
        """
        search_conditions = [
            Product.name.ilike(f"%{search_term}%"),
            Product.description.ilike(f"%{search_term}%")
        ]
        
        query = select(Product).where(or_(*search_conditions))
        
        # Apply additional filters
        if kwargs:
            filter_conditions = []
            for key, value in kwargs.items():
                if hasattr(Product, key):
                    if key == "category" and value:
                        filter_conditions.append(Product.category == value)
                    elif key == "price_range" and isinstance(value, dict):
                        if "min" in value and value["min"] is not None:
                            filter_conditions.append(Product.price >= value["min"])
                        if "max" in value and value["max"] is not None:
                            filter_conditions.append(Product.price <= value["max"])
                    elif key == "stock_range" and isinstance(value, dict):
                        if "min" in value and value["min"] is not None:
                            filter_conditions.append(Product.stock_quantity >= value["min"])
                        if "max" in value and value["max"] is not None:
                            filter_conditions.append(Product.stock_quantity <= value["max"])
                    elif value is not None:
                        filter_conditions.append(getattr(Product, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Add supplier loading
        query = query.options(selectinload(Product.suppliers))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def add_supplier(
        self, 
        db: AsyncSession, 
        *, 
        product_id: int, 
        supplier_id: int
    ) -> Product:
        """
        Add a supplier to a product.
        """
        # Check if association already exists
        query = select(ProductSupplier).where(
            and_(
                ProductSupplier.product_id == product_id,
                ProductSupplier.supplier_id == supplier_id
            )
        )
        result = await db.execute(query)
        association = result.scalar_one_or_none()
        
        if not association:
            # Create new association
            association = ProductSupplier(
                product_id=product_id,
                supplier_id=supplier_id
            )
            db.add(association)
            await db.commit()
        
        # Return the product with its suppliers
        return await self.get_with_suppliers(db, product_id)
    
    async def remove_supplier(
        self, 
        db: AsyncSession, 
        *, 
        product_id: int, 
        supplier_id: int
    ) -> Product:
        """
        Remove a supplier from a product.
        """
        # Find the association
        query = select(ProductSupplier).where(
            and_(
                ProductSupplier.product_id == product_id,
                ProductSupplier.supplier_id == supplier_id
            )
        )
        result = await db.execute(query)
        association = result.scalar_one_or_none()
        
        if association:
            # Delete the association
            await db.delete(association)
            await db.commit()
        
        # Return the product with its updated suppliers
        return await self.get_with_suppliers(db, product_id)
    
    async def get_by_category(
        self, 
        db: AsyncSession, 
        *, 
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Get products by category.
        """
        query = select(Product).where(Product.category == category).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_price_range(
        self, 
        db: AsyncSession, 
        *, 
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Get products within a price range.
        """
        conditions = []
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)
            
        query = select(Product)
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_stock_range(
        self, 
        db: AsyncSession, 
        *, 
        min_stock: Optional[int] = None,
        max_stock: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Get products within a stock quantity range.
        """
        conditions = []
        if min_stock is not None:
            conditions.append(Product.stock_quantity >= min_stock)
        if max_stock is not None:
            conditions.append(Product.stock_quantity <= max_stock)
            
        query = select(Product)
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_low_stock_products(
        self, 
        db: AsyncSession, 
        *, 
        threshold: int = 10,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Get products with stock quantity below the specified threshold.
        """
        query = select(Product).where(Product.stock_quantity < threshold).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count_by_category(self, db: AsyncSession) -> Dict[str, int]:
        """
        Count products by category.
        """
        query = select(Product.category, func.count(Product.id)).group_by(Product.category)
        result = await db.execute(query)
        return {category: count for category, count in result.all()}
    
    async def create_multi(
        self, 
        db: AsyncSession, 
        *, 
        objs_in: List[ProductCreate]
    ) -> List[Product]:
        """
        Create multiple products in a batch operation.
        """
        products = []
        for obj_in in objs_in:
            # Convert Pydantic model to dict
            obj_in_data = obj_in.model_dump(exclude_unset=True)
            db_obj = Product(**obj_in_data)
            db.add(db_obj)
            products.append(db_obj)
        
        await db.commit()
        # Refresh the objects to get generated values
        for product in products:
            await db.refresh(product)
        
        return products

    async def update_multi(
        self, 
        db: AsyncSession, 
        *, 
        updates: List[Dict[str, Any]]
    ) -> List[Product]:
        """
        Update multiple products in a batch operation.
        """
        updated_products = []
        for update_data in updates:
            if "id" not in update_data:
                continue
                
            product_id = update_data.pop("id")
            db_obj = await self.get(db, id=product_id)
            
            if db_obj:
                # Update product attributes
                for field, value in update_data.items():
                    if hasattr(db_obj, field):
                        setattr(db_obj, field, value)
                
                updated_products.append(db_obj)
        
        await db.commit()
        return updated_products

    async def delete_multi(
        self, 
        db: AsyncSession, 
        *, 
        ids: List[int]
    ) -> List[int]:
        """
        Delete multiple products in a batch operation.
        """
        deleted_ids = []
        for product_id in ids:
            db_obj = await self.get(db, id=product_id)
            if db_obj:
                await db.delete(db_obj)
                deleted_ids.append(product_id)
        
        await db.commit()
        return deleted_ids
    
    async def batch_create(
        self, 
        db: AsyncSession, 
        *, 
        objs_in: List[ProductCreate]
    ) -> List[Product]:
        """
        Create multiple products in a batch operation.
        """
        products = []
        for obj_in in objs_in:
            # Convert Pydantic model to dict
            obj_in_data = obj_in.model_dump()
            db_obj = Product(**obj_in_data)
            db.add(db_obj)
            products.append(db_obj)
        
        await db.commit()
        
        # Refresh all products to get their generated IDs
        for product in products:
            await db.refresh(product)
        
        return products
    
    async def delete(self, db: AsyncSession, *, id: Any) -> Product:
        """
        Delete a product by ID.
        """
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj