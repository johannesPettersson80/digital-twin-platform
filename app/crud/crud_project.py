from .base import CRUDBase
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

# Specific CRUD class for Project model
class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    # You can add project-specific CRUD methods here if needed.
    # For example, find project by name:
    #
    # from sqlalchemy.orm import Session
    # from sqlalchemy import select
    #
    # def get_by_name(self, db: Session, *, name: str) -> Project | None:
    #     statement = select(self.model).where(self.model.name == name)
    #     result = db.execute(statement)
    #     return result.scalar_one_or_none()
    pass

# Create an instance of the CRUDProject class for easy import
project = CRUDProject(Project)