from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

# Simulation Request Schemas
class SimulationStart(BaseModel):
    """Schema for simulation start request payload"""
    machine_model_id: int
    parameters: Optional[Dict[str, Any]] = None

class SimulationStop(BaseModel):
    """Schema for simulation stop request payload"""
    simulation_id: int
    force: bool = False

# Simulation Response Schemas
class SimulationInfo(BaseModel):
    """Schema for simulation information"""
    simulation_id: int
    machine_model_id: int
    status: str  # e.g., "pending", "running", "completed", "failed"
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    
class SimulationStatus(BaseModel):
    """Schema for simulation status"""
    simulation_id: int
    status: str
    progress: Optional[float] = None  # Percentage 0-100
    details: Dict[str, Any] = {}
    last_updated: Optional[datetime] = None

class SimulationResult(BaseModel):
    """Schema for simulation results"""
    simulation_id: int
    machine_model_id: int
    status: str
    execution_time: Optional[float] = None  # seconds
    results: Dict[str, Any] = {}
    completed_at: Optional[datetime] = None
