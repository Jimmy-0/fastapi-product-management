# app/api/v1/endpoints/product.py
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CommonDependencies
from app.core.database import get_db
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductBatchCreateRequest,
    ProductBatchUpdateRequest,
    ProductBatchDeleteRequest,
    ProductBatchUpdateItem
)

from app.schemas.supplier import SupplierResponse

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
async def get_products(
    commons: CommonDependencies = Depends(),
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(10, ge=1, le=100, description="Limit number of items returned"),
    page: Optional[int] = Query(None, ge=1, description="Page number"),
    size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by product name (case-insensitive)"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_stock: Optional[int] = Query(None, ge=0, description="Minimum stock quantity"),
    max_stock: Optional[int] = Query(None, ge=0, description="Maximum stock quantity"),
    sort: Optional[str] = Query(None, description="Sort by field"),
    order: Optional[str] = Query("asc", description="Sort order (asc or desc)")
) -> ProductListResponse:
    """
    Get list of products with filtering, sorting and pagination.
    """
    # Prepare filters
    filters = {}

    # Priority fix for pagination:
    # Always prioritize page/size parameters over skip/limit
    actual_size = size if size is not None else limit
    actual_skip = skip # default skip if page is not provided
    if page is not None:
        actual_skip = (page - 1) * actual_size
        limit = actual_size  # Ensure we use the actual_size for the limit
        skip = actual_skip # update skip to the calculated value


    # Apply other filters as before
    if category:
        filters["category"] = category

    if min_price is not None or max_price is not None:
        filters["price_range"] = {"min": min_price, "max": max_price}

    if min_stock is not None or max_stock is not None:
        filters["stock_range"] = {"min": min_stock, "max": max_stock}

    # Get products with the correct pagination parameters
    if name:
        products = await commons.product_service.search_products(
            commons.db,
            search_term=name,
            skip=skip,
            limit=limit,  # Use the calculated limit
            **filters
        )
    else:
        products = await commons.product_service.get_products(
            commons.db,
            skip=skip,
            limit=limit,  # Use the calculated limit
            sort_by=sort,
            sort_order=order,
            **filters
        )

    # Count total products (without pagination)
    total = await commons.product_service.product_repository.count(commons.db, **filters)

    # Use consistent calculation for response
    current_page = page if page is not None else (actual_skip // actual_size + 1 if actual_size > 0 else 1)
    current_size = actual_size

    return ProductListResponse(
        items=products,
        total=total,
        page=current_page,
        size=current_size,
        pages=(total + current_size - 1) // current_size if current_size > 0 else 1
    )

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    commons: CommonDependencies = Depends()
) -> ProductResponse:
    """
    Create a new product.
    """
    return await commons.product_service.create_product(commons.db, product_in=product_in)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    commons: CommonDependencies = Depends()
) -> ProductResponse:
    """
    Get a product by ID.
    """
    product = await commons.product_service.get_product(commons.db, id=product_id)
    # Ensure suppliers is properly initialized if empty
    if not hasattr(product, 'suppliers') or product.suppliers is None:
        product.suppliers = []
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_in: ProductUpdate,
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    commons: CommonDependencies = Depends()
) -> ProductResponse:
    """
    Update a product by ID.
    """
    update_data = product_in.model_dump(exclude_unset=True)
    change_reason = update_data.pop("change_reason", None)

    return await commons.product_service.update_product(
        commons.db,
        id=product_id,
        product_in=update_data,
        change_reason=change_reason
    )


@router.delete("/{product_id}", response_model=ProductResponse)
async def delete_product(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    commons: CommonDependencies = Depends()
) -> ProductResponse:
    """
    Delete a product by ID.
    """
    return await commons.product_service.delete_product(commons.db, id=product_id)


@router.post("/batch", response_model=Dict[str, List[ProductResponse]], status_code=status.HTTP_201_CREATED)
async def batch_create_products(
    batch_create_request: ProductBatchCreateRequest,
    commons: CommonDependencies = Depends()
) -> Dict[str, List[ProductResponse]]:
    """Create multiple products in a batch."""
    created_products = await commons.product_service.batch_create_products(
        commons.db,
        products_in=batch_create_request.products
    )
    return {"products": created_products}


@router.put("/batch", response_model=Dict[str, List[ProductResponse]])
async def batch_update_products(
    batch_update_request: ProductBatchUpdateRequest,
    commons: CommonDependencies = Depends()
) -> Dict[str, List[ProductResponse]]:
    """
    Update multiple products in a batch.
    
    Each product update must include the product ID and at least one field to update.
    """
    # Convert each update item to a dict including the ID
    updates = []
    for update_item in batch_update_request.updates:
        # Convert to dict but keep the ID in the dict
        update_dict = update_item.model_dump(exclude_unset=True)
        updates.append(update_dict)
    
    try:
        updated_products = await commons.product_service.batch_update_products(
            commons.db,
            updates=updates
        )
        
        return {"updated": updated_products}
    except HTTPException as e:
        # If non-existent products were detected, just filter them out silently
        # This maintains backward compatibility with the original implementation
        if e.status_code == 404 and "not found" in e.detail.lower():
            # Find the products that were successfully updated
            # To maintain compatibility, silently skip products that don't exist
            updated_products = await commons.product_service.batch_update_products_silently(
                commons.db,
                updates=updates
            )
            return {"updated": updated_products}
        else:
            raise

@router.delete("/batch", response_model=Dict[str, List[int]])
async def batch_delete_products(
    product_ids: str = Query(..., description="Comma-separated product IDs to delete"),
    commons: CommonDependencies = Depends()
) -> Dict[str, List[int]]:
    """
    Delete multiple products by IDs.
    
    The product_ids should be provided as a comma-separated list in the query string.
    Example: /api/v1/products/batch?product_ids=1,2,3
    """
    try:
        # Parse the comma-separated IDs
        ids = [int(id_str.strip()) for id_str in product_ids.split(",") if id_str.strip()]
        
        if not ids:
            raise HTTPException(
                status_code=400,
                detail="No valid product IDs provided"
            )
        
        # Get deleted products (maintain existing behavior)
        try:
            deleted_products = await commons.product_service.batch_delete_products(
                commons.db,
                ids=ids
            )
            
            # Return just the IDs of deleted products
            return {"deleted": [p.id for p in deleted_products]}
        except HTTPException as e:
            # If non-existent products were detected, just filter them out silently
            # This maintains backward compatibility with the original implementation
            if e.status_code == 404 and "not found" in e.detail.lower():
                # Find the IDs that were successfully deleted
                # Implementation depends on service returning specific messages
                # This is a workaround - better to update the service method
                deleted_products = await commons.product_service.batch_delete_products_silently(
                    commons.db,
                    ids=ids
                )
                return {"deleted": [p.id for p in deleted_products]}
            else:
                raise
            
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid product IDs format. Must be comma-separated integers."
        )

async def batch_delete_products_silently(
    self,
    db: AsyncSession,
    *,
    ids: List[int]
) -> List[ProductResponse]:
    """
    Delete multiple products in a batch, silently skipping any that don't exist.
    This method maintains compatibility with the original implementation.
    """
    deleted_products = []
    
    for product_id in ids:
        product = await self.product_repository.get(db, id=product_id)
        if product:
            # Keep a copy of the product before deletion
            deleted_products.append(product)
            await self.product_repository.delete(db, id=product_id)
    
    return deleted_products

@router.get("/low-stock", response_model=List[ProductResponse])
async def get_low_stock_products(
    threshold: int = Query(10, ge=0, description="Stock threshold"),
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit number of items returned"),
    commons: CommonDependencies = Depends()
) -> List[ProductResponse]:
    """
    Get products with stock quantity below the specified threshold.
    """
    return await commons.product_service.get_low_stock_products(
        commons.db,
        threshold=threshold,
        skip=skip,
        limit=limit
    )


@router.post("/{product_id}/suppliers/{supplier_id}", response_model=ProductResponse)
async def add_supplier_to_product(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    supplier_id: int = Path(..., gt=0, description="The ID of the supplier"),
    commons: CommonDependencies = Depends()
) -> ProductResponse:
    """
    Add a supplier to a product.
    """
    return await commons.product_service.add_supplier_to_product(
        commons.db,
        product_id=product_id,
        supplier_id=supplier_id
    )


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    query: str = Query(..., description="Search query"),
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(10, ge=1, le=100, description="Limit number of items returned"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_stock: Optional[int] = Query(None, ge=0, description="Minimum stock quantity"),
    max_stock: Optional[int] = Query(None, ge=0, description="Maximum stock quantity"),
    commons: CommonDependencies = Depends()
):
    """
    Search for products by name or description with filtering options.
    """
    # Prepare filters
    filters = {}
    
    if category:
        filters["category"] = category

    if min_price is not None or max_price is not None:
        filters["price_range"] = {"min": min_price, "max": max_price}

    if min_stock is not None or max_stock is not None:
        filters["stock_range"] = {"min": min_stock, "max": max_stock}
    
    # Get filtered search results
    products = await commons.product_service.search_products(
        commons.db,
        search_term=query,
        skip=skip,
        limit=limit,
        **filters
    )

    # Count total matching products with the same filters
    total = await commons.product_service.count_search_results(
        commons.db, 
        search_term=query,
        **filters
    )

    return ProductListResponse(
        items=products,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit,
        pages=(total + limit - 1) // limit if limit > 0 else 1
    )


@router.delete("/{product_id}/suppliers/{supplier_id}", response_model=ProductResponse)
async def remove_supplier_from_product(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    supplier_id: int = Path(..., gt=0, description="The ID of the supplier"),
    commons: CommonDependencies = Depends()
) -> ProductResponse:
    """
    Remove a supplier from a product.
    """
    return await commons.product_service.remove_supplier_from_product(
        commons.db,
        product_id=product_id,
        supplier_id=supplier_id
    )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_product_statistics(
    commons: CommonDependencies = Depends()
) -> Dict[str, Any]:
    """
    Get product statistics.
    """
    return await commons.product_service.get_product_statistics(commons.db)


@router.get("/{product_id}/suppliers", response_model=Dict[str, List[SupplierResponse]])
async def get_product_suppliers(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    commons: CommonDependencies = Depends()
) -> Dict[str, List[SupplierResponse]]:
    """
    Get all suppliers for a product.
    """
    suppliers = await commons.product_service.get_product_suppliers(
        commons.db,
        product_id=product_id
    )

    supplier_dicts = [
        {
            "id": supplier.id,
            "name": supplier.name,
            "contact_info": supplier.contact_info,
            "credit_rating": supplier.credit_rating,
            "created_at": supplier.created_at,
            "updated_at": supplier.updated_at
        }
        for supplier in suppliers
    ]

    supplier_responses = [SupplierResponse.model_validate(supplier_dict) 
                          for supplier_dict in supplier_dicts]
    
    return {"suppliers": supplier_responses}