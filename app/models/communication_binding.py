# app/models/communication_binding.py

from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base # Import Base from the new base module

class CommunicationBinding(Base):
    __tablename__ = "communication_bindings"

    id = Column(Integer, primary_key=True, index=True)
    machine_model_id = Column(Integer, ForeignKey("machine_models.id"), nullable=False, index=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=False, index=True)
    component_port = Column(String, nullable=False, index=True) # e.g., "temperature", "status", "setpoint"
    direction = Column(String, nullable=False, index=True) # "read" (from PLC), "write" (to PLC)
    protocol = Column(String, nullable=False, default="OPCUA", index=True) # e.g., "OPCUA", "Modbus"
    address = Column(String, nullable=False) # e.g., OPC UA Node ID "ns=2;s=MyDevice.MyVariable"
    config = Column(JSON, nullable=True) # Optional protocol-specific config

    # Relationships (optional but useful)
    machine_model = relationship("MachineModel", back_populates="communication_bindings")
    component = relationship("Component", back_populates="communication_bindings")