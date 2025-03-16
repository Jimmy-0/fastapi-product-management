from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Supplier schemas
class SupplierBase(BaseModel):
    name: str
    contact_info: Optional[str] = None
    credit_rating: float = Field(ge=0, le=5, description="Credit rating from 0 to 5 stars")

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase):
    id: int

    class Config:
        orm_mode = True

# Product schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = None
    stock_quantity: int = Field(0, ge=0)
    category: Optional[str] = None
    discount: float = Field(0, ge=0, le=100)

class ProductCreate(ProductBase):
    supplier_ids: Optional[List[int]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    discount: Optional[float] = Field(None, ge=0, le=100)
    supplier_ids: Optional[List[int]] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    suppliers: List[Supplier] = []

    class Config:
        orm_mode = True

# Batch operations schemas
class ProductBatchCreate(BaseModel):
    products: List[ProductCreate]

class ProductBatchUpdate(BaseModel):
    product_updates: List[dict] = Field(..., description="List of {id: product_id, ...fields_to_update}")

class ProductBatchDelete(BaseModel):
    product_ids: List[int]

# History schemas
class PriceStockHistoryBase(BaseModel):
    product_id: int
    old_price: Optional[float] = None
    new_price: Optional[float] = None
    old_stock: Optional[int] = None
    new_stock: Optional[int] = None

class PriceStockHistory(PriceStockHistoryBase):
    id: int
    change_timestamp: datetime

    class Config:
        orm_mode = True

# Query parameters schemas
class ProductFilterParams(BaseModel):
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None
    search_term: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields for future extensibility