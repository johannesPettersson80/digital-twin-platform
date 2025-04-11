from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base # Import Base from the new base module

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Define relationships
    machine_models = relationship("MachineModel", back_populates="project")
    # Other relationships can be uncommented as needed:
    # test_cases = relationship("TestCase", back_populates="project")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"