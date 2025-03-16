# app/services/history.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.history import PriceHistoryRepository, StockHistoryRepository
from app.repositories.product import ProductRepository
from app.schemas.history import PriceHistoryResponse, StockHistoryResponse


class HistoryService:
    """
    Service for handling business logic related to price and stock history.
    """
    
    def __init__(
        self,
        price_history_repository: PriceHistoryRepository,
        stock_history_repository: StockHistoryRepository,
        product_repository: ProductRepository
    ):
        self.price_history_repository = price_history_repository
        self.stock_history_repository = stock_history_repository
        self.product_repository = product_repository
    
    async def get_price_history(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[PriceHistoryResponse]:
        """
        Get price history records for a specific product.
        """
        # Check if product exists
        product = await self.product_repository.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        return await self.price_history_repository.get_by_product_id(
            db,
            product_id=product_id,
            skip=skip,
            limit=limit
        )
    
    async def get_price_history_by_date_range(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[PriceHistoryResponse]:
        """
        Get price history records for a specific product within a date range.
        """
        # Check if product exists
        product = await self.product_repository.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        return await self.price_history_repository.get_by_date_range(
            db,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
    
    async def get_stock_history(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockHistoryResponse]:
        """
        Get stock history records for a specific product.
        """
        # Check if product exists
        product = await self.product_repository.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        return await self.stock_history_repository.get_by_product_id(
            db,
            product_id=product_id,
            skip=skip,
            limit=limit
        )
    
    async def get_stock_history_by_date_range(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockHistoryResponse]:
        """
        Get stock history records for a specific product within a date range.
        """
        # Check if product exists
        product = await self.product_repository.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        return await self.stock_history_repository.get_by_date_range(
            db,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
    
    async def add_price_change(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        old_price: float,
        new_price: float
    ) -> PriceHistoryResponse:
        """
        Add a new price change record.
        """
        # Check if product exists
        product = await self.product_repository.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        # Add price change record
        return await self.price_history_repository.add_price_change(
            db,
            product_id=product_id,
            old_price=old_price,
            new_price=new_price
        )
    
    async def add_stock_change(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        old_quantity: int,
        new_quantity: int,
        change_reason: Optional[str] = None
    ) -> StockHistoryResponse:
        """
        Add a new stock change record.
        """
        # Check if product exists
        product = await self.product_repository.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        # Add stock change record
        return await self.stock_history_repository.add_stock_change(
            db,
            product_id=product_id,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            change_reason=change_reason
        )
    
    async def get_combined_history(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get combined price and stock history for a product.
        """
        # Check if product exists
        product = await self.product_repository.get(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        # Get price history
        price_history = await self.price_history_repository.get_by_date_range(
            db,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        # Get stock history
        stock_history = await self.stock_history_repository.get_by_date_range(
            db,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        # Combine the results
        return {
            "product_id": product_id,
            "product_name": product.name,
            "price_history": price_history,
            "stock_history": stock_history
        }