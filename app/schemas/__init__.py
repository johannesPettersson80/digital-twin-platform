# This file makes the 'schemas' directory a Python package.

# Import schemas here to make them directly accessible via app.schemas
from .project import Project, ProjectCreate, ProjectUpdate, ProjectInDB
from .machine_model import MachineModel, MachineModelCreate, MachineModelUpdate, MachineModelInDB
from .component import Component, ComponentCreate, ComponentUpdate, ComponentInDB
from .connection import Connection, ConnectionCreate, ConnectionUpdate, ConnectionInDB
from .simulation import SimulationStart, SimulationStop, SimulationInfo, SimulationStatus, SimulationResult
from .communication_binding import CommunicationBinding, CommunicationBindingCreate, CommunicationBindingUpdate, CommunicationBindingInDB # Added for Phase 3
from .message import Message # Import the new Message schema