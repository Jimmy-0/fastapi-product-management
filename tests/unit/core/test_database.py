# tests/unit/core/test_database.py
import pytest
from sqlalchemy import text
from app.core.database import get_engine
from app.core.database import get_db


@pytest.mark.asyncio
async def test_engine_creation():
    engine = await get_engine(max_retries=2, retry_interval=1)
    assert engine is not None
    
    assert str(engine.url).startswith("postgresql+asyncpg://")

    # Instead of connecting directly, use a simple query in a context manager
    # async with engine.begin() as conn:
    #     result = await conn.execute("SELECT 1")
    #     assert await result.scalar() == 1

@pytest.mark.asyncio
async def test_get_db():
    """Test that the get_db dependency provides a working database session."""
    # Import what we need for mocking
    from unittest.mock import patch, AsyncMock
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Create a mock session with a result that returns 1
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.fetchone.return_value = (1,)
    mock_session.execute.return_value = mock_result
    
    # Patch the AsyncSessionLocal to return our mock session
    with patch('app.core.database.AsyncSessionLocal', return_value=mock_session):
        # Get the generator
        db_generator = get_db()
        # Get the session from the generator
        db = await anext(db_generator)
        
        # Verify it's our mock session
        assert db is mock_session
        
        # Verify the execute method was called with the expected SQL
        mock_session.execute.assert_called_once()
        assert "SELECT 1" in str(mock_session.execute.call_args[0][0])
        
        # Clean up by advancing the generator to its end
        try:
            await anext(db_generator)
        except StopAsyncIteration:
            pass