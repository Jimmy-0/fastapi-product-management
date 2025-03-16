# app/api/v1/endpoints/history.py
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CommonDependencies
from app.core.database import get_db
from app.schemas.history import (
    PriceHistoryResponse,
    StockHistoryResponse,
    PriceHistoryListResponse,
    StockHistoryListResponse,
    CombinedHistoryResponse
)

router = APIRouter()


@router.get("/price/{product_id}", response_model=PriceHistoryListResponse)
async def get_price_history(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit number of items returned"),
    commons: CommonDependencies = Depends()
) -> PriceHistoryListResponse:
    """
    Get price history for a specific product.
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be later than end date"
        )
    
    # Get the product to ensure it exists and to get its name
    product = await commons.product_service.get_product(commons.db, id=product_id)
    
    if start_date or end_date:
        history_items = await commons.history_service.get_price_history_by_date_range(
            commons.db,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
    else:
        history_items = await commons.history_service.get_price_history(
            commons.db,
            product_id=product_id,
            skip=skip,
            limit=limit
        )
    
    # Count total history records
    total = len(await commons.history_service.price_history_repository.get_by_product_id(
        commons.db,
        product_id=product_id,
        limit=1000  # Set a reasonable limit for counting
    ))
    
    return PriceHistoryListResponse(
        items=[PriceHistoryResponse.model_validate(item) for item in history_items],
        total=total,
        product_id=product_id,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        pages=(total + limit - 1) // limit if limit > 0 else 1

    )


@router.get("/stock/{product_id}", response_model=StockHistoryListResponse)
async def get_stock_history(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit number of items returned"),
    commons: CommonDependencies = Depends()
) -> StockHistoryListResponse:
    """
    Get stock history for a specific product.
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be later than end date"
        )
    
    # Get the product to ensure it exists and to get its name
    product = await commons.product_service.get_product(commons.db, id=product_id)
    
    if start_date or end_date:
        history_items = await commons.history_service.get_stock_history_by_date_range(
            commons.db,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
    else:
        history_items = await commons.history_service.get_stock_history(
            commons.db,
            product_id=product_id,
            skip=skip,
            limit=limit
        )
    
    # Count total history records
    total = len(await commons.history_service.stock_history_repository.get_by_product_id(
        commons.db,
        product_id=product_id,
        limit=1000  # Set a reasonable limit for counting
    ))
    
    return StockHistoryListResponse(
        items=[StockHistoryResponse.model_validate(item) for item in history_items],
        total=total,
        product_id=product_id,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        pages=(total + limit - 1) // limit if limit > 0 else 1
    )


@router.get("/combined/{product_id}", response_model=CombinedHistoryResponse)
async def get_combined_history(
    product_id: int = Path(..., gt=0, description="The ID of the product"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit number of items returned"),
    commons: CommonDependencies = Depends()
) -> CombinedHistoryResponse:
    """
    Get combined price and stock history for a specific product.
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be later than end date"
        )
    
    return await commons.history_service.get_combined_history(
        commons.db,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )