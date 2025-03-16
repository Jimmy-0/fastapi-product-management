# app/models/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.core.database import Base

# Association table for Product-Supplier many-to-many relationship
ProductSupplier = Table(
    "product_suppliers",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("supplier_id", Integer, ForeignKey("suppliers.id"), primary_key=True)
)

class Product(Base):
    """Product model."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    category = Column(String(50), nullable=True, index=True)
    discount = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    suppliers = relationship("Supplier", secondary="product_suppliers", lazy="selectin")

    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    stock_history = relationship("StockHistory", back_populates="product", cascade="all, delete-orphan")


class Supplier(Base):
    """Supplier model."""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    contact_info = Column(Text, nullable=False)
    credit_rating = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = relationship("Product", secondary=ProductSupplier, back_populates="suppliers")


class PriceHistory(Base):
    """Price history model for tracking price changes."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    product = relationship("Product", back_populates="price_history")


class StockHistory(Base):
    """Stock history model for tracking stock quantity changes."""
    __tablename__ = "stock_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    old_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    change_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    product = relationship("Product", back_populates="stock_history")