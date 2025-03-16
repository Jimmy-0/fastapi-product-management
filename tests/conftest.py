# tests/conftest.py
import pytest
import os
import asyncio
from datetime import datetime
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient
from app.main import app
from app.core.database import Base, get_db
from app.models.models import Product, Supplier, PriceHistory, StockHistory
from unittest.mock import patch

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://postgres:password@localhost/test_product_service"
)

# Configure pytest-asyncio to use function scope for event loops
def pytest_configure(config):
    """Set pytest-asyncio default loop scope to function."""
    config.option.asyncio_default_fixture_loop_scope = "function"

# Event loop fixture
@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop for each test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    if not loop.is_closed():
        loop.close()

# Test DB engine
@pytest.fixture(scope="function")
async def test_engine():
    """Create a fresh test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL, 
        echo=False,
        future=True,
        poolclass=pool.NullPool
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()

# Test DB session
@pytest.fixture(scope="function")
async def test_db(test_engine):
    """Create a test database session."""
    async_session = sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

# Mocked client fixture to avoid startup event
@pytest.fixture(scope="function")
def client():
    """Create a test client with startup events disabled."""
    # Create a real database session for tests
    engine = create_async_engine(
        TEST_DATABASE_URL, 
        echo=False,
        future=True,
        poolclass=pool.NullPool
    )
    
    # Create session factory
    TestSessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    # Mock async generator for dependency override
    async def mock_get_db():
        async with TestSessionLocal() as session:
            yield session
    
    # Override dependency
    app.dependency_overrides[get_db] = mock_get_db
    
    # Disable startup event to avoid event loop issues
    with patch("app.main.create_tables", return_value=None):
        # Use sync TestClient
        with TestClient(app) as test_client:
            yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

# Sample data fixture
@pytest.fixture(scope="function")
async def sample_data(test_db):
    """Create sample data for testing."""
    try:
        # Create supplier
        supplier = Supplier(
            name="Test Supplier", 
            contact_info="test@supplier.com",
            credit_rating=0
        )
        test_db.add(supplier)
        await test_db.flush()
        
        # Create product
        product = Product(
            name="Test Product",
            description="Test description",
            price=19.99,
            stock_quantity=100,
            discount=0,
            category="Test"
        )
        test_db.add(product)
        await test_db.flush()
        
        # Create price history
        price_history = PriceHistory(
            product_id=product.id,
            old_price=18.99,
            new_price=19.99,
            timestamp=datetime.now()
        )
        test_db.add(price_history)
        
        # Create stock history
        stock_history = StockHistory(
            product_id=product.id,
            old_quantity=90,
            new_quantity=100,
            timestamp=datetime.now(),
            change_reason="Initial stock"
        )
        test_db.add(stock_history)
        
        await test_db.commit()
        
        return {
            "supplier": supplier, 
            "product": product,
            "price_history": price_history,
            "stock_history": stock_history
        }
    except Exception as e:
        await test_db.rollback()
        raise e