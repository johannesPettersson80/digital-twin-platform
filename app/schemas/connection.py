from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# Shared properties
class ConnectionBase(BaseModel):
    machine_model_id: int # Foreign key
    source_component_id: int # Foreign key
    target_component_id: int # Foreign key
    source_port: Optional[str] = None # Name of the output port on the source component
    target_port: Optional[str] = None # Name of the input port on the target component
    # Optional: Add fields like signal_name if defined in the model

# Properties to receive via API on creation
class ConnectionCreate(ConnectionBase):
    pass # Inherits all base fields

# Properties to receive via API on update
# Connections are often immutable in practice (delete and recreate)
# Define if specific updates are needed, otherwise keep minimal.
class ConnectionUpdate(BaseModel):
    # Typically, you wouldn't update source/target/model IDs.
    # Maybe update metadata if added later (e.g., signal_name)
    pass # No updatable fields defined for now

# Properties shared by models stored in DB
class ConnectionInDBBase(ConnectionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True) # Enable ORM mode

# Properties to return to client
class Connection(ConnectionInDBBase):
    pass # Inherits all fields from ConnectionInDBBase

# Properties stored in DB
class ConnectionInDB(ConnectionInDBBase):
    pass # Inherits all fields from ConnectionInDBBase