from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base # Import Base from the new base module

class MachineModel(Base):
    __tablename__ = "machine_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="machine_models")
    components = relationship("Component", back_populates="machine_model", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="machine_model", cascade="all, delete-orphan")
    communication_bindings = relationship("CommunicationBinding", back_populates="machine_model", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MachineModel(id={self.id}, name='{self.name}', project_id={self.project_id})>"