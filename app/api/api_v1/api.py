from fastapi import APIRouter

from app.api.api_v1.endpoints import projects, machine_models, components, connections, simulation, communication_bindings
# Import other endpoint routers here as they are created
# from app.api.api_v1.endpoints import testing

api_router = APIRouter()

# Include project routes
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])

# Include other routes here
api_router.include_router(machine_models.router, prefix="/machine-models", tags=["Machine Models"])
api_router.include_router(components.router, prefix="/components", tags=["Components"])
api_router.include_router(connections.router, prefix="/connections", tags=["Connections"])
api_router.include_router(simulation.router, prefix="/simulations", tags=["Simulation"]) # Added simulation router
api_router.include_router(communication_bindings.router, tags=["Communication Bindings"]) # Added communication bindings router (no prefix, handled in endpoint file)
# api_router.include_router(testing.router, prefix="/testing", tags=["Testing"])