from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# Shared properties
class MachineModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: int # Foreign key

# Properties to receive via API on creation
class MachineModelCreate(MachineModelBase):
    pass # Inherits name, description, project_id

# Properties to receive via API on update
class MachineModelUpdate(BaseModel):
    name: Optional[str] = None # Make all fields optional for update
    description: Optional[str] = None
    # project_id is typically not updatable directly this way

# Properties shared by models stored in DB
class MachineModelInDBBase(MachineModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True) # Enable ORM mode

# Properties to return to client
class MachineModel(MachineModelInDBBase):
    pass # Inherits all fields from MachineModelInDBBase
    # Later, might include nested components/connections here

# Properties stored in DB
class MachineModelInDB(MachineModelInDBBase):
    pass # Inherits all fields from MachineModelInDBBase