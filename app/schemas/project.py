from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# Shared properties
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

# Properties to receive via API on creation
class ProjectCreate(ProjectBase):
    pass # name is required, description is optional

# Properties to receive via API on update
class ProjectUpdate(ProjectBase):
    name: Optional[str] = None # Make all fields optional for update
    description: Optional[str] = None

# Properties shared by models stored in DB
class ProjectInDBBase(ProjectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Pydantic V2 uses model_config
    model_config = ConfigDict(from_attributes=True) # Enable ORM mode

# Properties to return to client
class Project(ProjectInDBBase):
    pass # Inherits all fields from ProjectInDBBase

# Properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass # Inherits all fields from ProjectInDBBase