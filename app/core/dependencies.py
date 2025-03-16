# app/core/dependencies.py
from typing import Generator, Callable, Any
from functools import lru_cache
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.product import ProductRepository
from app.repositories.supplier import SupplierRepository
from app.repositories.history import PriceHistoryRepository, StockHistoryRepository
from app.services.product import ProductService
from app.services.supplier import SupplierService
from app.services.history import HistoryService


# Repository dependencies
@lru_cache
def get_product_repository() -> ProductRepository:
    return ProductRepository()


@lru_cache
def get_supplier_repository() -> SupplierRepository:
    return SupplierRepository()


@lru_cache
def get_price_history_repository() -> PriceHistoryRepository:
    return PriceHistoryRepository()


@lru_cache
def get_stock_history_repository() -> StockHistoryRepository:
    return StockHistoryRepository()


# Service dependencies
@lru_cache
def get_product_service(
    product_repository: ProductRepository = Depends(get_product_repository),
    price_history_repository: PriceHistoryRepository = Depends(get_price_history_repository),
    stock_history_repository: StockHistoryRepository = Depends(get_stock_history_repository)
) -> ProductService:
    return ProductService(
        product_repository=product_repository,
        price_history_repository=price_history_repository,
        stock_history_repository=stock_history_repository
    )


@lru_cache
def get_supplier_service(
    supplier_repository: SupplierRepository = Depends(get_supplier_repository)
) -> SupplierService:
    return SupplierService(supplier_repository=supplier_repository)


@lru_cache
def get_history_service(
    price_history_repository: PriceHistoryRepository = Depends(get_price_history_repository),
    stock_history_repository: StockHistoryRepository = Depends(get_stock_history_repository),
    product_repository: ProductRepository = Depends(get_product_repository)
) -> HistoryService:
    return HistoryService(
        price_history_repository=price_history_repository,
        stock_history_repository=stock_history_repository,
        product_repository=product_repository
    )


# Define common dependencies for API endpoints
class CommonDependencies:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        product_service: ProductService = Depends(get_product_service),
        supplier_service: SupplierService = Depends(get_supplier_service),
        history_service: HistoryService = Depends(get_history_service)
    ):
        self.db = db
        self.product_service = product_service
        self.supplier_service = supplier_service
        self.history_service = history_service