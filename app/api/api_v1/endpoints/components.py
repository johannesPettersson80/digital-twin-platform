from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.db.session import get_db # Dependency

router = APIRouter()

@router.post("/", response_model=schemas.Component, status_code=status.HTTP_201_CREATED)
def create_component(
    *,
    db: Session = Depends(get_db),
    component_in: schemas.ComponentCreate,
) -> Any:
    """
    Create new component. Requires machine_model_id in the input schema.
    """
    # Check if machine_model_id exists
    machine_model = crud.machine_model.get(db=db, id=component_in.machine_model_id)
    if not machine_model:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail=f"Machine Model with id {component_in.machine_model_id} not found",
         )
    component = crud.component.create(db=db, obj_in=component_in)
    return component

@router.get("/", response_model=List[schemas.Component])
def read_components(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    machine_model_id: Optional[int] = Query(None, description="Filter components by machine model ID"),
) -> Any:
    """
    Retrieve components. Optionally filter by machine_model_id.
    """
    if machine_model_id is not None:
        # Check if machine model exists
        machine_model = crud.machine_model.get(db=db, id=machine_model_id)
        if not machine_model:
            return [] # Return empty list if parent model not found
        components = crud.component.get_multi_by_machine_model(
            db=db, machine_model_id=machine_model_id, skip=skip, limit=limit
        )
    else:
        # Consider if listing all components across all models is desired/allowed
        # For now, let's assume it is, but it might be better to require machine_model_id
        components = crud.component.get_multi(db, skip=skip, limit=limit)
    return components

@router.get("/{component_id}", response_model=schemas.Component)
def read_component(
    *,
    db: Session = Depends(get_db),
    component_id: int,
) -> Any:
    """
    Get component by ID.
    """
    component = crud.component.get(db=db, id=component_id)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )
    return component

@router.put("/{component_id}", response_model=schemas.Component)
def update_component(
    *,
    db: Session = Depends(get_db),
    component_id: int,
    component_in: schemas.ComponentUpdate,
) -> Any:
    """
    Update a component.
    """
    component = crud.component.get(db=db, id=component_id)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )
    component = crud.component.update(db=db, db_obj=component, obj_in=component_in)
    return component

@router.delete("/{component_id}", response_model=schemas.Component)
def delete_component(
    *,
    db: Session = Depends(get_db),
    component_id: int,
) -> Any:
    """
    Delete a component.
    """
    component = crud.component.get(db=db, id=component_id)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )
    # Note: Cascading deletes for connections involving this component are handled by relationship config
    deleted_component = crud.component.remove(db=db, id=component_id)
    return deleted_component