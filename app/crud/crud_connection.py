from .base import CRUDBase
from app.models.connection import Connection
from app.schemas.connection import ConnectionCreate, ConnectionUpdate
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from typing import List

class CRUDConnection(CRUDBase[Connection, ConnectionCreate, ConnectionUpdate]):
    # Add specific methods if needed, e.g., get connections by machine_model_id
    def get_multi_by_machine_model(
        self, db: Session, *, machine_model_id: int, skip: int = 0, limit: int = 100
    ) -> List[Connection]:
        statement = (
            select(self.model)
            .where(self.model.machine_model_id == machine_model_id)
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(statement)
        return result.scalars().all()

    # Example: Get connections involving a specific component (either as source or target)
    def get_multi_by_component(
        self, db: Session, *, component_id: int, skip: int = 0, limit: int = 100
    ) -> List[Connection]:
         statement = (
            select(self.model)
            .where(or_(self.model.source_component_id == component_id, self.model.target_component_id == component_id))
            .offset(skip)
            .limit(limit)
        )
         result = db.execute(statement)
         return result.scalars().all()


# Create an instance for easy import
connection = CRUDConnection(Connection)