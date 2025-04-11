import requests
import time
import json
import sys

# --- Configuration ---
# Ensure this matches the port your FastAPI app is running on
BASE_URL = "http://127.0.0.1:7778/api/v1" # Using port 7778 as specified

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
def run_binding_test():
    project_id = None
    model_id = None
    component_id = None
    binding_id = None

    try:
        print("\n--- Test Setup: Creating Prerequisites ---")

        # 1. Create Project
        project_data = {"name": "Binding Test Project", "description": "Testing Communication Bindings API"}
        project = api_request("POST", "/projects/", data=project_data, expected_status=(201,))
        if not project: sys.exit("Failed to create project.")
        project_id = project["id"]

        # 2. Create Machine Model
        model_data = {"name": "BindingTestModel", "project_id": project_id}
        model = api_request("POST", "/machine-models/", data=model_data, expected_status=(201,)) # Use hyphenated path
        if not model: sys.exit("Failed to create machine model.")
        model_id = model["id"]

        # 3. Create Component
        component_data = {"name": "TestComponentForBinding", "type": "Generic", "config": {}, "machine_model_id": model_id}
        component = api_request("POST", "/components/", data=component_data, expected_status=(201,))
        if not component: sys.exit("Failed to create component.")
        component_id = component["id"]

        print("\n--- Testing Communication Binding CRUD ---")

        # 4. Create Communication Binding
        binding_data_create = {
            "machine_model_id": model_id,
            "component_id": component_id,
            "component_port": "temperature",
            "direction": "read",
            "protocol": "OPCUA",
            "address": "ns=2;s=MyDevice.Temp",
            "config": {"sampling_interval": 500}
        }
        binding = api_request("POST", f"/machine_models/{model_id}/communication_bindings/", data=binding_data_create, expected_status=(201,))
        if not binding: sys.exit("Failed to create communication binding.")
        binding_id = binding["id"]
        assert binding["component_port"] == "temperature"
        assert binding["address"] == "ns=2;s=MyDevice.Temp"
        assert binding["direction"] == "read"

        # 5. Read Binding (Individual)
        binding_read = api_request("GET", f"/communication_bindings/{binding_id}")
        if not binding_read: sys.exit("Failed to read communication binding by ID.")
        assert binding_read["id"] == binding_id
        assert binding_read["protocol"] == "OPCUA"

        # 6. Read Bindings (List for Model)
        bindings_list = api_request("GET", f"/machine_models/{model_id}/communication_bindings/")
        if bindings_list is None: sys.exit("Failed to list communication bindings for model.") # Allow empty list []
        assert isinstance(bindings_list, list)
        found = any(b["id"] == binding_id for b in bindings_list)
        assert found, f"Created binding {binding_id} not found in list for model {model_id}"

        # 7. Update Binding
        binding_data_update = {
            "component_port": "pressure",
            "direction": "write",
            "address": "ns=3;s=Another.Var",
            "config": {"write_mask": 1}
        }
        binding_updated = api_request("PUT", f"/communication_bindings/{binding_id}", data=binding_data_update)
        if not binding_updated: sys.exit("Failed to update communication binding.")
        assert binding_updated["id"] == binding_id
        assert binding_updated["component_port"] == "pressure"
        assert binding_updated["direction"] == "write"
        assert binding_updated["address"] == "ns=3;s=Another.Var"
        assert binding_updated["config"] == {"write_mask": 1}

        print("\n--- CRUD Tests Passed ---")

    except Exception as e:
        print(f"\n--- Test Failed: {e} ---")
    finally:
        print("\n--- Test Cleanup ---")
        # Delete in reverse order of creation
        if binding_id:
            print(f"Deleting Binding ID: {binding_id}")
            api_request("DELETE", f"/communication_bindings/{binding_id}", expected_status=(200,)) # DELETE often returns 200 with body or 204 no content
        if component_id:
            print(f"Deleting Component ID: {component_id}")
            api_request("DELETE", f"/components/{component_id}", expected_status=(200,))
        if model_id:
            print(f"Deleting Machine Model ID: {model_id}")
            api_request("DELETE", f"/machine-models/{model_id}", expected_status=(200,))
        if project_id:
            print(f"Deleting Project ID: {project_id}")
            api_request("DELETE", f"/projects/{project_id}", expected_status=(200,))
        print("Cleanup attempt complete.")


if __name__ == "__main__":
    print("Starting Communication Binding API Test...")
    print(f"Targeting Base URL: {BASE_URL}")
    # Add a small delay to ensure the server is ready if just started
    time.sleep(1)
    run_binding_test()
    print("\nTest Finished.")