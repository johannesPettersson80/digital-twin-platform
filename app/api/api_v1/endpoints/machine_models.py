from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.db.session import get_db # Dependency

router = APIRouter()

@router.post("/", response_model=schemas.MachineModel, status_code=status.HTTP_201_CREATED)
def create_machine_model(
    *,
    db: Session = Depends(get_db),
    machine_model_in: schemas.MachineModelCreate,
) -> Any:
    """
    Create new machine model. Requires project_id in the input schema.
    """
    # Optional: Check if project_id exists?
    project = crud.project.get(db=db, id=machine_model_in.project_id)
    if not project:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail=f"Project with id {machine_model_in.project_id} not found",
         )
    machine_model = crud.machine_model.create(db=db, obj_in=machine_model_in)
    return machine_model

@router.get("/", response_model=List[schemas.MachineModel])
def read_machine_models(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = Query(None, description="Filter machine models by project ID"),
) -> Any:
    """
    Retrieve machine models. Optionally filter by project_id.
    """
    if project_id is not None:
        # Optional: Check if project exists?
        project = crud.project.get(db=db, id=project_id)
        if not project:
            # Return empty list or 404? Returning empty list is common for filters.
            return []
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found")
        machine_models = crud.machine_model.get_multi_by_project(
            db=db, project_id=project_id, skip=skip, limit=limit
        )
    else:
        machine_models = crud.machine_model.get_multi(db, skip=skip, limit=limit)
    return machine_models

@router.get("/{machine_model_id}", response_model=schemas.MachineModel)
def read_machine_model(
    *,
    db: Session = Depends(get_db),
    machine_model_id: int,
) -> Any:
    """
    Get machine model by ID.
    """
    machine_model = crud.machine_model.get(db=db, id=machine_model_id)
    if not machine_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine Model not found",
        )
    return machine_model

@router.put("/{machine_model_id}", response_model=schemas.MachineModel)
def update_machine_model(
    *,
    db: Session = Depends(get_db),
    machine_model_id: int,
    machine_model_in: schemas.MachineModelUpdate,
) -> Any:
    """
    Update a machine model.
    """
    machine_model = crud.machine_model.get(db=db, id=machine_model_id)
    if not machine_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine Model not found",
        )
    machine_model = crud.machine_model.update(db=db, db_obj=machine_model, obj_in=machine_model_in)
    return machine_model

@router.delete("/{machine_model_id}", response_model=schemas.MachineModel)
def delete_machine_model(
    *,
    db: Session = Depends(get_db),
    machine_model_id: int,
) -> Any:
    """
    Delete a machine model.
    """
    machine_model = crud.machine_model.get(db=db, id=machine_model_id)
    if not machine_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine Model not found",
        )
    # Note: Cascading deletes for components/connections are handled by the relationship config in the model
    deleted_machine_model = crud.machine_model.remove(db=db, id=machine_model_id)
    return deleted_machine_model