import requests
import time
import json

# --- Configuration ---
BASE_URL = "http://127.0.0.1:7778/api/v1" # Using port 7778 as specified
POLL_INTERVAL = 1.0 # seconds
POLL_COUNT = 15 # Number of times to poll simulation status

# --- Helper Functions ---
def api_request(method, endpoint, data=None, expected_status=(200, 201, 204)):
    """Sends an API request, checks status, and handles basic errors."""
    url = f"{BASE_URL}{endpoint}"
    print(f"-> {method} {url} {json.dumps(data) if data else ''}")
    response = None # Initialize response
    try:
        response = requests.request(method, url, json=data, timeout=10) # Added timeout
        if response.status_code not in expected_status:
             print(f"!! Unexpected Status Code: {response.status_code} (Expected: {expected_status})")
             print(f"   Response Body: {response.text}")
             response.raise_for_status() # Raise HTTPError to be caught below

        # Handle cases where response might be empty (e.g., DELETE 204)
        if response.status_code == 204 or not response.content:
            print(f"<- {response.status_code} (No Content)")
            return None

        response_json = response.json()
        print(f"<- {response.status_code} {json.dumps(response_json)}")
        return response_json
    except requests.exceptions.RequestException as e:
        print(f"!! API Request Error ({method} {url}): {e}")
        if response is not None:
            print(f"   Response Body: {response.text}")
        return None
    except json.JSONDecodeError:
        print(f"!! API Response Error: Could not decode JSON from {method} {url}")
        print(f"   Response Body: {response.text}")
        return None

# --- Test Steps ---
def run_test():
    project_id = None
    model_id = None
    sensor_id = None
    heater_id = None # Added Heater
    actuator_id = None
    connection1_id = None # Sensor -> Heater
    connection2_id = None # Heater -> Actuator
    simulation_id = None

    try:
        print("--- Test Setup ---")

        # 1. Create Project
        project_data = {"name": "Test Dependency Project", "description": "Testing Sensor->Heater->Actuator dependency"}
        project = api_request("POST", "/projects/", data=project_data, expected_status=(201,))
        if not project: return
        project_id = project["id"]
        print(f"Created Project ID: {project_id}")

        # 2. Create Machine Model
        model_data = {"name": "SensorHeaterActuatorModel", "project_id": project_id}
        model = api_request("POST", "/machine-models/", data=model_data, expected_status=(201,))
        if not model: return
        model_id = model["id"]
        print(f"Created Machine Model ID: {model_id}")

        # 3. Create Sensor Component
        # Configure sensor to output a sine wave crossing 0.5
        # Configure sensor to output a sine wave crossing 50 (Heater setpoint target)
        sensor_config = {"frequency": 0.05, "amplitude": 60.0, "offset": 20.0} # Oscillates between -40 and 80
        sensor_data = {"name": "SetpointSensor", "type": "Sensor", "config": sensor_config, "machine_model_id": model_id}
        sensor = api_request("POST", "/components/", data=sensor_data, expected_status=(201,))
        if not sensor: return
        sensor_id = sensor["id"]
        print(f"Created Sensor Component ID: {sensor_id}")

        # 4. Create Heater Component
        heater_config = {"heating_rate": 10.0, "initial_temp": 15.0} # Heats towards input setpoint
        heater_data = {"name": "IntermediateHeater", "type": "Heater", "config": heater_config, "machine_model_id": model_id}
        heater = api_request("POST", "/components/", data=heater_data, expected_status=(201,))
        if not heater: return
        heater_id = heater["id"]
        print(f"Created Heater Component ID: {heater_id}")

        # 5. Create Actuator Component
        # Actuator turns on if heater temperature > 40
        actuator_config = {"threshold": 40.0}
        actuator_data = {"name": "FinalActuator", "type": "Actuator", "config": actuator_config, "machine_model_id": model_id}
        actuator = api_request("POST", "/components/", data=actuator_data, expected_status=(201,))
        if not actuator: return
        actuator_id = actuator["id"]
        print(f"Created Actuator Component ID: {actuator_id}")

        # 6. Create Connection 1 (Sensor.value -> Heater.setpoint)
        connection1_data = {
            "machine_model_id": model_id,
            "source_component_id": sensor_id,
            "target_component_id": heater_id,
            "source_port": "value",       # Output port of Sensor
            "target_port": "setpoint"     # Input port of Heater
        }
        connection1 = api_request("POST", "/connections/", data=connection1_data, expected_status=(201,))
        if not connection1: return
        connection1_id = connection1["id"]
        print(f"Created Connection 1 ID: {connection1_id} (Sensor.value -> Heater.setpoint)")

        # 7. Create Connection 2 (Heater.temperature -> Actuator.command)
        connection2_data = {
            "machine_model_id": model_id,
            "source_component_id": heater_id,
            "target_component_id": actuator_id,
            "source_port": "temperature", # Output port of Heater
            "target_port": "command"      # Input port of Actuator
        }
        connection2 = api_request("POST", "/connections/", data=connection2_data, expected_status=(201,))
        if not connection2: return
        connection2_id = connection2["id"]
        print(f"Created Connection 2 ID: {connection2_id} (Heater.temperature -> Actuator.command)")

        print("\n--- Running Simulation ---")

        # 8. Start Simulation
        start_data = {"machine_model_id": model_id} # Simpler start request if parameters not needed
        sim_start_response = api_request("POST", "/simulations/start", data=start_data, expected_status=(200, 201)) # Start might return 200 or 201
        if not sim_start_response or "simulation_id" not in sim_start_response:
             print(f"Failed to start simulation or get simulation_id. Response: {sim_start_response}")
             return
        simulation_id = sim_start_response["simulation_id"]
        print(f"Started Simulation ID: {simulation_id}")

        # Give simulation a moment to start properly
        time.sleep(2.0)

        # 9. Poll Simulation Status
        print("\n--- Polling Simulation State ---")
        print(f"{'SimTime':<8} | {'SensorOut':<11} | {'HeaterTemp':<12} | {'ActuatorStatus':<15}")
        print("-" * 50)
        for i in range(POLL_COUNT):
            sim_state = api_request("GET", f"/simulations/{simulation_id}/status")
            if not sim_state:
                print(f"Failed to get simulation status for ID: {simulation_id}")
                break # Exit polling if status check fails

            sim_status = sim_state.get("status")
            if sim_status != "running":
                print(f"Simulation {simulation_id} no longer running. Status: {sim_status}. Error: {sim_state.get('error_message')}")
                break
            # Access component states nested under 'details'
            details = sim_state.get("details", {})
            # Calculate elapsed time relative to simulation start time
            start_time = details.get("start_time")
            current_sim_time = (time.time() - start_time) if start_time else 0.0
            comp_states = details.get("component_states", {})

            # Get states for all components, handling potential missing keys
            sensor_state = comp_states.get(str(sensor_id), {})
            heater_state = comp_states.get(str(heater_id), {})
            actuator_state = comp_states.get(str(actuator_id), {})

            sensor_value = sensor_state.get("value", "N/A")
            heater_temp = heater_state.get("temperature", "N/A")
            actuator_status = actuator_state.get("status", "N/A")

            # Format for printing
            sensor_val_str = f"{sensor_value:.2f}" if isinstance(sensor_value, float) else str(sensor_value)
            heater_temp_str = f"{heater_temp:.2f}" if isinstance(heater_temp, float) else str(heater_temp)

            print(f"{current_sim_time:<8.2f} | {sensor_val_str:<11} | {heater_temp_str:<12} | {actuator_status:<15}")

            time.sleep(POLL_INTERVAL)

    finally:
        print("\n--- Test Cleanup ---")
        # 10. Stop Simulation (if running)
        # Check sim_status exists before using it (in case loop didn't run)
        sim_status_at_end = sim_state.get("status") if 'sim_state' in locals() else None
        if simulation_id and sim_status_at_end == "running":
            print(f"Stopping Simulation ID: {simulation_id}")
            # Stop endpoint expects POST /simulations/stop with {"simulation_id": ...} in body
            stop_data = {"simulation_id": simulation_id}
            stop_response = api_request("POST", "/simulations/stop", data=stop_data, expected_status=(200,))

            if stop_response:
                 print(f"Stop signal sent. Response: {stop_response}")
            else:
                 print("Failed to send stop signal or get confirmation.")

        # 11. Cleanup: Delete created resources
        if connection2_id: api_request("DELETE", f"/connections/{connection2_id}", expected_status=(200,))
        if connection1_id: api_request("DELETE", f"/connections/{connection1_id}", expected_status=(200,))
        if actuator_id: api_request("DELETE", f"/components/{actuator_id}", expected_status=(200,))
        if heater_id: api_request("DELETE", f"/components/{heater_id}", expected_status=(200,))
        if sensor_id: api_request("DELETE", f"/components/{sensor_id}", expected_status=(200,))
        if model_id: api_request("DELETE", f"/machine-models/{model_id}", expected_status=(200,))
        if project_id: api_request("DELETE", f"/projects/{project_id}", expected_status=(200,))
        print("Cleanup attempt complete.")


if __name__ == "__main__":
    print("Starting Simulation Dependency Test...")
    print(f"Targeting Base URL: {BASE_URL}")
    # Add a small delay to ensure the server is ready if just started
    time.sleep(1)
    run_test()
    print("\nTest Finished.")