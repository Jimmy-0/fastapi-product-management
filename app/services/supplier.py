# app/services/supplier.py
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.supplier import SupplierRepository
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse


class SupplierService:
    """
    Service for handling business logic related to suppliers.
    """
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def get_supplier(self, db: AsyncSession, id: int) -> SupplierResponse:
        """
        Get a supplier by ID with products loaded.
        """
        supplier = await self.supplier_repository.get_with_products(db, id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID {id} not found"
            )
        return supplier
    
    async def get_suppliers(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc",
        **filters
    ) -> List[SupplierResponse]:
        """
        Get multiple suppliers with filtering, sorting and pagination.
        """
        return await self.supplier_repository.get_multi_with_products(
            db, 
            skip=skip, 
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            **filters
        )
    
    async def search_suppliers(
        self,
        db: AsyncSession,
        *,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[SupplierResponse]:
        """
        Search for suppliers by name or contact information.
        """
        return await self.supplier_repository.search_suppliers(
            db,
            search_term=search_term,
            skip=skip,
            limit=limit,
            **filters
        )
    
    async def create_supplier(self, db: AsyncSession, *, supplier_in: SupplierCreate) -> SupplierResponse:
        """
        Create a new supplier.
        """
        # Validate supplier data (check credit rating is in range, etc.)
        if supplier_in.credit_rating < 0 or supplier_in.credit_rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit rating must be between 0 and 5"
            )
        
        # Create the supplier
        supplier = await self.supplier_repository.create(db, obj_in=supplier_in)
        return supplier
    
    async def update_supplier(
        self,
        db: AsyncSession,
        *,
        id: int,
        supplier_in: SupplierUpdate
    ) -> SupplierResponse:
        """
        Update a supplier.
        """
        # Get the current supplier
        supplier = await self.supplier_repository.get(db, id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID {id} not found"
            )
        
        # Validate credit rating if provided
        if supplier_in.credit_rating is not None and (supplier_in.credit_rating < 0 or supplier_in.credit_rating > 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit rating must be between 0 and 5"
            )
        
        # Update the supplier
        updated_supplier = await self.supplier_repository.update(
            db,
            db_obj=supplier,
            obj_in=supplier_in
        )
        
        return updated_supplier
    
    async def delete_supplier(self, db: AsyncSession, *, id: int) -> SupplierResponse:
        """
        Delete a supplier.
        """
        supplier = await self.supplier_repository.get(db, id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID {id} not found"
            )
        
        # Delete the supplier
        deleted_supplier = await self.supplier_repository.delete(db, id=id)
        return deleted_supplier
    
    async def batch_create_suppliers(
        self,
        db: AsyncSession,
        *,
        suppliers_in: List[SupplierCreate]
    ) -> List[SupplierResponse]:
        """
        Create multiple suppliers in a batch.
        """
        # Validate credit ratings
        for supplier_in in suppliers_in:
            if supplier_in.credit_rating < 0 or supplier_in.credit_rating > 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Credit rating must be between 0 and 5"
                )
        
        # Create the suppliers
        suppliers = await self.supplier_repository.batch_create(db, objs_in=suppliers_in)
        return suppliers
    
    async def batch_update_suppliers(
        self,
        db: AsyncSession,
        *,
        ids: List[int],
        update_data: SupplierUpdate
    ) -> List[SupplierResponse]:
        """
        Update multiple suppliers in a batch.
        """
        # Validate credit rating if provided
        if update_data.credit_rating is not None and (update_data.credit_rating < 0 or update_data.credit_rating > 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit rating must be between 0 and 5"
            )
        
        # Update all suppliers
        updated_suppliers = await self.supplier_repository.batch_update(
            db,
            ids=ids,
            obj_in=update_data
        )
        
        return updated_suppliers
    
    async def batch_delete_suppliers(
        self,
        db: AsyncSession,
        *,
        ids: List[int]
    ) -> List[SupplierResponse]:
        """
        Delete multiple suppliers in a batch.
        """
        # Delete the suppliers
        deleted_suppliers = await self.supplier_repository.batch_delete(db, ids=ids)
        return deleted_suppliers
    
    async def get_top_rated_suppliers(
        self,
        db: AsyncSession,
        *,
        limit: int = 10
    ) -> List[SupplierResponse]:
        """
        Get the top-rated suppliers.
        """
        return await self.supplier_repository.get_top_rated_suppliers(db, limit=limit)
    
    async def get_by_credit_rating(
        self,
        db: AsyncSession,
        *,
        rating: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupplierResponse]:
        """
        Get suppliers by credit rating.
        """
        if rating < 0 or rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit rating must be between 0 and 5"
            )
            
        return await self.supplier_repository.get_by_credit_rating(
            db,
            rating=rating,
            skip=skip,
            limit=limit
        )
    
    async def get_by_credit_rating_range(
        self,
        db: AsyncSession,
        *,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupplierResponse]:
        """
        Get suppliers within a credit rating range.
        """
        if min_rating is not None and (min_rating < 0 or min_rating > 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum credit rating must be between 0 and 5"
            )
            
        if max_rating is not None and (max_rating < 0 or max_rating > 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum credit rating must be between 0 and 5"
            )
            
        if min_rating is not None and max_rating is not None and min_rating > max_rating:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum credit rating cannot be greater than maximum credit rating"
            )
            
        return await self.supplier_repository.get_by_credit_rating_range(
            db,
            min_rating=min_rating,
            max_rating=max_rating,
            skip=skip,
            limit=limit
        )