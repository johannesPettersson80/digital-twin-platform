from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base # Import Base from the new base module

class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), index=True, nullable=False) # e.g., 'Sensor', 'Actuator', 'LogicBlock'
    config = Column(JSON, nullable=True) # Store component-specific configuration
    machine_model_id = Column(Integer, ForeignKey("machine_models.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    machine_model = relationship("MachineModel", back_populates="components")
    # Relationships to Connections (as source or target) will be defined in the Connection model
    source_connections = relationship(
        "Connection",
        foreign_keys="[Connection.source_component_id]",
        back_populates="source_component",
        cascade="all, delete-orphan"
    )
    communication_bindings = relationship("CommunicationBinding", back_populates="component", cascade="all, delete-orphan")
    target_connections = relationship(
        "Connection",
        foreign_keys="[Connection.target_component_id]",
        back_populates="target_component",
        cascade="all, delete-orphan"
    )


    def __repr__(self):
        return f"<Component(id={self.id}, name='{self.name}', type='{self.type}', machine_model_id={self.machine_model_id})>"