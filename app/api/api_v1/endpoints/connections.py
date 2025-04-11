from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.db.session import get_db # Dependency

router = APIRouter()

@router.post("/", response_model=schemas.Connection, status_code=status.HTTP_201_CREATED)
def create_connection(
    *,
    db: Session = Depends(get_db),
    connection_in: schemas.ConnectionCreate,
) -> Any:
    """
    Create new connection between two components within a machine model.
    Requires machine_model_id, source_component_id, target_component_id.
    """
    # Validate machine_model exists
    machine_model = crud.machine_model.get(db=db, id=connection_in.machine_model_id)
    if not machine_model:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail=f"Machine Model with id {connection_in.machine_model_id} not found",
         )

    # Validate source component exists and belongs to the machine model
    source_component = crud.component.get(db=db, id=connection_in.source_component_id)
    if not source_component or source_component.machine_model_id != connection_in.machine_model_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source component with id {connection_in.source_component_id} not found or does not belong to machine model {connection_in.machine_model_id}",
        )

    # Validate target component exists and belongs to the machine model
    target_component = crud.component.get(db=db, id=connection_in.target_component_id)
    if not target_component or target_component.machine_model_id != connection_in.machine_model_id:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target component with id {connection_in.target_component_id} not found or does not belong to machine model {connection_in.machine_model_id}",
        )

    # Prevent self-connections? (Optional business logic)
    if connection_in.source_component_id == connection_in.target_component_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and target component cannot be the same.",
        )

    connection = crud.connection.create(db=db, obj_in=connection_in)
    return connection

@router.get("/", response_model=List[schemas.Connection])
def read_connections(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    machine_model_id: Optional[int] = Query(None, description="Filter connections by machine model ID"),
    component_id: Optional[int] = Query(None, description="Filter connections involving a specific component ID (as source or target)"),
) -> Any:
    """
    Retrieve connections. Filter by machine_model_id or component_id.
    """
    if machine_model_id is not None:
        # Check if machine model exists
        machine_model = crud.machine_model.get(db=db, id=machine_model_id)
        if not machine_model:
            return []
        connections = crud.connection.get_multi_by_machine_model(
            db=db, machine_model_id=machine_model_id, skip=skip, limit=limit
        )
    elif component_id is not None:
        # Check if component exists
        component = crud.component.get(db=db, id=component_id)
        if not component:
            return []
        connections = crud.connection.get_multi_by_component(
            db=db, component_id=component_id, skip=skip, limit=limit
        )
    else:
        # Listing all connections across all models might not be useful/performant
        # Consider raising an error or requiring a filter
        # For now, return all connections (consistent with others)
        connections = crud.connection.get_multi(db, skip=skip, limit=limit)
    return connections

@router.get("/{connection_id}", response_model=schemas.Connection)
def read_connection(
    *,
    db: Session = Depends(get_db),
    connection_id: int,
) -> Any:
    """
    Get connection by ID.
    """
    connection = crud.connection.get(db=db, id=connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )
    return connection

# PUT endpoint for connections is often omitted as they are usually immutable
# If updates were needed (e.g., changing metadata), it would go here.
# @router.put("/{connection_id}", response_model=schemas.Connection)
# def update_connection(...): ...

@router.delete("/{connection_id}", response_model=schemas.Connection)
def delete_connection(
    *,
    db: Session = Depends(get_db),
    connection_id: int,
) -> Any:
    """
    Delete a connection.
    """
    connection = crud.connection.get(db=db, id=connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )
    deleted_connection = crud.connection.remove(db=db, id=connection_id)
    return deleted_connection