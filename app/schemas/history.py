# app/schemas/history.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PriceHistoryBase(BaseModel):
    """Base schema for price history data."""
    product_id: int = Field(..., gt=0, description="Product ID")
    old_price: float = Field(..., ge=0, description="Previous price")
    new_price: float = Field(..., ge=0, description="New price")
    timestamp: datetime = Field(..., description="Timestamp of the change")


class PriceHistoryCreate(PriceHistoryBase):
    """Schema for creating a new price history record."""
    pass


class PriceHistoryResponse(PriceHistoryBase):
    """Schema for price history response."""
    id: int
    product_id: int
    old_price: float
    new_price: float
    timestamp: datetime
    
    class Config:
        from_attributes = True 


class StockHistoryBase(BaseModel):
    """Base schema for stock history data."""
    product_id: int = Field(..., gt=0, description="Product ID")
    old_quantity: int = Field(..., ge=0, description="Previous stock quantity")
    new_quantity: int = Field(..., ge=0, description="New stock quantity")
    change_reason: Optional[str] = Field(None, description="Reason for the stock change")
    timestamp: datetime = Field(..., description="Timestamp of the change")


class StockHistoryCreate(StockHistoryBase):
    """Schema for creating a new stock history record."""
    pass


class StockHistoryResponse(StockHistoryBase):
    """Schema for stock history response."""
    id: int

    model_config = {"from_attributes": True}

class HistoryListParams(BaseModel):
    """Schema for history list query parameters."""
    product_id: int = Field(..., gt=0, description="Product ID")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    skip: int = Field(0, ge=0, description="Skip first N items")
    limit: int = Field(100, ge=1, le=100, description="Limit number of items returned")


class PriceHistoryListResponse(BaseModel):
    """Schema for paginated price history list response."""
    items: List[PriceHistoryResponse]
    total: int
    product_id: int
    page: int
    page_size: int
    pages: int


class StockHistoryListResponse(BaseModel):
    """Schema for paginated stock history list response."""
    items: List[StockHistoryResponse]
    total: int
    product_id: int
    page: int
    page_size: int
    pages: int

    model_config = {"from_attributes": True}


class CombinedHistoryResponse(BaseModel):
    """Schema for combined price and stock history response."""
    product_id: int
    product_name: str
    price_history: List[PriceHistoryResponse]
    stock_history: List[StockHistoryResponse]
    