from ..models.base import Base
from ..core.database import engine
from ..models.models import Product, Supplier, PriceStockHistory
import logging

logger = logging.getLogger(__name__)

def init_db():
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# This ensures tables are created when the application starts
if __name__ == "__main__":
    init_db()