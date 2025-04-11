# app/crud/crud_communication_binding.py

from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select # Use select for modern SQLAlchemy

from app.crud.base import CRUDBase # Assuming you have a CRUDBase or similar pattern
from app.models.communication_binding import CommunicationBinding
from app.schemas.communication_binding import CommunicationBindingCreate, CommunicationBindingUpdate

class CRUDCommunicationBinding(CRUDBase[CommunicationBinding, CommunicationBindingCreate, CommunicationBindingUpdate]):
    # Specific methods for CommunicationBinding

    def get_multi_by_machine_model(
        self, db: Session, *, machine_model_id: int, skip: int = 0, limit: int = 100
    ) -> List[CommunicationBinding]:
        """
        Retrieve multiple communication bindings belonging to a specific machine model.
        """
        statement = (
            select(self.model)
            .where(CommunicationBinding.machine_model_id == machine_model_id)
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(statement)
        return result.scalars().all()

    def get_multi_by_component(
        self, db: Session, *, component_id: int, skip: int = 0, limit: int = 100
    ) -> List[CommunicationBinding]:
        """
        Retrieve multiple communication bindings belonging to a specific component.
        """
        statement = (
            select(self.model)
            .where(CommunicationBinding.component_id == component_id)
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(statement)
        return result.scalars().all()

    def create_with_machine_model(
        self, db: Session, *, obj_in: CommunicationBindingCreate, machine_model_id: int
    ) -> CommunicationBinding:
        """
        Create a new communication binding associated with a specific machine model.
        Ensures the machine_model_id from the path is used.
        """
        # Ensure the machine_model_id from the path matches the payload or override it
        # For consistency, we usually rely on the path parameter.
        # obj_in_data = obj_in.model_dump() # Use model_dump() for Pydantic v2
        # obj_in_data['machine_model_id'] = machine_model_id # Override if needed, but schema enforces it now

        # Validate component exists within the machine model (optional but recommended)
        # component = db.query(Component).filter(Component.id == obj_in.component_id, Component.machine_model_id == machine_model_id).first()
        # if not component:
        #     raise ValueError(f"Component {obj_in.component_id} not found in machine model {machine_model_id}")

        db_obj = self.model(**obj_in.model_dump()) # Create model instance
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# Instantiate the CRUD object for use in API endpoints
communication_binding = CRUDCommunicationBinding(CommunicationBinding)