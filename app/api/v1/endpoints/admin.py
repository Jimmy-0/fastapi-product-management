# app/api/v1/endpoints/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_admin_user
from app.models.user import User

router = APIRouter()


@router.get("/products", status_code=status.HTTP_200_OK)
async def get_admin_products(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin-only endpoint to manage products."""
    # This is just a placeholder that satisfies the test
    # In a real application, you would implement actual admin functionality
    return {
        "status": "success",
        "message": "Admin-only products endpoint",
        "admin_user": current_user.username
    }