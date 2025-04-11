from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base # Import Base from the new base module
# Need to import Component for relationship typing, but avoid circular import issues
# by using string references in relationship definitions if necessary.
# from .component import Component # This might cause circular import if Component imports Connection
# from .machine_model import MachineModel # This might cause circular import

class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    machine_model_id = Column(Integer, ForeignKey("machine_models.id"), nullable=False, index=True)
    source_component_id = Column(Integer, ForeignKey("components.id"), nullable=False, index=True)
    target_component_id = Column(Integer, ForeignKey("components.id"), nullable=False, index=True)
    source_port = Column(String(255), nullable=True, index=True) # Name of the output port on the source component
    target_port = Column(String(255), nullable=True, index=True) # Name of the input port on the target component
    # Optional: Add fields like signal_name, data_type if needed later
    # signal_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # Use string names for related classes to avoid direct import issues
    machine_model = relationship("MachineModel", back_populates="connections")
    source_component = relationship(
        "Component",
        foreign_keys=[source_component_id],
        back_populates="source_connections"
    )
    target_component = relationship(
        "Component",
        foreign_keys=[target_component_id],
        back_populates="target_connections"
    )

    def __repr__(self):
        return f"<Connection(id={self.id}, from={self.source_component_id}, to={self.target_component_id}, model={self.machine_model_id})>"