# app/api/v1/endpoints/supplier.py
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CommonDependencies
from app.core.database import get_db
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse,
    SupplierBatchCreateRequest,
    SupplierBatchUpdateRequest,
    SupplierBatchDeleteRequest,
)

router = APIRouter()


@router.get("/", response_model=SupplierListResponse)
async def get_suppliers(
    commons: CommonDependencies = Depends(),
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit number of items returned"),
    name: Optional[str] = Query(None, description="Filter by supplier name (case-insensitive)"),
    min_rating: Optional[int] = Query(None, ge=0, le=5, description="Minimum credit rating"),
    max_rating: Optional[int] = Query(None, ge=0, le=5, description="Maximum credit rating"),
    sort_by: Optional[str] = Query(None, description="Sort by field"),
    sort_order: Optional[str] = Query("asc", description="Sort order (asc or desc)")
) -> SupplierListResponse:
    """
    Get list of suppliers with filtering, sorting and pagination.
    """
    # Prepare filters
    filters = {}
    
    if min_rating is not None or max_rating is not None:
        filters["credit_rating"] = {"min": min_rating, "max": max_rating}
    
    # Search by name or get all with filters
    if name:
        suppliers = await commons.supplier_service.search_suppliers(
            commons.db,
            search_term=name,
            skip=skip,
            limit=limit,
            **filters
        )
    else:
        suppliers = await commons.supplier_service.get_suppliers(
            commons.db,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            **filters
        )
    
    # Count total suppliers (without pagination)
    total = await commons.supplier_service.supplier_repository.count(commons.db, **filters)
    
    # Use model_dump to convert SQLAlchemy models to dictionaries first
    supplier_dicts = [
        {
            "id": supplier.id,
            "name": supplier.name,
            "contact_info": supplier.contact_info,
            "credit_rating": supplier.credit_rating,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at
            # Add any other fields that exist in your model
        }
        for supplier in suppliers
    ]
    
    # Now validate the dictionaries
    supplier_responses = [SupplierResponse.model_validate(supplier_dict) for supplier_dict in supplier_dicts]
    
    return SupplierListResponse(
        items=supplier_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        pages=(total + limit - 1) // limit if limit > 0 else 1
    )



@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_in: SupplierCreate,
    commons: CommonDependencies = Depends()
) -> SupplierResponse:
    """
    Create a new supplier.
    """
    return await commons.supplier_service.create_supplier(commons.db, supplier_in=supplier_in)


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int = Path(..., gt=0, description="The ID of the supplier"),
    commons: CommonDependencies = Depends()
) -> SupplierResponse:
    """
    Get a supplier by ID.
    """
    return await commons.supplier_service.get_supplier(commons.db, id=supplier_id)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_in: SupplierUpdate,
    supplier_id: int = Path(..., gt=0, description="The ID of the supplier"),
    commons: CommonDependencies = Depends()
) -> SupplierResponse:
    """
    Update a supplier by ID.
    """
    return await commons.supplier_service.update_supplier(
        commons.db,
        id=supplier_id,
        supplier_in=supplier_in
    )


@router.delete("/{supplier_id}", response_model=SupplierResponse)
async def delete_supplier(
    supplier_id: int = Path(..., gt=0, description="The ID of the supplier"),
    commons: CommonDependencies = Depends()
) -> SupplierResponse:
    """
    Delete a supplier by ID.
    """
    return await commons.supplier_service.delete_supplier(commons.db, id=supplier_id)


@router.post("/batch/create", response_model=List[SupplierResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_suppliers(
    batch_create_request: SupplierBatchCreateRequest,
    commons: CommonDependencies = Depends()
) -> List[SupplierResponse]:
    """
    Create multiple suppliers in a batch.
    """
    return await commons.supplier_service.batch_create_suppliers(
        commons.db,
        suppliers_in=batch_create_request.suppliers
    )


@router.put("/batch/update", response_model=List[SupplierResponse])
async def batch_update_suppliers(
    batch_update_request: SupplierBatchUpdateRequest,
    commons: CommonDependencies = Depends()
) -> List[SupplierResponse]:
    """
    Update multiple suppliers in a batch.
    """
    return await commons.supplier_service.batch_update_suppliers(
        commons.db,
        ids=batch_update_request.supplier_ids,
        update_data=batch_update_request.update_data
    )


@router.post("/batch/delete", response_model=List[SupplierResponse])
async def batch_delete_suppliers(
    batch_delete_request: SupplierBatchDeleteRequest,
    commons: CommonDependencies = Depends()
) -> List[SupplierResponse]:
    """
    Delete multiple suppliers in a batch.
    """
    return await commons.supplier_service.batch_delete_suppliers(
        commons.db,
        ids=batch_delete_request.supplier_ids
    )


@router.get("/top-rated", response_model=List[SupplierResponse])
async def get_top_rated_suppliers(
    limit: int = Query(10, ge=1, le=100, description="Number of suppliers to return"),
    commons: CommonDependencies = Depends()
) -> List[SupplierResponse]:
    """
    Get the top-rated suppliers.
    """
    return await commons.supplier_service.get_top_rated_suppliers(
        commons.db,
        limit=limit
    )