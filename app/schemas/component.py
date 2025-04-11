from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

# Shared properties
class ComponentBase(BaseModel):
    name: str
    type: str # e.g., 'Sensor', 'Actuator'
    config: Optional[dict[str, Any]] = None # Allow any JSON structure for config
    machine_model_id: int # Foreign key

# Properties to receive via API on creation
class ComponentCreate(ComponentBase):
    pass # Inherits name, type, config, machine_model_id

# Properties to receive via API on update
class ComponentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    # machine_model_id is typically not updatable

# Properties shared by models stored in DB
class ComponentInDBBase(ComponentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True) # Enable ORM mode

# Properties to return to client
class Component(ComponentInDBBase):
    pass # Inherits all fields from ComponentInDBBase

# Properties stored in DB
class ComponentInDB(ComponentInDBBase):
    pass # Inherits all fields from ComponentInDBBase