# app/schemas/communication_binding.py

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

# Shared properties
class CommunicationBindingBase(BaseModel):
    component_id: int = Field(..., gt=0, description="ID of the component this binding applies to")
    component_port: str = Field(..., min_length=1, description="Name of the component's port/property (e.g., 'temperature', 'status')")
    direction: str = Field(..., description="Direction of data flow: 'read' (from external) or 'write' (to external)")
    protocol: str = Field(default="OPCUA", description="Communication protocol (e.g., 'OPCUA', 'Modbus')")
    address: str = Field(..., min_length=1, description="External system address (e.g., OPC UA Node ID, Modbus register)")
    config: Optional[Dict[str, Any]] = Field(None, description="Optional protocol-specific configuration")
    machine_model_id: int = Field(..., gt=0, description="ID of the machine model this binding belongs to")

    @field_validator('direction')
    def direction_must_be_valid(cls, v):
        if v not in ['read', 'write']:
            raise ValueError("Direction must be either 'read' or 'write'")
        return v

# Properties to receive via API on creation
class CommunicationBindingCreate(CommunicationBindingBase):
    pass # Inherits all fields from Base

# Properties to receive via API on update
class CommunicationBindingUpdate(BaseModel):
    component_id: Optional[int] = Field(None, gt=0, description="ID of the component this binding applies to")
    component_port: Optional[str] = Field(None, min_length=1, description="Name of the component's port/property")
    direction: Optional[str] = Field(None, description="Direction of data flow: 'read' or 'write'")
    protocol: Optional[str] = Field(None, description="Communication protocol")
    address: Optional[str] = Field(None, min_length=1, description="External system address")
    config: Optional[Dict[str, Any]] = Field(None, description="Optional protocol-specific configuration")
    # machine_model_id is usually not updatable directly, managed via endpoint path

    @field_validator('direction')
    def direction_must_be_valid_optional(cls, v):
        if v is not None and v not in ['read', 'write']:
            raise ValueError("Direction must be either 'read' or 'write'")
        return v

# Properties shared by models stored in DB
class CommunicationBindingInDBBase(CommunicationBindingBase):
    id: int

    class Config:
        from_attributes = True # Replaces orm_mode = True

# Properties to return to client
class CommunicationBinding(CommunicationBindingInDBBase):
    pass # Inherits all fields from InDBBase

# Properties stored in DB
class CommunicationBindingInDB(CommunicationBindingInDBBase):
    pass # Inherits all fields from InDBBase