from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Direct imports for clarity
from app.crud.crud_project import project as crud_project
from app.schemas import Project, ProjectCreate, ProjectUpdate
from app.db.session import get_db

# Import models to ensure they're loaded (important for SQLAlchemy relationship detection)
from app.models.project import Project as ProjectModel
from app.models.machine_model import MachineModel  # This ensures the relationship is properly detected

router = APIRouter()

@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED) 
def create_project(
    *,
    db: Session = Depends(get_db),
    project_in: ProjectCreate, # Use imported ProjectCreate schema
) -> Any:
    """
    Create new project.
    """
    project = crud_project.create(db=db, obj_in=project_in)
    return project


@router.get("/", response_model=List[Project]) # Use imported Project schema
def read_projects(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve projects.
    """
    projects = crud_project.get_multi(db, skip=skip, limit=limit) # Use imported crud_project
    return projects

@router.get("/{project_id}", response_model=Project) # Use imported Project schema
def read_project(
    *,
    db: Session = Depends(get_db),
    project_id: int,
) -> Any:
    """
    Get project by ID.
    """
    project = crud_project.get(db=db, id=project_id) # Use imported crud_project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project

@router.put("/{project_id}", response_model=Project) # Use imported Project schema
def update_project(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    project_in: ProjectUpdate, # Use imported ProjectUpdate schema
) -> Any:
    """
    Update a project.
    """
    project = crud_project.get(db=db, id=project_id) # Use imported crud_project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    project = crud_project.update(db=db, db_obj=project, obj_in=project_in) # Use imported crud_project
    return project

@router.delete("/{project_id}", response_model=Project) # Use imported Project schema
def delete_project(
    *,
    db: Session = Depends(get_db),
    project_id: int,
) -> Any:
    """
    Delete a project.
    """
    project = crud_project.get(db=db, id=project_id) # Use imported crud_project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    project = crud_project.remove(db=db, id=project_id) # Use imported crud_project
    # Note: remove returns the deleted object or None if deletion failed unexpectedly after check
    # We rely on the initial check for the 404
    return project # Return the deleted object data