from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Import simulation schemas and service
from app import schemas
from app.services import simulation_service
# Import DB session dependency
from app.db.session import get_db
# Placeholder for potential DB/CRUD dependencies (kept for reference)
# from app.crud import crud_simulation

router = APIRouter()

# Placeholder for getting DB session if needed for simulation control
# def get_db():
#     db = db_session.SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# Define response model later if needed, e.g., response_model=schemas.SimulationInfo
@router.post("/start", status_code=202, response_model=schemas.SimulationInfo)
async def start_simulation(
    payload: schemas.SimulationStart,
    db: Session = Depends(get_db) # Inject DB session
):
    """
    Starts a simulation based on the provided machine model ID.
    """
    print(f"API: Received request to start simulation for model ID: {payload.machine_model_id}")
    try:
        sim_state = await simulation_service.create_and_start_simulation(
            db=db, # Pass the DB session
            machine_model_id=payload.machine_model_id
        )
        # Map SimulationState to SimulationInfo response
        return schemas.SimulationInfo(
            simulation_id=sim_state.simulation_id,
            machine_model_id=sim_state.machine_model_id,
            status=sim_state.status,
            message=f"Simulation {sim_state.simulation_id} starting."
        )
    except Exception as e:
        # Basic error handling, refine as needed
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")

@router.post("/stop", status_code=200, response_model=schemas.Message)
async def stop_simulation(
    payload: schemas.SimulationStop,
    # db: Session = Depends(get_db) # Example: If DB interaction is needed
):
    """
    Stops a running simulation identified by its ID.
    """
    print(f"API: Received request to stop simulation ID: {payload.simulation_id}")
    stopped = await simulation_service.stop_simulation(payload.simulation_id)
    if not stopped:
        # Check if simulation exists before raising 404
        state = simulation_service.get_simulation_state(payload.simulation_id)
        if state is None:
            raise HTTPException(status_code=404, detail=f"Simulation {payload.simulation_id} not found.")
        else:
            # Simulation exists but couldn't be stopped (e.g., already stopped/error)
             raise HTTPException(status_code=400, detail=f"Simulation {payload.simulation_id} could not be stopped (current status: {state.status}).")

    return {"message": f"Simulation {payload.simulation_id} stop request accepted."}

@router.get("/{simulation_id}/status", response_model=schemas.SimulationStatus)
async def get_simulation_status(
    simulation_id: int,
    # db: Session = Depends(get_db) # Example: If DB interaction is needed
):
    """
    Gets the current status of a specific simulation.
    """
    print(f"API: Received request for status of simulation {simulation_id}...")
    sim_state = simulation_service.get_simulation_state(simulation_id)

    if sim_state is None:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found.")

    # Map SimulationState to SimulationStatus response
    return schemas.SimulationStatus(
        simulation_id=sim_state.simulation_id,
        status=sim_state.status,
        details={
            "machine_model_id": sim_state.machine_model_id,
            "start_time": sim_state.start_time,
            "error": sim_state.error_message,
            "component_states": sim_state.component_states # Include component states
        }
    )