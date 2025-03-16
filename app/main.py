# app/main.py
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

from app.api.v1.router import api_router
from app.core.database import create_tables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API settings
API_V1_STR = "/api/v1"
PROJECT_NAME = "Product Service API"

# Create FastAPI application
app = FastAPI(
    title=PROJECT_NAME,
    openapi_url=f"{API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=API_V1_STR)

# Service registration settings
SERVICE_NAME = os.getenv("SERVICE_NAME", "product-service")
SERVICE_HOST = os.getenv("SERVICE_HOST", "localhost")
SERVICE_PORT = os.getenv("SERVICE_PORT", "8000")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://api-gateway:8080")


@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    """
    logger.info("Starting up application...")
    
    # Create database tables for development/testing
    # In production, use Alembic for migrations
    if os.getenv("ENVIRONMENT", "development") == "development":
        await create_tables()
        logger.info("Database tables created")
    
    # Register service with API gateway if gateway URL is provided
    if GATEWAY_URL != "http://api-gateway:8080":
        await register_service()


async def register_service():
    """
    Register service with API gateway.
    """
    service_data = {
        "name": SERVICE_NAME,
        "url": f"http://{SERVICE_HOST}:{SERVICE_PORT}",
        "endpoints": [
            {"path": f"{API_V1_STR}/products", "methods": ["GET", "POST"]},
            {"path": f"{API_V1_STR}/products/{{product_id}}", "methods": ["GET", "PUT", "DELETE"]},
            {"path": f"{API_V1_STR}/suppliers", "methods": ["GET", "POST"]},
            {"path": f"{API_V1_STR}/suppliers/{{supplier_id}}", "methods": ["GET", "PUT", "DELETE"]},
            {"path": f"{API_V1_STR}/history/price/{{product_id}}", "methods": ["GET"]},
            {"path": f"{API_V1_STR}/history/stock/{{product_id}}", "methods": ["GET"]},
        ]
    }
    try:
        response = requests.post(f"{GATEWAY_URL}/register", json=service_data)
        if response.status_code == 200:
            logger.info(f"Service registered successfully: {response.json()}")
        else:
            logger.error(f"Failed to register service: {response.text}")
    except Exception as e:
        logger.error(f"Service registration error: {e}")


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    """
    # Check database connection
    try:
        from sqlalchemy import text
        from app.core.database import engine
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": SERVICE_NAME,
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": SERVICE_NAME,
            "error": str(e)
        }


# If running directly with "python app/main.py"
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)