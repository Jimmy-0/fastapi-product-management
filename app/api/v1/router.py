# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.endpoints import product, supplier, history, auth, admin

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

# Admin routes that require authentication
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"]
)

api_router.include_router(
    product.router,
    prefix="/products",
    tags=["products"]
)

api_router.include_router(
    supplier.router,
    prefix="/suppliers",
    tags=["suppliers"]
)

api_router.include_router(
    history.router,
    prefix="/history",
    tags=["history"]
)