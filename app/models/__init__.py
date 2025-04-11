# This file makes the 'models' directory a Python package.
# We can import Base from session here for convenience if needed,
# or specific models can import it directly.

# Example: Make Base easily accessible
# from app.db.session import Base

# Import models here to make them easily accessible from app.models
# and ensure they are registered with Base.metadata for Alembic
from .project import Project
from .machine_model import MachineModel
from .component import Component
from .connection import Connection