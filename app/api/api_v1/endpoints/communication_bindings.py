# app/api/api_v1/endpoints/communication_bindings.py

from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
# from app.api import deps # Incorrect assumption
from app.db.session import get_db # Correct import for the dependency

router = APIRouter()

# Endpoint to list bindings for a specific machine model
@router.get("/machine_models/{machine_model_id}/communication_bindings/", response_model=List[schemas.CommunicationBinding])
def read_communication_bindings_for_model(
    machine_model_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve communication bindings for a specific machine model.
    """
    # Optional: Check if machine model exists
    model = crud.machine_model.get(db=db, id=machine_model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine Model with ID {machine_model_id} not found",
        )
    bindings = crud.communication_binding.get_multi_by_machine_model(
        db=db, machine_model_id=machine_model_id, skip=skip, limit=limit
    )
    return bindings

# Endpoint to create a binding for a specific machine model
@router.post("/machine_models/{machine_model_id}/communication_bindings/", response_model=schemas.CommunicationBinding, status_code=status.HTTP_201_CREATED)
def create_communication_binding_for_model(
    machine_model_id: int,
    *,
    db: Session = Depends(get_db),
    binding_in: schemas.CommunicationBindingCreate,
) -> Any:
    """
    Create a new communication binding associated with a specific machine model.
    """
    # Optional: Check if machine model exists
    model = crud.machine_model.get(db=db, id=machine_model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine Model with ID {machine_model_id} not found",
        )
    # Ensure the payload's machine_model_id matches the path parameter
    if binding_in.machine_model_id != machine_model_id:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payload machine_model_id ({binding_in.machine_model_id}) does not match path parameter ({machine_model_id})",
        )

    # Optional: Check if component exists within the model
    component = crud.component.get(db=db, id=binding_in.component_id)
    if not component or component.machine_model_id != machine_model_id:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component with ID {binding_in.component_id} not found within Machine Model {machine_model_id}",
        )

    binding = crud.communication_binding.create_with_machine_model(
        db=db, obj_in=binding_in, machine_model_id=machine_model_id
    )
    return binding

# Endpoint to get a specific binding by its ID
@router.get("/communication_bindings/{binding_id}", response_model=schemas.CommunicationBinding)
def read_communication_binding(
    binding_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific communication binding by ID.
    """
    binding = crud.communication_binding.get(db=db, id=binding_id)
    if not binding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Communication Binding with ID {binding_id} not found",
        )
    return binding

# Endpoint to update a specific binding
@router.put("/communication_bindings/{binding_id}", response_model=schemas.CommunicationBinding)
def update_communication_binding(
    binding_id: int,
    *,
    db: Session = Depends(get_db),
    binding_in: schemas.CommunicationBindingUpdate,
) -> Any:
    """
    Update a communication binding.
    """
    binding = crud.communication_binding.get(db=db, id=binding_id)
    if not binding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Communication Binding with ID {binding_id} not found",
        )

    # Optional: Add validation if component_id is changed, ensure it exists in the same model
    if binding_in.component_id is not None:
        component = crud.component.get(db=db, id=binding_in.component_id)
        if not component or component.machine_model_id != binding.machine_model_id:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Component with ID {binding_in.component_id} not found within the original Machine Model {binding.machine_model_id}",
            )

    updated_binding = crud.communication_binding.update(db=db, db_obj=binding, obj_in=binding_in)
    return updated_binding

# Endpoint to delete a specific binding
@router.delete("/communication_bindings/{binding_id}", response_model=schemas.CommunicationBinding)
def delete_communication_binding(
    binding_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Delete a communication binding.
    """
    binding = crud.communication_binding.get(db=db, id=binding_id)
    if not binding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Communication Binding with ID {binding_id} not found",
        )
    deleted_binding = crud.communication_binding.remove(db=db, id=binding_id)
    return deleted_binding