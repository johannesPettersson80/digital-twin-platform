# app/db/base.py
from sqlalchemy.orm import declarative_base

# Define the Base class for models to inherit from
Base = declarative_base()

# Import all models here using Base.metadata to ensure they are registered correctly.
# This pattern helps avoid circular import issues and ensures SQLAlchemy knows about all tables.
# The imports need to happen *after* Base is defined.
# Use noqa comments if your linter complains about unused imports, as they are needed for registration.

from app.models.project import Project  # noqa: F401, E402
from app.models.machine_model import MachineModel  # noqa: F401, E402
from app.models.component import Component  # noqa: F401, E402
from app.models.connection import Connection  # noqa: F401, E402
from app.models.communication_binding import CommunicationBinding  # noqa: F401, E402

# Explicitly access something on the models to help ensure they are fully processed/registered.
_ = [
    Project.__tablename__,
    MachineModel.__tablename__,
    Component.__tablename__,
    Connection.__tablename__,
    CommunicationBinding.__tablename__,
]