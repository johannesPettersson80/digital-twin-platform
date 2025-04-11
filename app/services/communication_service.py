# app/services/communication_service.py

import asyncio
from typing import Dict, List, Any, Optional
from collections import defaultdict # Import defaultdict
from asyncua import Client, ua # Import asyncua

from app.schemas.communication_binding import CommunicationBinding # For type hinting

# Removed global placeholders, managed within the service instance now
# --- Subscription Handler ---
# Define SubHandler before CommunicationService uses it
class SubHandler:
    """
    Subscription Handler. To receive events from server for subscribed nodes.
    Needs access to the CommunicationService instance's state.
    """
    def __init__(self, comm_service_instance: 'CommunicationService'):
        self.comm_service = comm_service_instance

    def datachange_notification(self, node, val, data):
        node_id_str = node.nodeid.to_string()
        binding_id = self.comm_service.node_id_to_binding_id_map.get(node_id_str)
        if binding_id is not None:
            # print(f"OPC UA Subscription Update: Node {node_id_str} (Binding {binding_id}), New Value: {val}") # Verbose
            self.comm_service.binding_values[binding_id] = val # Update the central store
        else:
            print(f"Warning: Received datachange for unmapped node: {node_id_str}, Value: {val}")

    def event_notification(self, event):
        print("OPC UA Event Received: ", event)
        # Event handling logic can be added here if needed

class CommunicationService:
    """
    Manages connections and data exchange with external systems (initially OPC UA).
    """

    def __init__(self):
        # Initialize necessary state
        self.opcua_clients: Dict[str, Client] = {} # {endpoint_url: client}
        self.opcua_subscriptions: Dict[str, ua.Subscription] = {} # {endpoint_url: subscription}
        self.monitored_items: Dict[str, List[ua.MonitoredItem]] = defaultdict(list) # {endpoint_url: [items]}
        self.read_bindings: List[CommunicationBinding] = []
        self.write_bindings: List[CommunicationBinding] = []
        self.binding_values: Dict[int, Any] = {} # {binding_id: latest_value} - Updated by SubHandler
        self.node_id_to_binding_id_map: Dict[str, int] = {} # {opcua_node_id_string: binding_id} - Used by SubHandler
        self.sub_handler = SubHandler(self) # Pass instance to handler

    async def initialize_connections(self, bindings: List[CommunicationBinding]):
        """
        Establishes connections based on the unique server endpoints found in bindings.
        Separates bindings into read/write lists.
        """
        self.read_bindings = [b for b in bindings if b.direction == 'read']
        self.write_bindings = [b for b in bindings if b.direction == 'write']
        print(f"CommService: Initializing with {len(self.read_bindings)} read bindings and {len(self.write_bindings)} write bindings.")

        endpoints = {b.endpoint_url for b in bindings if b.endpoint_url}
        print(f"CommService: Found unique endpoints: {endpoints}")

        if not endpoints:
            print("CommService: No endpoints found in bindings. Skipping connection.")
            return

        for url in endpoints:
            if url in self.opcua_clients:
                print(f"CommService: Already connected to {url}. Skipping.")
                continue

            print(f"CommService: Attempting to connect to OPC UA server: {url}")
            client = Client(url=url)
            try:
                await client.connect()
                self.opcua_clients[url] = client
                print(f"CommService: Successfully connected to {url}")

                # Create subscription for this endpoint if there are read bindings for it
                endpoint_read_bindings = [b for b in self.read_bindings if b.endpoint_url == url]
                if endpoint_read_bindings:
                    print(f"CommService: Creating subscription for {url}")
                    subscription = await client.create_subscription(500, self.sub_handler) # Period ms, handler object
                    self.opcua_subscriptions[url] = subscription
                    print(f"CommService: Subscription created for {url}")

                    # Subscribe to nodes for read bindings
                    nodes_to_monitor = []
                    for binding in endpoint_read_bindings:
                        try:
                            node = client.get_node(binding.address)
                            nodes_to_monitor.append(node)
                            # Map node ID string back to our binding ID for the handler
                            node_id_str = node.nodeid.to_string()
                            self.node_id_to_binding_id_map[node_id_str] = binding.id
                            print(f"CommService: Prepared node {binding.address} (Binding {binding.id}) for monitoring.")
                        except Exception as node_err:
                            print(f"CommService Error: Failed to get node '{binding.address}' on {url} for binding {binding.id}: {node_err}")

                    if nodes_to_monitor:
                        print(f"CommService: Subscribing to {len(nodes_to_monitor)} nodes on {url}...")
                        handles = await subscription.subscribe_data_change(nodes_to_monitor)
                        # Store monitored item objects (optional, might be useful for unsubscribing later)
                        # Note: asyncua might return handles or MonitoredItem objects depending on version/context
                        # Assuming handles are sufficient for now, or that MonitoredItems are implicitly managed by subscription
                        print(f"CommService: Subscribed to data changes for nodes on {url}. Handles: {handles}")
                        # self.monitored_items[url].extend(handles) # Or store MonitoredItem objects if available/needed

            except Exception as e:
                print(f"CommService Error: Failed to connect or subscribe to {url}: {e}")
                # Clean up if connection failed partially
                if url in self.opcua_clients:
                    try:
                        await self.opcua_clients[url].disconnect()
                    except Exception: pass # Ignore errors during cleanup disconnect
                    del self.opcua_clients[url]
                if url in self.opcua_subscriptions: del self.opcua_subscriptions[url]
                # Remove any node mappings added for this failed endpoint
                keys_to_remove = [k for k, v in self.node_id_to_binding_id_map.items() if any(b.endpoint_url == url and b.id == v for b in self.read_bindings)]
                for k in keys_to_remove: del self.node_id_to_binding_id_map[k]

        print("CommService: Connection initialization complete.")

    async def disconnect_all(self):
        """
        Disconnects all active OPC UA connections.
        """
        print("CommService: Disconnecting all OPC UA clients...")
        # Disconnect clients gracefully
        disconnect_tasks = []
        for url, client in self.opcua_clients.items():
            print(f"CommService: Disconnecting from {url}...")
            disconnect_tasks.append(client.disconnect())

        if disconnect_tasks:
            results = await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            for url, result in zip(self.opcua_clients.keys(), results):
                if isinstance(result, Exception):
                    print(f"CommService Error: Failed to disconnect from {url}: {result}")
                else:
                    print(f"CommService: Disconnected from {url}")

        # Clear internal state
        self.opcua_clients.clear()
        self.opcua_subscriptions.clear()
        self.monitored_items.clear()
        self.binding_values.clear()
        self.node_id_to_binding_id_map.clear()
        self.read_bindings.clear()
        self.write_bindings.clear()
        print("CommService: All connections closed.")

    async def read_values_from_external(self) -> Dict[int, Any]:
        """
        Reads the latest values for all 'read' bindings.
        For OPC UA, this might involve checking the latest values received via subscription.
        Returns a dictionary mapping {binding_id: value}.
        """
        # Values are updated asynchronously by the SubHandler.
        # This function simply returns the current state of the values dictionary.
        # print(f"CommService: Returning current binding values: {self.binding_values}") # Verbose
        return self.binding_values.copy() # Return a copy to prevent external modification

    async def write_values_to_external(self, values_to_write: Dict[int, Any]):
        """
        Writes values to the external system based on 'write' bindings.
        Input: Dictionary mapping {binding_id: value_to_write}.
        """
        # print(f"CommService: Attempting to write values: {values_to_write}") # Verbose
        write_tasks = []
        bindings_map = {b.id: b for b in self.write_bindings} # Quick lookup

        for binding_id, value in values_to_write.items():
            binding = bindings_map.get(binding_id)
            if not binding:
                print(f"CommService Warning: No write binding found for ID {binding_id}. Skipping.")
                continue
            if not binding.endpoint_url or not binding.address:
                print(f"CommService Warning: Write binding {binding_id} is missing endpoint_url or address. Skipping.")
                continue

            client = self.opcua_clients.get(binding.endpoint_url)
            if not client:
                print(f"CommService Warning: No active client found for endpoint {binding.endpoint_url} (Binding {binding_id}). Skipping write.")
                continue

            # Schedule the write operation as an async task
            write_tasks.append(self._write_single_value(client, binding.address, value, binding_id))

        if write_tasks:
            results = await asyncio.gather(*write_tasks, return_exceptions=True)
            for binding_id, result in zip(values_to_write.keys(), results): # Assuming order is preserved
                 if isinstance(result, Exception):
                     print(f"CommService Error: Failed to write value for binding {binding_id}: {result}")
                 # else: # Optional: Log success
                 #     print(f"CommService: Successfully wrote value for binding {binding_id}")
        # print("CommService: Finished writing values.") # Verbose

    async def _write_single_value(self, client: Client, node_address: str, value: Any, binding_id: int):
        """Helper to write a single value asynchronously."""
        try:
            node = client.get_node(node_address)
            # Determine data type if possible, otherwise let asyncua handle it
            # For robust implementation, check binding.data_type or node's data type
            variant_type = None # Example: ua.VariantType.Double if known
            data_value = ua.DataValue(ua.Variant(value, variant_type))
            # print(f"  Writing to Node {node_address} (Binding {binding_id}): {data_value}") # Verbose
            await node.write_value(data_value)
        except Exception as e:
            # Raise the exception to be caught by asyncio.gather
            raise Exception(f"Node {node_address} (Binding {binding_id}): {e}") from e

# --- Subscription Handler --- # Moved definition to the top

# Instantiate the service (consider dependency injection for FastAPI)
communication_service = CommunicationService()

# Removed SubHandler definition from here, moved to top

# Instantiate the service (consider dependency injection for FastAPI)
communication_service = CommunicationService()