# app/repositories/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import func, select, desc, asc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException

# Define generic types for SQLAlchemy models and Pydantic schemas
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class that provides CRUD operations for different entities.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with the SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get a single record by id.
        """
        result = await db.get(self.model, id)
        if not result:
            raise NotFoundException(f"{self.model.__name__} with id {id} not found")
        return result

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc",
        **filters
    ) -> List[ModelType]:
        """
        Get multiple records with pagination, sorting and filtering.
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, dict):
                        # Handle range filters (min/max)
                        if "min" in value and value["min"] is not None:
                            filter_conditions.append(getattr(self.model, key) >= value["min"])
                        if "max" in value and value["max"] is not None:
                            filter_conditions.append(getattr(self.model, key) <= value["max"])
                    elif isinstance(value, list):
                        # Handle list of values (IN operator)
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    elif value is not None:
                        # Handle exact match
                        filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Apply sorting
        if sort_by and hasattr(self.model, sort_by):
            if sort_order.lower() == "desc":
                query = query.order_by(desc(getattr(self.model, sort_by)))
            else:
                query = query.order_by(asc(getattr(self.model, sort_by)))
                
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def search(
        self,
        db: AsyncSession,
        *,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
        **kwargs
    ) -> List[ModelType]:
        """
        Search for records based on a search term across multiple fields.
        """
        if not search_term or not search_fields:
            return await self.get_multi(db, skip=skip, limit=limit, **kwargs)
        
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                search_conditions.append(
                    getattr(self.model, field).ilike(f"%{search_term}%")
                )
        
        query = select(self.model).where(or_(*search_conditions))
        
        # Apply additional filters from kwargs
        if kwargs:
            filter_conditions = []
            for key, value in kwargs.items():
                if hasattr(self.model, key) and value is not None:
                    filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def batch_create(self, db: AsyncSession, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple records in a batch.
        """
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db_objs.append(db_obj)
        
        await db.commit()
        
        # Refresh all objects
        for db_obj in db_objs:
            await db.refresh(db_obj)
        
        return db_objs

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        """
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def batch_update(
        self,
        db: AsyncSession,
        *,
        ids: List[Any],
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> List[ModelType]:
        """
        Update multiple records by their IDs.
        """
        if not ids:
            return []
            
        # Get all objects to update
        query = select(self.model).where(self.model.id.in_(ids))
        result = await db.execute(query)
        db_objs = result.scalars().all()
        
        if not db_objs:
            return []
            
        # Convert input to dict if it's a Pydantic model
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        # Update each object
        updated_objs = []
        for db_obj in db_objs:
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
                    
            db.add(db_obj)
            updated_objs.append(db_obj)
            
        await db.commit()
        
        # Refresh all objects
        for db_obj in updated_objs:
            await db.refresh(db_obj)
            
        return updated_objs

    async def delete(self, db: AsyncSession, *, id: Any) -> ModelType:
        """
        Delete a record by id.
        """
        obj = await self.get(db, id)
        await db.delete(obj)
        await db.commit()
        return obj

    async def batch_delete(self, db: AsyncSession, *, ids: List[Any]) -> List[ModelType]:
        """
        Delete multiple records by their IDs.
        """
        if not ids:
            return []
            
        # Get all objects to delete
        query = select(self.model).where(self.model.id.in_(ids))
        result = await db.execute(query)
        db_objs = result.scalars().all()
        
        if not db_objs:
            return []
            
        # Delete each object
        for db_obj in db_objs:
            await db.delete(db_obj)
            
        await db.commit()
        return db_objs

    async def count(self, db: AsyncSession, **filters) -> int:
        """
        Count total records with optional filters.
        """
        query = select(func.count()).select_from(self.model)
        
        # Apply filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
                
        result = await db.execute(query)
        return result.scalar_one()