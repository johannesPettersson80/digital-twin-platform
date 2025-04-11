from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select # Use select for SQLAlchemy 2.0 style queries

from app.db.base import Base # Import Base from the new base module

# Define Type Variables for Generic CRUD operations
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        # SQLAlchemy 2.0 style query
        statement = select(self.model).where(self.model.id == id)
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination."""
        statement = select(self.model).offset(skip).limit(limit)
        result = db.execute(statement)
        return result.scalars().all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        # Convert Pydantic schema to dict
        obj_in_data = jsonable_encoder(obj_in)
        # Create SQLAlchemy model instance
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing record."""
        # Get existing data as dict
        obj_data = jsonable_encoder(db_obj)
        # Get update data as dict, excluding unset values if it's a Pydantic model
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Use exclude_unset=True to only update fields that were explicitly passed
            update_data = obj_in.model_dump(exclude_unset=True)

        # Update fields
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Delete a record by ID."""
        obj = db.get(self.model, id) # Use db.get for primary key lookup
        if obj:
            db.delete(obj)
            db.commit()
        return obj