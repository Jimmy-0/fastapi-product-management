# app/core/database.py
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tenacity import retry, stop_after_attempt, wait_fixed

from sqlalchemy import text

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async engine 
# Note: Async engines use their own pooling mechanism automatically
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DB_ECHO_LOG,
    pool_pre_ping=True,
)

# Create async session factory
# In SQLAlchemy 2.0, asyncio using async_sessionmaker is preferred
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Create base class for SQLAlchemy models
Base = declarative_base()

async def get_engine(max_retries=None, retry_interval=None):
    return engine


@retry(
    stop=stop_after_attempt(settings.DB_RETRY_LIMIT),
    wait=wait_fixed(settings.DB_RETRY_INTERVAL),
)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create and yield a database session.
    
    Returns:
        AsyncGenerator: Database session
        
    Yields:
        AsyncGenerator[AsyncSession, None]: Database session
    """
    session = AsyncSessionLocal()
    try:
        # Test connection before yielding - use text() function
        await session.execute(text("SELECT 1"))
        logger.debug("Database connection established")
        
        yield session
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        await session.close()


async def create_tables():
    """
    Create all tables defined in the models.
    For development and testing purposes only.
    In production, use Alembic for migrations.
    """
    from app.models.user import User
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def drop_tables():
    """
    Drop all tables defined in the models.
    For development and testing purposes only.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped")