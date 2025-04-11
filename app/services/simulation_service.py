# app/services/simulation_service.py

import asyncio
import time
import math # For sine wave example
import logging # Ensure logging is imported
from typing import Dict, Any, Optional, List
from collections import deque, defaultdict
from pydantic import BaseModel
from sqlalchemy.orm import Session
import fmpy # Import fmpy for FMU handling
from fmpy.fmi2 import FMU2Slave # Specific type for FMI 2.0 Co-Simulation

logger = logging.getLogger(__name__) # Ensure logger is defined

# Import CRUD and models/schemas needed for loading
from app.crud import crud_component, crud_connection, crud_communication_binding
from app.models.component import Component as ComponentModel
from app.schemas.connection import Connection as ConnectionSchema # To store connection info
from app.schemas.communication_binding import CommunicationBinding as CommunicationBindingSchema # For loading bindings

# Import Communication Service (assuming singleton instance for now)
from .communication_service import communication_service, CommunicationService

# --- Data Structures ---

class ComponentInfo(BaseModel):
    """Simplified component data stored in simulation state"""
    id: int
    name: str
    type: str
    config: Optional[Dict[str, Any]] = None

class SimulationState(BaseModel):
    simulation_id: int
    machine_model_id: int
    status: str = "pending" # e.g., pending, running, stopped, error
    start_time: Optional[float] = None
    components: List[ComponentInfo] = [] # Store loaded components
    connections: List[ConnectionSchema] = [] # Store loaded internal connections
    communication_bindings: List[CommunicationBindingSchema] = [] # Store loaded external bindings
    component_states: Dict[int, Dict[str, Any]] = {} # Store state/outputs from the *previous* step {component_id: {"output_value": ...}}
    execution_order: List[int] = [] # Order in which to execute components
    error_message: Optional[str] = None
    comm_service: Optional[CommunicationService] = None # Runtime reference, not serialized
    fmu_instances: Dict[int, FMU2Slave] = {} # Store instantiated FMU models {component_id: fmu_instance}

    model_config = {
        "arbitrary_types_allowed": True
    }

# --- Simulation Management ---

# In-memory store for active simulations (replace with DB/cache for persistence if needed)
_active_simulations: Dict[int, SimulationState] = {}
_next_simulation_id = 1

# --- Service Functions ---

async def create_and_start_simulation(db: Session, machine_model_id: int, simulation_mode: str = "pure") -> SimulationState:
    """
    Creates a new simulation instance, assigns an ID, and starts its execution loop (async).
    Supports different modes like 'pure' (internal only) or 'hil' (Hardware-in-the-Loop).
    """
    global _next_simulation_id
    sim_id = _next_simulation_id
    _next_simulation_id += 1

    # Load components for the model
    print(f"Service: Loading components for model {machine_model_id}")
    try:
        db_components = crud_component.component.get_multi_by_machine_model(db=db, machine_model_id=machine_model_id, limit=1000) # Call method on the 'component' instance
        loaded_components = [
            ComponentInfo(id=c.id, name=c.name, type=c.type, config=c.config)
            for c in db_components
        ]
        print(f"Service: Found {len(loaded_components)} components.")
    except Exception as e:
        print(f"Service Error: Failed to load components for model {machine_model_id}: {e}")
        # Handle error appropriately, maybe raise exception or return error state
        raise e # Re-raise for now

    # Load connections for the model
    print(f"Service: Loading connections for model {machine_model_id}")
    try:
        # Assuming a similar CRUD function exists for connections
        db_connections = crud_connection.connection.get_multi_by_machine_model(db=db, machine_model_id=machine_model_id, limit=5000)
        loaded_connections = [ConnectionSchema.model_validate(c) for c in db_connections] # Validate using Pydantic schema
        print(f"Service: Found {len(loaded_connections)} connections.")
    except Exception as e:
        print(f"Service Error: Failed to load connections for model {machine_model_id}: {e}")
        # Handle error appropriately
        raise e # Re-raise for now

    # Load communication bindings if in HIL mode
    loaded_bindings = []
    if simulation_mode == "hil":
        print(f"Service: Loading communication bindings for HIL mode (model {machine_model_id})")
        try:
            db_bindings = crud_communication_binding.communication_binding.get_multi_by_machine_model(db=db, machine_model_id=machine_model_id, limit=5000)
            loaded_bindings = [CommunicationBindingSchema.model_validate(b) for b in db_bindings]
            print(f"Service: Found {len(loaded_bindings)} communication bindings.")
        except Exception as e:
            print(f"Service Error: Failed to load communication bindings for model {machine_model_id}: {e}")
            # Decide how to handle: maybe prevent HIL start?
            # For now, log and continue without bindings for HIL
            loaded_bindings = [] # Ensure it's empty on error

    new_sim = SimulationState(
        simulation_id=sim_id,
        machine_model_id=machine_model_id,
        status="starting",
        components=loaded_components,
        connections=loaded_connections,
        communication_bindings=loaded_bindings, # Add loaded bindings
        component_states={comp.id: {} for comp in loaded_components}, # Initialize state dict
        execution_order=[], # Will be populated below
        comm_service=communication_service if simulation_mode == "hil" else None, # Assign comm service if HIL
        fmu_instances={} # Initialize FMU instance dictionary
    )
    _active_simulations[sim_id] = new_sim

    # Calculate execution order
    try:
        new_sim.execution_order = _get_execution_order(new_sim.components, new_sim.connections)
        print(f"Service: Calculated execution order for sim {sim_id}: {new_sim.execution_order}")
    except Exception as e:
        print(f"Service Error: Failed to calculate execution order for sim {sim_id}: {e}")
        # Decide how to handle: stop simulation, use default order, etc.
        # For now, let's use the default order and log the error.
        new_sim.execution_order = [comp.id for comp in new_sim.components]
        new_sim.status = "error"
        new_sim.error_message = f"Failed to determine execution order: {e}"
        # Don't start the loop if order calculation fails critically
        # return new_sim # Or raise an error

    # --- Initialize FMUs ---
    fmu_load_successful = True
    for comp in new_sim.components:
        if comp.type == 'FMU':
            fmu_path = comp.config.get('fmu_path') if comp.config else None
            if not fmu_path:
                logger.error(f"FMU component {comp.id} ('{comp.name}') is missing 'fmu_path' in config.")
                new_sim.status = "error"
                new_sim.error_message = f"FMU component {comp.id} missing fmu_path."
                fmu_load_successful = False
                break # Stop loading FMUs if one fails critically

            logger.info(f"Loading FMU for component {comp.id} from path: {fmu_path}")
            try:
                # 1. Read model description
                model_description = fmpy.read_model_description(fmu_path)

                # 2. Extract GUID
                guid = model_description.guid

                # 3. Unpack FMU
                unzipdir = fmpy.extract(fmu_path)

                # 4. Instantiate FMU (assuming FMI 2.0 Co-Simulation)
                # TODO: Add logic to handle FMI versions and types (ModelExchange vs CoSimulation)
                fmu_instance = FMU2Slave(guid=guid,
                                         unzipDirectory=unzipdir,
                                         modelIdentifier=model_description.coSimulation.modelIdentifier,
                                         instanceName=comp.name) # Use component name for instance name
                fmu_instance.instantiate()
                logger.info(f"Instantiated FMU for component {comp.id} ('{comp.name}')")

                # TODO: Setup experiment (optional, depends on FMU needs)
                # fmu_instance.setupExperiment(startTime=0.0)

                # TODO: Enter initialization mode (optional, depends on FMU needs)
                # fmu_instance.enterInitializationMode()
                # fmu_instance.exitInitializationMode()

                # Store the instance
                new_sim.fmu_instances[comp.id] = fmu_instance

            except Exception as e:
                logger.error(f"Failed to load or instantiate FMU '{fmu_path}' for component {comp.id}: {e}", exc_info=True)
                new_sim.status = "error"
                new_sim.error_message = f"Failed to load FMU for component {comp.id}: {e}"
                fmu_load_successful = False
                # Clean up already loaded FMUs before breaking
                for loaded_fmu_id, loaded_fmu_instance in new_sim.fmu_instances.items():
                    try:
                        loaded_fmu_instance.terminate()
                        loaded_fmu_instance.freeInstance()
                    except Exception as cleanup_err:
                        logger.error(f"Error cleaning up FMU instance for component {loaded_fmu_id} after load failure: {cleanup_err}")
                new_sim.fmu_instances.clear()
                break # Stop loading further FMUs

    # --- Initialize Communication Service (only if FMUs loaded successfully) ---
    if fmu_load_successful and simulation_mode == "hil" and new_sim.comm_service and new_sim.communication_bindings:
        logger.info(f"Initializing Communication Service for sim {sim_id}")
        try:
            await new_sim.comm_service.initialize_connections(new_sim.communication_bindings)
            logger.info(f"Communication Service initialized for sim {sim_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Communication Service for sim {sim_id}: {e}")
            new_sim.status = "error"
            new_sim.error_message = f"Failed to initialize communication: {e}"
            # Clean up potentially partially initialized comm service?
            if new_sim.comm_service:
                 await new_sim.comm_service.disconnect_all() # Attempt cleanup
            # Also clean up FMUs if comms init fails
            for fmu_instance in new_sim.fmu_instances.values():
                try:
                    fmu_instance.terminate()
                    fmu_instance.freeInstance()
                except Exception as fmu_cleanup_err:
                    logger.error(f"Error cleaning up FMU instance after comms failure: {fmu_cleanup_err}")
            new_sim.fmu_instances.clear()
    # Start the simulation loop in the background only if status is not error
    if new_sim.status != "error":
        # Pass the simulation mode to the loop runner
        asyncio.create_task(_run_simulation_loop(sim_id, simulation_mode))

    print(f"Service: Created simulation {sim_id} for model {machine_model_id} in '{simulation_mode}' mode")
    return new_sim

async def stop_simulation(simulation_id: int) -> bool:
    """
    Stops a running simulation.
    """
    if simulation_id not in _active_simulations:
        print(f"Service: Stop failed - Simulation {simulation_id} not found.")
        return False

    sim = _active_simulations[simulation_id]
    if sim.status == "running" or sim.status == "starting":
        sim.status = "stopping" # Signal the loop to stop
        print(f"Service: Signaled simulation {simulation_id} to stop.")
        # The loop itself will update status to "stopped" and handle comms disconnect
        return True
    elif sim.status in ["stopped", "error", "pending", "stopping"]:
         print(f"Service: Simulation {simulation_id} is already stopping or stopped ({sim.status}).")
         # If it's an error state, maybe try to ensure comms are disconnected anyway
         if sim.comm_service:
             print(f"Service: Ensuring communication service is disconnected for sim {simulation_id} in state {sim.status}.")
             # Run disconnect in background to not block the stop request
             asyncio.create_task(sim.comm_service.disconnect_all())
         return True # Indicate stop signal was acknowledged or already stopped/stopping
    else:
        print(f"Service: Stop failed - Simulation {simulation_id} in unexpected state ({sim.status}).")
        return False

def get_simulation_state(simulation_id: int) -> Optional[SimulationState]:
    """
    Retrieves the current state of a simulation.
    """
    return _active_simulations.get(simulation_id)

# --- Topological Sort Helper ---

def _get_execution_order(components: List[ComponentInfo], connections: List[ConnectionSchema]) -> List[int]:
    """
    Calculates the execution order of components based on dependencies using topological sort (Kahn's algorithm).
    Returns a list of component IDs in execution order.
    Raises ValueError if a cycle is detected.
    """
    adj = defaultdict(list)
    in_degree = defaultdict(int)
    component_ids = {comp.id for comp in components}

    # Initialize in-degree for all components
    for comp_id in component_ids:
        in_degree[comp_id] = 0

    # Build adjacency list and calculate in-degrees
    for conn in connections:
        source_id = conn.source_component_id
        target_id = conn.target_component_id
        # Ensure both source and target are part of the simulation's components
        if source_id in component_ids and target_id in component_ids:
            # Check if the edge already exists to avoid duplicate increments
            if target_id not in adj[source_id]:
                adj[source_id].append(target_id)
                in_degree[target_id] += 1

    # Initialize queue with nodes having in-degree 0
    queue = deque([comp_id for comp_id in component_ids if in_degree[comp_id] == 0])
    sorted_order = []

    while queue:
        u = queue.popleft()
        sorted_order.append(u)

        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    # Check for cycles
    if len(sorted_order) != len(component_ids):
        # Identify components involved in cycles (those with in_degree > 0)
        cycle_nodes = {comp_id for comp_id in component_ids if in_degree[comp_id] > 0}
        print(f"Warning: Cycle detected in component graph involving components: {cycle_nodes}. Falling back to default order.")
        # Fallback: return original order or raise error
        # raise ValueError(f"Cycle detected in component graph involving components: {cycle_nodes}")
        return [comp.id for comp in components] # Fallback to original order

    return sorted_order


# --- Simulation Loop (Internal) ---

async def _run_simulation_loop(simulation_id: int, simulation_mode: str):
    """
    The core loop for a single simulation instance. Runs asynchronously.
    Handles both 'pure' and 'hil' modes.
    """
    if simulation_id not in _active_simulations:
        print(f"Service Loop Error: Simulation {simulation_id} not found at start.")
        return

    sim = _active_simulations[simulation_id]
    sim.status = "running"
    sim.start_time = time.time()
    print(f"Service Loop: Simulation {simulation_id} started.")

    # Create a mapping from ID to ComponentInfo for quick lookup
    component_map = {comp.id: comp for comp in sim.components}

    try:
        # --- Simulation Core Logic ---
        step_count = 0
        while sim.status == "running":
            step_count += 1
            current_time = time.time() - sim.start_time

            # --- HIL Mode: Read Inputs from External System ---
            external_inputs: Dict[int, Any] = {} # {binding_id: value}
            if simulation_mode == "hil" and sim.comm_service:
                try:
                    external_inputs = await sim.comm_service.read_values_from_external()
                    # print(f"SimLoop[{simulation_id}] Read external inputs: {external_inputs}") # Verbose
                except Exception as e:
                    print(f"SimLoop Error [{simulation_id}]: Failed to read external values: {e}")
                    # Decide how to handle: stop simulation, continue with old values?
                    # For now, log and continue
                    pass # Continue with potentially empty external_inputs

            # --- Execute Component Logic in Dependency Order ---
            next_component_states: Dict[int, Dict[str, Any]] = {} # Store results for *this* step

            for comp_id in sim.execution_order:
                # Get component info using the map
                comp_info = component_map.get(comp_id)
                if not comp_info:
                    print(f"Warning: Component ID {comp_id} from execution order not found in component map. Skipping.")
                    continue # Should not happen if execution order is derived correctly

                comp_type = comp_info.type
                comp_config = comp_info.config or {}

                # --- Gather Inputs ---
                inputs: Dict[str, Any] = {} # Key: target_port_name, Value: input_value

                # 1. Gather inputs from internal connections (previous step state)
                for conn in sim.connections:
                    if conn.target_component_id == comp_id and conn.target_port and conn.source_port:
                        source_id = conn.source_component_id
                        source_port_name = conn.source_port
                        target_port_name = conn.target_port
                        source_state_previous_step = sim.component_states.get(source_id, {})
                        value = source_state_previous_step.get(source_port_name)
                        if value is not None:
                            inputs[target_port_name] = value
                        # else: # Optional: Log warning for missing internal input
                        #     print(f"Warning: Internal input '{source_port_name}' from {source_id} not found for {comp_id}:{target_port_name}")

                # 2. Gather inputs from external communication bindings (HIL mode)
                if simulation_mode == "hil" and sim.communication_bindings:
                    for binding in sim.communication_bindings:
                        # Check if this binding reads from external and writes to this component's port
                        if binding.direction == 'read' and binding.component_id == comp_id and binding.component_port:
                            target_port_name = binding.component_port
                            # Get the value read from external system in this step
                            external_value = external_inputs.get(binding.id)
                            if external_value is not None:
                                # print(f"  HIL Input for {comp_info.name} ({comp_id}) port '{target_port_name}' from binding {binding.id}: {external_value}") # Verbose
                                inputs[target_port_name] = external_value
                            # else: # Optional: Log warning for missing external input
                            #     print(f"Warning: External input for binding {binding.id} not found for {comp_id}:{target_port_name}")

                # print(f"  Inputs gathered for {comp_info.name} ({comp_id}): {inputs}") # Verbose

                # Execute logic based on type
                output_state = {}
                if comp_type == 'Sensor':
                    # Example: Sine wave sensor based on time
                    frequency = comp_config.get('frequency', 0.1) # Hz
                    amplitude = comp_config.get('amplitude', 1.0)
                    offset = comp_config.get('offset', 0.0)
                    output_value = offset + amplitude * math.sin(2 * math.pi * frequency * current_time)
                    output_state = {"value": output_value}
                    # print(f"  Sensor {comp_info.name} ({comp_id}): {output_value:.3f}") # Verbose logging

                elif comp_type == 'Heater':
                    # Basic Heater Logic: Increase temperature towards a setpoint, potentially driven by input
                    # Configurable parameters (with defaults)
                    # --- Heater Logic ---
                    # Configurable parameters (with defaults)
                    config_setpoint = comp_config.get('setpoint', 50.0)
                    heating_rate = comp_config.get('heating_rate', 5.0) # degrees per second when heating
                    cooling_rate = comp_config.get('cooling_rate', 1.0) # degrees per second when cooling
                    ambient_temp = comp_config.get('ambient_temp', 20.0) # Minimum temperature
                    initial_temp = comp_config.get('initial_temp', ambient_temp)
                    time_step = 1.0 # Corresponds to asyncio.sleep(1.0) later

                    # Get previous state
                    previous_step_state = sim.component_states.get(comp_id, {})
                    current_temp = previous_step_state.get('temperature', initial_temp)

                    # Determine the target setpoint (from input or config)
                    target_setpoint = config_setpoint
                    input_setpoint = inputs.get('setpoint') # Assuming target port is named 'setpoint'
                    if input_setpoint is not None and isinstance(input_setpoint, (int, float)):
                        target_setpoint = input_setpoint
                        # logger.debug(f"  Heater {comp_info.name} using input setpoint: {target_setpoint}")

                    # Calculate new temperature
                    new_temp = current_temp
                    delta_temp = 0.0
                    if current_temp < target_setpoint:
                        # Heating
                        increase = heating_rate * time_step
                        potential_temp = current_temp + increase
                        new_temp = min(potential_temp, target_setpoint) # Don't overshoot target
                        delta_temp = new_temp - current_temp
                    elif current_temp > target_setpoint:
                        # Cooling
                        decrease = cooling_rate * time_step
                        potential_temp = current_temp - decrease
                        # Ensure we don't cool below ambient or the target setpoint if it's higher than ambient
                        floor_temp = max(ambient_temp, target_setpoint if target_setpoint > ambient_temp else ambient_temp)
                        new_temp = max(potential_temp, floor_temp) # Don't undershoot floor
                        delta_temp = new_temp - current_temp

                    # logger.debug(f"  Heater {comp_info.name} ({comp_id}): Current={current_temp:.2f}, Target={target_setpoint:.2f}, Delta={delta_temp:.2f}, New={new_temp:.2f}")

                    output_state = {"temperature": new_temp} # Output port named 'temperature'

                elif comp_type == 'Actuator':
                    # Basic Actuator Logic: Turn On/Off based on input threshold
                    # Configurable parameters
                    threshold = comp_config.get('threshold', 0.5)
                    input_value = None

                    # Determine input value from 'command' port
                    input_command = inputs.get('command') # Assuming target port is named 'command'
                    if input_command is not None and isinstance(input_command, (int, float)):
                        input_value = input_command
                        # print(f"  Actuator {comp_info.name} using input command: {input_value}") # Verbose
                    else:
                        input_value = None # No valid command input

                    # Determine state based on input and threshold
                    if input_value is not None and input_value >= threshold:
                        actuator_status = "On"
                    else:
                        actuator_status = "Off" # Default to Off if no input or below threshold

                    output_state = {"status": actuator_status} # Output port named 'status'
                    # print(f"  Actuator {comp_info.name} ({comp_id}): {actuator_status}") # Verbose logging

                elif comp_type == 'Valve':
                    # Basic Valve Logic: Open/Close based on control signal
                    # Configurable parameters (optional, none needed for basic logic)
                    threshold = comp_config.get('threshold', 0.5) # Threshold to open
                    input_value = None

                    # Determine input value from 'ControlSignal' port
                    input_signal = inputs.get('ControlSignal') # Assuming target port is named 'ControlSignal'
                    if input_signal is not None and isinstance(input_signal, (int, float)):
                        input_value = input_signal
                        # print(f"  Valve {comp_info.name} using input signal: {input_value}") # Verbose
                    else:
                        input_value = None # No valid signal input

                    # Determine state based on input and threshold
                    if input_value is not None and input_value > threshold:
                        valve_flow = 1.0 # Open
                    else:
                        valve_flow = 0.0 # Closed (default if no input or below threshold)

                    output_state = {"Flow": valve_flow} # Output port named 'Flow'
                    # print(f"  Valve {comp_info.name} ({comp_id}): Flow={valve_flow}") # Verbose logging

                elif comp_type == 'FMU':
                    # --- FMU Execution Logic ---
                    fmu_instance = sim.fmu_instances.get(comp_id)
                    if not fmu_instance:
                        logger.warning(f"FMU instance for component {comp_id} not found in simulation state. Skipping.")
                        output_state = {"status": "error_fmu_not_found"}
                    else:
                        try:
                            # 1. Set FMU inputs based on gathered inputs
                            #    Assumption: Input port name == FMU variable name, Type == Real
                            #    TODO: Need proper mapping from port name to FMU variable ValueReference and type handling
                            input_vars = [] # Collect variable names for logging/debugging
                            for port_name, value in inputs.items():
                                try:
                                    # Attempt to get variable by name (less efficient but simpler for now)
                                    # A better approach uses ValueReferences obtained during loading
                                    variable = fmu_instance.modelDescription.modelVariables[port_name]
                                    vr = [variable.valueReference]
                                    # Basic type handling (extend as needed)
                                    if variable.type == 'Real':
                                        fmu_instance.setReal(vr, [float(value)])
                                    elif variable.type == 'Integer' or variable.type == 'Enumeration':
                                         fmu_instance.setInteger(vr, [int(value)])
                                    elif variable.type == 'Boolean':
                                         fmu_instance.setBoolean(vr, [bool(value)])
                                    # Add String etc. if needed
                                    else:
                                         logger.warning(f"FMU {comp_id}: Unsupported input variable type '{variable.type}' for variable '{port_name}'. Skipping set.")
                                         continue
                                    input_vars.append(f"{port_name}={value}")
                                except KeyError:
                                     logger.warning(f"FMU {comp_id}: Input variable '{port_name}' not found in FMU model description. Skipping set.")
                                except Exception as set_err:
                                    logger.error(f"FMU {comp_id}: Error setting input '{port_name}' to {value}: {set_err}")


                            # 2. Perform simulation step
                            step_size = 1.0 # Matches asyncio.sleep duration
                            # currentCommunicationPoint is the time at the beginning of the step
                            comm_point = current_time
                            # logger.debug(f"  FMU {comp_id}: doStep(current={comm_point:.3f}, stepSize={step_size}) Inputs: {', '.join(input_vars)}")
                            status = fmu_instance.doStep(currentCommunicationPoint=comm_point, communicationStepSize=step_size)
                            if status != fmpy.fmi2OK:
                                logger.error(f"FMU {comp_id}: doStep failed with status {status}")
                                # Handle error, maybe stop simulation?
                                output_state = {"status": f"error_doStep_{status}"}
                            else:
                                # 3. Get FMU outputs
                                #    Assumption: Output port name == FMU variable name, Type == Real
                                #    TODO: Need proper mapping and type handling using ValueReferences
                                output_state = {}
                                for variable in fmu_instance.modelDescription.modelVariables:
                                    # Simple check if variable is an output (causality='output')
                                    # This assumes component ports are named exactly like FMU output variables
                                    if variable.causality == 'output':
                                        vr = [variable.valueReference]
                                        var_name = variable.name
                                        try:
                                            if variable.type == 'Real':
                                                value = fmu_instance.getReal(vr)[0]
                                            elif variable.type == 'Integer' or variable.type == 'Enumeration':
                                                value = fmu_instance.getInteger(vr)[0]
                                            elif variable.type == 'Boolean':
                                                value = fmu_instance.getBoolean(vr)[0]
                                            # Add String etc. if needed
                                            else:
                                                logger.warning(f"FMU {comp_id}: Unsupported output variable type '{variable.type}' for variable '{var_name}'. Skipping get.")
                                                continue
                                            output_state[var_name] = value
                                        except Exception as get_err:
                                             logger.error(f"FMU {comp_id}: Error getting output '{var_name}': {get_err}")
                                # logger.debug(f"  FMU {comp_id}: Outputs: {output_state}")

                        except Exception as fmu_err:
                            logger.error(f"Error during FMU execution for component {comp_id}: {fmu_err}", exc_info=True)
                            output_state = {"status": "error_fmu_execution"}

                # Add more component types here...
                else:
                    # Unknown component type
                    logger.warning(f"Unknown component type '{comp_type}' encountered for component {comp_id}.")
                    output_state = {"status": "unknown_type"}

                # Store the calculated state for *this* step in the temporary dictionary
                next_component_states[comp_id] = output_state

            # --- Update Main State After Processing All Components in Step ---
            sim.component_states.update(next_component_states)

            # --- HIL Mode: Write Outputs to External System ---
            if simulation_mode == "hil" and sim.comm_service and sim.communication_bindings:
                values_to_write_external: Dict[int, Any] = {} # {binding_id: value}
                for binding in sim.communication_bindings:
                    # Check if this binding writes from this component's port to external
                    if binding.direction == 'write' and binding.component_id and binding.component_port:
                        source_comp_id = binding.component_id
                        source_port_name = binding.component_port
                        # Get the output value calculated in *this* step
                        current_comp_state = next_component_states.get(source_comp_id, {})
                        value_to_write = current_comp_state.get(source_port_name)

                        if value_to_write is not None:
                            # print(f"  HIL Output from {source_comp_id}:{source_port_name} for binding {binding.id}: {value_to_write}") # Verbose
                            values_to_write_external[binding.id] = value_to_write
                        # else: # Optional: Log warning for missing output value for write binding
                        #     print(f"Warning: Output value '{source_port_name}' not found in component {source_comp_id} state for write binding {binding.id}")

                if values_to_write_external:
                    try:
                        # print(f"SimLoop[{simulation_id}] Writing external outputs: {values_to_write_external}") # Verbose
                        await sim.comm_service.write_values_to_external(values_to_write_external)
                    except Exception as e:
                        print(f"SimLoop Error [{simulation_id}]: Failed to write external values: {e}")
                        # Decide how to handle: stop simulation? log and continue?
                        # For now, log and continue
                        pass

            print(f"Service Loop [{simulation_id}]: Step {step_count}, Time {current_time:.2f}s, States: {sim.component_states}")

            # Simulate time step
            await asyncio.sleep(1.0) # Simulate 1 second time step

            # Check if stop was requested
            if sim.status == "stopping":
                break

        # --- End of Loop ---
        sim.status = "stopped"
        print(f"Service Loop: Simulation {simulation_id} stopped gracefully.")

    except Exception as e:
        sim.status = "error"
        sim.error_message = str(e)
        print(f"Service Loop Error [{simulation_id}]: {e}")
    finally:
        # --- Cleanup ---
        if sim: # Ensure sim object exists
            logger.info(f"Simulation {simulation_id} loop ending with status: {sim.status}. Starting cleanup.")
            # 1. Clean up FMU instances
            if sim.fmu_instances:
                logger.info(f"Terminating and freeing {len(sim.fmu_instances)} FMU instance(s) for sim {simulation_id}...")
                for comp_id, fmu_instance in sim.fmu_instances.items():
                    try:
                        fmu_instance.terminate()
                        fmu_instance.freeInstance()
                        logger.debug(f"Cleaned up FMU for component {comp_id}.")
                    except Exception as fmu_cleanup_err:
                        logger.error(f"Error cleaning up FMU instance for component {comp_id}: {fmu_cleanup_err}")
                sim.fmu_instances.clear() # Clear the dictionary after attempting cleanup

            # 2. Clean up Communication Service
            if sim.comm_service:
                logger.info(f"Cleaning up communication service for sim {simulation_id}...")
                try:
                    await sim.comm_service.disconnect_all()
                    logger.info(f"Communication service cleanup complete for sim {simulation_id}.")
                except Exception as comm_cleanup_err:
                     logger.error(f"Error cleaning up communication service for sim {simulation_id}: {comm_cleanup_err}")

            # 3. Update final status if not already error/stopped
            if sim.status not in ["error", "stopped"]:
                 logger.warning(f"Simulation {simulation_id} loop exited unexpectedly with status {sim.status}. Setting to 'stopped'.")
                 sim.status = "stopped" # Ensure final status is set

            logger.info(f"Simulation {simulation_id} cleanup finished. Final status: {sim.status}")
        else:
             logger.error(f"Simulation {simulation_id} loop ended but sim object was not found for cleanup.")

        # Remove simulation from active list? Or keep for final state inspection?
        # For now, keep it but ensure status reflects final state (stopped/error)