#app/shcemas/product.py
from typing import List, Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.schemas.supplier import SupplierResponse


class ProductBase(BaseModel):
    """Base schema for product data."""
    name: str = Field(..., min_length=3, max_length=100, description="Product name")
    price: float = Field(..., gt=0, description="Product price")
    description: Optional[str] = Field(None, description="Product description")
    stock_quantity: int = Field(..., ge=0, description="Available stock quantity")
    category: Optional[str] = Field(None, description="Product category")
    discount: Optional[float] = Field(0, ge=0, le=100, description="Discount percentage (0-100)")

    @field_validator('price')
    def validate_price(cls, v):
        if v is None:
            return v
            
        if v < 0:
            raise ValueError("Price cannot be negative")
        
        # Check decimal places
        str_value = str(v)
        if '.' in str_value:
            decimals = len(str_value.split('.')[1])
            if decimals > 2:
                raise ValueError("Price cannot have more than 2 decimal places")
        
        return v


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=3, max_length=100, description="Product name")
    price: Optional[float] = Field(None, gt=0, description="Product price")
    description: Optional[str] = Field(None, description="Product description")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available stock quantity")
    category: Optional[str] = Field(None, description="Product category")
    discount: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage (0-100)")
    change_reason: Optional[str] = Field(None, description="Reason for the update")

    @field_validator("price")
    def validate_price(cls, v):
        """Validate price to ensure it has at most 2 decimal places."""
        if v is not None and v * 100 != int(v * 100):
            raise ValueError("Price must have at most 2 decimal places")
        return v


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    created_at: datetime
    updated_at: datetime
    suppliers: List[SupplierResponse] = Field(default=[])

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list response."""
    items: List[ProductResponse]
    total: int
    page: int
    size: int
    pages: int


class ProductBatchUpdateItem(BaseModel):
    """Schema for a single product update in a batch request"""
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    discount: Optional[float] = None
    category: Optional[str] = None
    change_reason: Optional[str] = None
    
    model_config = ConfigDict(extra="ignore")



class ProductBatchCreateRequest(BaseModel):
    """Schema for batch product creation request."""
    products: List[ProductCreate]


class ProductBatchUpdateRequest(BaseModel):
    """Schema for batch product update request."""
    updates: List[ProductBatchUpdateItem]


class ProductBatchDeleteRequest(BaseModel):
    """Schema for batch product delete request."""
    product_ids: List[int]

class ProductBatchResponse(BaseModel):
    """Response schema for batch product operations."""
    products: List[ProductResponse]


class ProductBatchUpdateResponse(BaseModel):
    """Response schema for batch product update."""
    updated: List[ProductResponse]


class ProductBatchDeleteResponse(BaseModel):
    """Response schema for batch product deletion."""
    deleted: List[int]