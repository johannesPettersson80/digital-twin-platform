from .base import CRUDBase
from app.models.machine_model import MachineModel
from app.schemas.machine_model import MachineModelCreate, MachineModelUpdate
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

class CRUDMachineModel(CRUDBase[MachineModel, MachineModelCreate, MachineModelUpdate]):
    # Add specific methods if needed, e.g., get models by project_id
    def get_multi_by_project(
        self, db: Session, *, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[MachineModel]:
        statement = (
            select(self.model)
            .where(self.model.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(statement)
        return result.scalars().all()

# Create an instance for easy import
machine_model = CRUDMachineModel(MachineModel)