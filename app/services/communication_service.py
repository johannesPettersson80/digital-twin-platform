# app/services/communication_service.py

import asyncio
import logging # Import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict # Import defaultdict
from asyncua import Client, ua # Import asyncua

from app.schemas.communication_binding import CommunicationBinding # For type hinting

logger = logging.getLogger(__name__) # Setup logger
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
            logger.debug(f"OPC UA Sub Update: Node {node_id_str} (Binding {binding_id}), Value: {val}")
            self.comm_service.binding_values[binding_id] = val # Update the central store
        else:
            logger.warning(f"Received datachange for unmapped node: {node_id_str}, Value: {val}")

    def event_notification(self, event):
        logger.info(f"OPC UA Event Received: {event}")
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
        self.binding_values.clear() # Clear previous values
        self.node_id_to_binding_id_map.clear() # Clear previous mapping
        self.read_bindings = [b for b in bindings if b.direction == 'read']
        self.write_bindings = [b for b in bindings if b.direction == 'write']
        logger.info(f"Initializing connections for {len(self.read_bindings)} read and {len(self.write_bindings)} write bindings.")

        endpoints = {b.endpoint_url for b in bindings if b.endpoint_url}
        logger.info(f"Found unique endpoints: {endpoints}")

        if not endpoints:
            logger.warning("No endpoints found in bindings. Skipping connection initialization.")
            return

        for url in endpoints:
            # Check if client exists and is connected
            existing_client = self.opcua_clients.get(url)
            is_connected = False
            if existing_client:
                try:
                    # A simple check, might need more robust check depending on asyncua version
                    await existing_client.get_endpoints()
                    is_connected = True
                    logger.info(f"Already connected to {url}. Skipping connection attempt.")
                except Exception:
                    logger.warning(f"Client for {url} exists but seems disconnected. Attempting reconnect.")
                    # Clean up old client before reconnecting
                    try:
                        await existing_client.disconnect()
                    except Exception: pass
                    del self.opcua_clients[url]
                    if url in self.opcua_subscriptions: del self.opcua_subscriptions[url]
                    # Consider clearing related monitored items and node mappings too

            if is_connected:
                continue

            logger.info(f"Attempting to connect to OPC UA server: {url}")
            client = Client(url=url)
            try:
                await client.connect()
                self.opcua_clients[url] = client
                logger.info(f"Successfully connected to {url}")

                # Create subscription for this endpoint if there are read bindings for it
                endpoint_read_bindings = [b for b in self.read_bindings if b.endpoint_url == url]
                # Create subscription for this endpoint if there are read bindings for it
                endpoint_read_bindings = [b for b in self.read_bindings if b.endpoint_url == url]
                if endpoint_read_bindings:
                    logger.info(f"Creating subscription for {url} (Period: 500ms)")
                    try:
                        subscription = await client.create_subscription(500, self.sub_handler) # Period ms, handler object
                        self.opcua_subscriptions[url] = subscription
                        logger.info(f"Subscription created for {url}")
                    except Exception as sub_err:
                        logger.error(f"Failed to create subscription for {url}: {sub_err}")
                        # Should we disconnect if subscription fails? Depends on requirements.
                        # await client.disconnect()
                        # del self.opcua_clients[url]
                        continue # Skip monitoring for this endpoint if subscription failed

                    # Subscribe to nodes for read bindings
                    nodes_to_monitor = []
                    for binding in endpoint_read_bindings:
                        try:
                            node = client.get_node(binding.address)
                            nodes_to_monitor.append(node)
                            # Map node ID string back to our binding ID for the handler
                            node_id_str = node.nodeid.to_string()
                            self.node_id_to_binding_id_map[node_id_str] = binding.id # Map OPC UA node ID to our internal binding ID
                            logger.debug(f"Prepared node {binding.address} (NodeID: {node_id_str}, Binding: {binding.id}) for monitoring.")
                        except Exception as node_err:
                            logger.error(f"Failed to get node '{binding.address}' on {url} for binding {binding.id}: {node_err}")

                    if nodes_to_monitor:
                        logger.info(f"Subscribing to data changes for {len(nodes_to_monitor)} nodes on {url}...")
                        try:
                            handles = await subscription.subscribe_data_change(nodes_to_monitor)
                            # Store monitored item objects (optional, might be useful for unsubscribing later)
                            # Note: asyncua might return handles or MonitoredItem objects depending on version/context
                            # Assuming handles are sufficient for now, or that MonitoredItems are implicitly managed by subscription
                            logger.info(f"Successfully subscribed to data changes for nodes on {url}. Handles: {handles}")
                            # self.monitored_items[url].extend(handles) # Or store MonitoredItem objects if available/needed
                        except Exception as sub_data_err:
                            logger.error(f"Failed to subscribe to data changes for nodes on {url}: {sub_data_err}")

            except Exception as conn_err:
                logger.error(f"Failed to connect or complete subscription setup for {url}: {conn_err}")
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

        logger.info("Connection initialization process complete.")

    async def disconnect_all(self):
        """
        Disconnects all active OPC UA connections.
        """
        logger.info("Disconnecting all OPC UA clients...")
        # Disconnect clients gracefully
        disconnect_tasks = []
        urls = list(self.opcua_clients.keys()) # Get keys before clearing
        for url in urls:
            client = self.opcua_clients.get(url)
            if client:
                logger.info(f"Scheduling disconnect for {url}...")
                disconnect_tasks.append(client.disconnect())
            else:
                logger.warning(f"Client for {url} not found during disconnect initiation.")

        if disconnect_tasks:
            results = await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            for url, result in zip(urls, results): # Use the saved list of URLs
                if isinstance(result, Exception):
                    logger.error(f"Failed to disconnect from {url}: {result}")
                else:
                    logger.info(f"Successfully disconnected from {url}")

        # Clear internal state
        self.opcua_clients.clear()
        self.opcua_subscriptions.clear()
        self.monitored_items.clear()
        self.binding_values.clear()
        self.node_id_to_binding_id_map.clear()
        self.read_bindings.clear()
        self.write_bindings.clear()
        logger.info("All connections closed and internal state cleared.")

    async def read_values_from_external(self) -> Dict[int, Any]:
        """
        Reads the latest values for all 'read' bindings.
        For OPC UA, this might involve checking the latest values received via subscription.
        Returns a dictionary mapping {binding_id: value}.
        """
        # Values are updated asynchronously by the SubHandler.
        # This function returns the current state of the values dictionary received via subscriptions.
        current_values = self.binding_values.copy() # Return a copy
        logger.debug(f"Returning current binding values (from subscriptions): {current_values}")
        return current_values

    async def write_values_to_external(self, values_to_write: Dict[int, Any]):
        """
        Writes values to the external system based on 'write' bindings.
        Input: Dictionary mapping {binding_id: value_to_write}.
        """
        logger.debug(f"Attempting to write values: {values_to_write}")
        write_tasks = []
        bindings_map = {b.id: b for b in self.write_bindings} # Quick lookup

        for binding_id, value in values_to_write.items():
            binding = bindings_map.get(binding_id)
            if not binding:
                logger.warning(f"No write binding found for ID {binding_id}. Skipping write.")
                continue
            if not binding.endpoint_url or not binding.address:
                logger.warning(f"Write binding {binding_id} is missing endpoint_url or address. Skipping write.")
                continue

            client = self.opcua_clients.get(binding.endpoint_url)
            if not client:
                print(f"CommService Warning: No active client found for endpoint {binding.endpoint_url} (Binding {binding_id}). Skipping write.")
                continue

            # Schedule the write operation as an async task
            write_tasks.append(self._write_single_value(client, binding, value)) # Pass the whole binding

        if write_tasks:
            # Use a dictionary to map task back to binding_id for better error reporting
            task_to_binding_id = {task: binding_id for task, binding_id in zip(write_tasks, values_to_write.keys())}
            results = await asyncio.gather(*write_tasks, return_exceptions=True)

            # Process results, linking back to binding_id
            for i, result in enumerate(results):
                 task = write_tasks[i] # Get the original task
                 binding_id = task_to_binding_id.get(task) # Find the corresponding binding_id
                 if isinstance(result, Exception):
                     logger.error(f"Failed to write value for binding {binding_id}: {result}")
                 else: # Optional: Log success
                     logger.debug(f"Successfully wrote value for binding {binding_id}")
        logger.debug("Finished write values attempt.")

    async def _write_single_value(self, client: Client, binding: CommunicationBinding, value: Any):
        """Helper to write a single value asynchronously, using binding info."""
        node_address = binding.address
        binding_id = binding.id
        try:
            node = client.get_node(node_address)

            # Basic type inference (can be expanded)
            variant_type = None
            if isinstance(value, float):
                variant_type = ua.VariantType.Double
            elif isinstance(value, int):
                variant_type = ua.VariantType.Int64 # Or Int32, depending on server
            elif isinstance(value, bool):
                variant_type = ua.VariantType.Boolean
            elif isinstance(value, str):
                 variant_type = ua.VariantType.String
            # Add more types as needed (e.g., based on binding.data_type if available)

            data_value = ua.DataValue(ua.Variant(value, variant_type))
            logger.debug(f"Writing to Node {node_address} (Binding {binding_id}): Value={value}, Type={variant_type}, DV={data_value}")
            await node.write_value(data_value)
        except Exception as e:
            # Raise the exception to be caught by asyncio.gather, including binding info
            raise Exception(f"Node {node_address} (Binding {binding_id}): {e}") from e

# --- Subscription Handler --- # Moved definition to the top

# Instantiate the service (consider dependency injection for FastAPI)
communication_service = CommunicationService()

# Removed SubHandler definition from here, moved to top