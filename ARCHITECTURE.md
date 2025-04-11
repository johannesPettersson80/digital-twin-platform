# Digital Twin & Testing Platform - Architecture Plan

This document outlines the proposed architecture for the web-based Digital Twin & Testing Platform.

## 1. High-Level Architecture

The system follows a service-oriented approach with a clear separation between the frontend UI and backend services.

```mermaid
graph TD
    subgraph User Interface
        Frontend[Web Application (React/Vue/Angular)]
    end

    subgraph Backend Services (Python/FastAPI)
        API[API Gateway (FastAPI)]
        SimService[Simulation Service]
        CommService[Communication Service]
        TestService[Test Automation Service]
        DB[(Database - SQLite)] # Changed from PostgreSQL
    end

    subgraph External Systems
        PLC[Physical/Virtual PLC]
        FMU[FMU Files]
        User[User]
    end

    User -- Interacts via Browser --> Frontend
    Frontend -- HTTP/WebSocket --> API

    API -- Routes requests --> SimService
    API -- Routes requests --> CommService
    API -- Routes requests --> TestService
    API -- Reads/Writes --> DB

    SimService -- Manages state, runs models --> DB
    SimService -- Loads --> FMU
    SimService -- Exchanges data --> CommService

    CommService -- Connects/Exchanges data --> PLC
    CommService -- Exchanges data --> SimService

    TestService -- Orchestrates tests --> SimService
    TestService -- Orchestrates tests --> CommService
    TestService -- Records results --> DB
```

## 2. Component Breakdown & Responsibilities

*   **Frontend (Web Application):**
    *   Provides the graphical user interface (GUI).
    *   Includes: Modeling canvas (drag-and-drop components, connections), properties editor, communication binding interface, test sequence editor, real-time dashboard.
    *   Communicates with the Backend API via HTTP requests (for configuration, commands) and WebSockets (for real-time data updates).
    *   *Technology:* TBD (React, Vue, or Angular recommended).
*   **Backend API Gateway (FastAPI):**
    *   The main entry point for the frontend.
    *   Handles user authentication and authorization (if implemented).
    *   Validates incoming requests (using Pydantic schemas).
    *   Routes requests to the appropriate backend service (Simulation, Communication, Test).
    *   Performs CRUD operations on the database for configuration data (Projects, Models, Components, Tests, etc.) via SQLAlchemy ORM.
    *   Serves data to the frontend.
    *   *Technology:* Python, FastAPI, SQLAlchemy, Pydantic.
*   **Simulation Service:**
    *   Manages the lifecycle of simulation sessions (start, stop, pause, step).
    *   Loads and executes built-in component models based on user configuration.
    *   Loads, initializes, and steps through FMUs using an FMI library (e.g., FMPy).
    *   Maintains the state of all components in a running simulation.
    *   Calculates the next state based on internal logic, inputs from connected components, and data from the Communication Service (in HIL mode).
    *   *Technology:* Python, FMPy.
*   **Communication Service:**
    *   Manages connections to external hardware/software (PLCs).
    *   Implements adapters for various industrial protocols (starting with OPC UA, potentially adding Modbus, etc.).
    *   Reads data from PLCs based on user-defined bindings and provides it to the Simulation Service.
    *   Writes data from the Simulation Service to PLCs based on bindings.
    *   Handles connection management and error handling for external communication.
    *   *Technology:* Python, `asyncua` (chosen over `python-opcua`), potentially `pymodbus` or similar.
*   **Test Automation Service:**
    *   Parses and executes automated test sequences defined by the user.
    *   Interacts with the Simulation Service (e.g., to set initial conditions, read simulated values).
    *   Interacts with the Communication Service (e.g., to trigger PLC actions, read PLC values).
    *   Evaluates assertions defined in the test steps.
    *   Logs test execution details and results to the Database.
    *   *Technology:* Python.
*   **Database (SQLite):** # Changed from PostgreSQL for simplicity during initial development
    *   Persists all configuration data: User projects, machine models (components, connections), FMU metadata, communication bindings, test case definitions.
    *   Stores test results and potentially simulation logs.
    *   *Technology:* SQLite (using SQLAlchemy and Alembic).

## 3. Data Flow Examples

*   **Creating a Model:** User (Frontend) -> Drags component -> Frontend sends API request (`POST /api/v1/models/{id}/components`) -> API Gateway validates -> API Gateway writes to DB -> API Gateway confirms to Frontend -> Frontend updates UI.
*   **Running HIL Simulation:**
    1.  User (Frontend) -> Clicks 'Run HIL' -> Frontend sends API request (`POST /api/v1/simulation/start_hil/{model_id}`) -> API Gateway routes to Simulation Service.
    2.  Simulation Service loads model from DB, initializes FMUs, tells Communication Service to connect to PLC based on bindings.
    3.  *Loop:*
        *   Comm Service reads input values from PLC -> Sends to Sim Service.
        *   Sim Service steps its internal models & FMUs using PLC inputs and internal state -> Calculates outputs.
        *   Sim Service sends output values to Comm Service.
        *   Comm Service writes output values to PLC.
        *   Sim Service/Comm Service push state updates via API Gateway (WebSockets) -> Frontend Dashboard updates.
*   **Running Automated Test:**
    1.  User (Frontend) -> Clicks 'Run Test' -> Frontend sends API request (`POST /api/v1/testing/run/{test_id}`) -> API Gateway routes to Test Service.
    2.  Test Service loads test case from DB.
    3.  Test Service instructs Sim/Comm Services to set up initial state (may involve starting HIL).
    4.  Test Service executes steps: sends commands (via Sim/Comm Services), waits, reads values (via Sim/Comm Services), evaluates assertions.
    5.  Test Service logs results to DB.
    6.  Test Service reports completion status via API -> Frontend updates UI.

## 4. Core Data Models (Conceptual)

*   **Project:** User's workspace.
*   **MachineModel:** Visual model configuration (components, connections).
*   **Component:** Instance of a building block (Heater, Sensor, FMU) with properties, inputs, outputs.
*   **Connection:** Link between component ports (specifies `source_component_id`, `target_component_id`, `source_port`, `target_port`).
*   **FMU:** Metadata about imported FMU files.
*   **CommunicationBinding:** Link between component property/port and external address (PLC tag).
*   **TestCase:** Definition of an automated test sequence (steps).
*   **TestResult:** Outcome of a test run.

## 5. Technology Summary

*   **Backend:** Python 3.x, FastAPI, SQLAlchemy, Pydantic, FMPy, asyncua (chosen).
*   **Database:** SQLite (using SQLAlchemy and Alembic). # Changed from PostgreSQL
*   **Frontend:** TBD (React/Vue/Angular recommended).

## 6. Phased Implementation Plan (Suggestion)

1.  **Phase 1: Core Backend & Modeling:** Setup FastAPI project, define DB models (SQLAlchemy) & API schemas (Pydantic), implement CRUD API endpoints for Projects, Models, Components, Connections. Basic simulation service structure. Minimal frontend to visualize/edit models. **(DONE)**
2.  **Phase 2: Basic Simulation:** Implement simple built-in component models (e.g., Heater, Sensor, Actuator, Valve) in the Simulation Service. Implement connection handling for data flow between components. Add API endpoints to run pure simulations (no PLC). Improve simulation loop (dependency handling). Basic dashboard view. **(Mostly DONE)**
3.  **Phase 3: Communication & HIL:** Implement Communication Service with OPC UA adapter (`asyncua`). Implement communication bindings (API & DB). Integrate Comm Service with Sim Service for HIL loop. Enhance dashboard for HIL. **(In Progress - Bindings infrastructure DONE, Core OPC UA logic implemented, HIL integration in SimService DONE. Needs testing & refinement)**
4.  **Phase 4: FMU Integration:** Integrate FMPy into Simulation Service. Add API/UI for uploading/managing FMUs and configuring FMU components in models.
5.  **Phase 5: Test Automation:** Develop Test Service, define test step format, implement test execution logic. Add API/UI for creating and running tests, viewing results.
6.  **Phase 6+:** Refinement, more components, other protocols, user management, deployment optimization.