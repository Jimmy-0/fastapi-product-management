# app/repositories/history.py
from datetime import datetime
from typing import Any, List, Optional, Union
from sqlalchemy import select, and_, between
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import PriceHistory, StockHistory
from app.schemas.history import PriceHistoryCreate, StockHistoryCreate
from app.repositories.base import BaseRepository


class PriceHistoryRepository(BaseRepository[PriceHistory, PriceHistoryCreate, PriceHistoryCreate]):
    """
    Repository for PriceHistory entity.
    """
    
    def __init__(self):
        super().__init__(PriceHistory)
    
    async def get_by_product_id(
        self, 
        db: AsyncSession, 
        *, 
        product_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[PriceHistory]:
        """
        Get price history records for a specific product.
        """
        query = select(PriceHistory).where(
            PriceHistory.product_id == product_id
        ).order_by(
            PriceHistory.timestamp.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_date_range(
        self, 
        db: AsyncSession, 
        *, 
        product_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[PriceHistory]:
        """
        Get price history records for a specific product within a date range.
        """
        conditions = [PriceHistory.product_id == product_id]
        
        if start_date and end_date:
            conditions.append(between(PriceHistory.timestamp, start_date, end_date))
        elif start_date:
            conditions.append(PriceHistory.timestamp >= start_date)
        elif end_date:
            conditions.append(PriceHistory.timestamp <= end_date)
        
        query = select(PriceHistory).where(
            and_(*conditions)
        ).order_by(
            PriceHistory.timestamp.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def add_price_change(
        self, 
        db: AsyncSession, 
        *, 
        product_id: int,
        old_price: float,
        new_price: float
    ) -> PriceHistory:
        """
        Add a new price change record.
        """
        price_history = PriceHistory(
            product_id=product_id,
            old_price=old_price,
            new_price=new_price,
            timestamp=datetime.utcnow()
        )
        db.add(price_history)
        await db.commit()
        await db.refresh(price_history)
        return price_history


class StockHistoryRepository(BaseRepository[StockHistory, StockHistoryCreate, StockHistoryCreate]):
    """
    Repository for StockHistory entity.
    """
    
    def __init__(self):
        super().__init__(StockHistory)
    
    async def get_by_product_id(
        self, 
        db: AsyncSession, 
        *, 
        product_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockHistory]:
        """
        Get stock history records for a specific product.
        """
        query = select(StockHistory).where(
            StockHistory.product_id == product_id
        ).order_by(
            StockHistory.timestamp.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_date_range(
        self, 
        db: AsyncSession, 
        *, 
        product_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockHistory]:
        """
        Get stock history records for a specific product within a date range.
        """
        conditions = [StockHistory.product_id == product_id]
        
        if start_date and end_date:
            conditions.append(between(StockHistory.timestamp, start_date, end_date))
        elif start_date:
            conditions.append(StockHistory.timestamp >= start_date)
        elif end_date:
            conditions.append(StockHistory.timestamp <= end_date)
        
        query = select(StockHistory).where(
            and_(*conditions)
        ).order_by(
            StockHistory.timestamp.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def add_stock_change(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        old_quantity: int,
        new_quantity: int,
        change_reason: Optional[str] = None
    ) -> StockHistory:
        """
        Add a stock quantity change record.
        """
        stock_history = StockHistory(
            product_id=product_id,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            # change_type="Manual Update",
            change_reason=change_reason,  # Make sure this gets stored
            timestamp=datetime.utcnow()
        )
        db.add(stock_history)
        await db.commit()
        await db.refresh(stock_history)
        return stock_history