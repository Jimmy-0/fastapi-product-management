# app/repositories/supplier.py
from typing import Any, List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[Supplier, SupplierCreate, SupplierUpdate]):
    """
    Repository for Supplier entity with custom methods specific to suppliers.
    """
    
    def __init__(self):
        super().__init__(Supplier)
    
    async def get_with_products(self, db: AsyncSession, id: Any) -> Optional[Supplier]:
        """
        Get a supplier by ID with its products loaded.
        """
        query = select(Supplier).where(Supplier.id == id).options(
            selectinload(Supplier.products)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_multi_with_products(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        **kwargs
    ) -> List[Supplier]:
        """
        Get multiple suppliers with their products loaded, with pagination and filtering.
        """
        query = select(Supplier).options(
            selectinload(Supplier.products)
        )
        
        # Apply filters
        if kwargs:
            filter_conditions = []
            for key, value in kwargs.items():
                if hasattr(Supplier, key):
                    if key == "credit_rating" and value is not None:
                        if isinstance(value, dict):
                            if "min" in value and value["min"] is not None:
                                filter_conditions.append(Supplier.credit_rating >= value["min"])
                            if "max" in value and value["max"] is not None:
                                filter_conditions.append(Supplier.credit_rating <= value["max"])
                        else:
                            filter_conditions.append(Supplier.credit_rating == value)
                    elif value is not None:
                        filter_conditions.append(getattr(Supplier, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def search_suppliers(
        self,
        db: AsyncSession,
        *,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        **kwargs
    ) -> List[Supplier]:
        """
        Search for suppliers by name or contact information.
        """
        search_conditions = [
            Supplier.name.ilike(f"%{search_term}%"),
            Supplier.contact_info.ilike(f"%{search_term}%")
        ]
        
        query = select(Supplier).where(or_(*search_conditions))
        
        # Apply additional filters
        if kwargs:
            filter_conditions = []
            for key, value in kwargs.items():
                if hasattr(Supplier, key) and value is not None:
                    filter_conditions.append(getattr(Supplier, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Add product loading
        query = query.options(selectinload(Supplier.products))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_credit_rating(
        self, 
        db: AsyncSession, 
        *, 
        rating: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Supplier]:
        """
        Get suppliers by credit rating.
        """
        query = select(Supplier).where(Supplier.credit_rating == rating).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_credit_rating_range(
        self, 
        db: AsyncSession, 
        *, 
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Supplier]:
        """
        Get suppliers within a credit rating range.
        """
        conditions = []
        if min_rating is not None:
            conditions.append(Supplier.credit_rating >= min_rating)
        if max_rating is not None:
            conditions.append(Supplier.credit_rating <= max_rating)
            
        query = select(Supplier)
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_top_rated_suppliers(
        self, 
        db: AsyncSession, 
        *, 
        limit: int = 10
    ) -> List[Supplier]:
        """
        Get the top-rated suppliers.
        """
        query = select(Supplier).order_by(Supplier.credit_rating.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()