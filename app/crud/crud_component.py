from .base import CRUDBase
from app.models.component import Component
from app.schemas.component import ComponentCreate, ComponentUpdate
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

class CRUDComponent(CRUDBase[Component, ComponentCreate, ComponentUpdate]):
    # Add specific methods if needed, e.g., get components by machine_model_id
    def get_multi_by_machine_model(
        self, db: Session, *, machine_model_id: int, skip: int = 0, limit: int = 100
    ) -> List[Component]:
        statement = (
            select(self.model)
            .where(self.model.machine_model_id == machine_model_id)
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(statement)
        return result.scalars().all()

# Create an instance for easy import
component = CRUDComponent(Component)