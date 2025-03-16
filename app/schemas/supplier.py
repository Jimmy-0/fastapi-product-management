# app/schemas/supplier.py
from typing import List, Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, validator, conlist


class SupplierBase(BaseModel):
    """Base schema for supplier data."""
    name: str = Field(..., min_length=2, max_length=100, description="Supplier name")
    contact_info: str = Field(..., description="Supplier contact information")
    credit_rating: int = Field(..., ge=0, le=5, description="Supplier credit rating (0-5 stars)")


class SupplierCreate(SupplierBase):
    """Schema for creating a new supplier."""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Supplier name")
    contact_info: Optional[str] = Field(None, description="Supplier contact information")
    credit_rating: Optional[int] = Field(None, ge=0, le=5, description="Supplier credit rating (0-5 stars)")


class SupplierResponse(SupplierBase):
    """Schema for supplier response."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class SupplierWithProductsResponse(SupplierResponse):
    """Schema for supplier response with products."""
    products: List = []  # This will be populated with ProductResponse objects


class SupplierListResponse(BaseModel):
    """Schema for paginated supplier list response."""
    items: List[SupplierResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SupplierBatchCreateRequest(BaseModel):
    """Schema for batch supplier creation request."""
    suppliers: Annotated[List[SupplierCreate], Field(min_length=1, max_length=100)]

    # suppliers: conlist(SupplierCreate, min_items=1, max_items=100)


class SupplierBatchUpdateRequest(BaseModel):
    """Schema for batch supplier update request."""
    supplier_ids: Annotated[List[int], Field(min_length=1, max_length=100)]
    # supplier_ids: conlist(int, min_items=1, max_items=100)
    update_data: SupplierUpdate


class SupplierBatchDeleteRequest(BaseModel):
    """Schema for batch supplier delete request."""
    supplier_ids: Annotated[List[int], Field(min_length=1, max_length=100)]
    # supplier_ids: conlist(int, min_items=1, max_items=100)