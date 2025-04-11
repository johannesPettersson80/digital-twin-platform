# Digital Twin & Testing Platform - Project Documentation

**Last Updated:** 2025-04-11 ~10:18 PM (Added basic FMU integration to SimulationService)

This document provides a comprehensive overview of the Digital Twin & Testing Platform project, intended to facilitate understanding and future development.

## 1. Project Overview

*   **Goal:** To build a web-based system for testing and simulating machines, inspired by OpenCommissioning but with a focus on ease of use.
*   **Core Technologies:**
    *   **Backend:** Python 3.x, FastAPI
    *   **Database:** SQLite (via SQLAlchemy and Alembic for migrations)
    *   **Configuration:** Pydantic Settings, `.env` files
    *   **FMU Handling:** FMPy (for Phase 4)
    *   **Frontend:** TBD (React/Vue/Angular proposed)
*   **Current Status (as of 2025-04-11 ~3:54 PM):**
    *   Phase 1 (Core Backend & Modeling) is complete.
    *   Basic FastAPI application structure is established.
    *   Database connection (SQLite) and configuration are set up.
    *   Resources implemented (Model, Schema, CRUD, API Endpoint):
        *   `Project`
        *   `MachineModel`
        *   `Component`
        *   `Connection`
    *   Alembic is configured and initial migrations are applied.
    *   Phase 2 (Basic Simulation) is mostly complete:
        *   Simulation service (`app/services/simulation_service.py`) created.
        *   Simulation API endpoints (`/start`, `/stop`, `/status`) implemented.
        *   Component loading from DB implemented.
        *   Basic logic for 'Sensor', 'Heater', 'Actuator', 'Valve' components implemented.
        *   Connection handling refined (source/target ports).
        *   **Simulation loop improved:** Uses topological sort for dependency handling.
    *   Phase 3 (Communication & HIL) is in progress:
        *   Added `asyncua` dependency to `requirements.txt`. **(DONE)**
        *   Implemented `CommunicationBinding` resource (Model, Schema, CRUD, API Endpoint). **(DONE)**
        *   Generated and applied Alembic migration for `communication_bindings` table. **(DONE)**
        *   Created `CommunicationService` (`app/services/communication_service.py`). **(DONE)**
        *   Implemented core OPC UA connection, subscription, read/write logic in `CommunicationService`. **(DONE)**
        *   Integrated `CommunicationService` into `SimulationService` to enable HIL mode (`simulation_mode='hil'`). **(DONE)**
    *   Phase 4 (FMU Integration) is in progress:
        *   Added `fmpy` dependency to `requirements.txt`. **(DONE)**
        *   Integrated basic FMU loading, stepping, and cleanup into `SimulationService`. **(DONE)**
## 2. Setup & Running Locally

Follow these steps to set up the development environment and run the application:

1.  **Navigate to Project Root:**
    Open a terminal in the project directory: `C:\2.Private\projects\digital_twin_platform`

2.  **Create & Activate Virtual Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    # source venv/bin/activate # Linux/macOS
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt # Re-run if requirements changed (e.g., asyncua added)
    ```

4.  **Apply Database Migrations:**
    This command creates the `digital_twin.db` file (if it doesn't exist) in the project root and applies the schema changes defined in the migration files.
    ```bash
    alembic upgrade head
    ```
    *Note: Migrations should be kept up-to-date. Run this command if new migration scripts are added.*

5.  **Run Development Server:**
    This starts the FastAPI backend server using Uvicorn.
    ```bash
    # Run from the project root directory
    uvicorn app.main:app --reload --app-dir C:\2.Private\projects\digital_twin_platform
    ```
    *   The API will be accessible at `http://127.0.0.1:8000`.
    *   Interactive API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.
    *   Alternative documentation (ReDoc) is available at `http://127.0.0.1:8000/redoc`.

## 3. Architecture

The system is designed with a separation between the frontend UI and backend services.

### 3.1. High-Level Components (Current Implementation Focus)

*   **Frontend (Web Application):** (Not yet implemented) Intended to provide the GUI for modeling, configuration, testing, and monitoring.
*   **Backend API Gateway (FastAPI):**
    *   The main entry point (`app/main.py`).
    *   Handles HTTP requests, validation (Pydantic), routing, and database interactions (SQLAlchemy).
    *   Serves API endpoints under `/api/v1/`.
    *   Manages database connections (`app/db/session.py`).
    *   Handles configuration (`app/core/config.py`).
*   **Database (SQLite):**
    *   Stores persistent data (Projects, Models, Components, Connections, CommunicationBindings).
    *   Managed by SQLAlchemy (`app/models/`) and Alembic (`migrations/`).
    *   The database file (`digital_twin.db`) is located in the project root.

### 3.2. Planned Future Components (Based on ARCHITECTURE.md)

*   **Simulation Service:** Manages simulation lifecycles, executes component models. (Partially implemented)
*   **Communication Service:** Handles connections and data exchange with external systems like PLCs (e.g., via OPC UA). (Core OPC UA logic implemented)
*   **Test Automation Service:** To execute automated test sequences against the simulated or physical system. (Not started)

*(Further details on the planned architecture can be found in `ARCHITECTURE.md`)*

---
*(Documentation continues in the next sections...)*

## 4. Project Structure

```
digital_twin_platform/
├── alembic.ini             # Alembic configuration file
├── ARCHITECTURE.md         # Detailed architecture plan (updated for SQLite, asyncua)
├── digital_twin.db         # SQLite database file (created after running migrations)
├── PROJECT_DOCS.md         # This documentation file
├── README.md               # Quick start guide and current status
├── requirements.txt        # Python package dependencies (includes asyncua)
├── app/                    # Main application source code directory
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point, creates app instance, includes routers
│   ├── api/                # API related modules
│   │   ├── __init__.py
│   │   └── api_v1/         # Version 1 of the API
│   │       ├── __init__.py
│   │       ├── api.py      # Aggregates all v1 API routers
│   │       └── endpoints/  # Specific API endpoint implementations (routers)
│   │           ├── __init__.py
│   │           ├── projects.py       # API endpoints for Project resource
│   │           ├── machine_models.py # API endpoints for MachineModel resource
│   │           ├── components.py     # API endpoints for Component resource
│   │           ├── connections.py    # API endpoints for Connection resource
│   │           ├── simulation.py     # API endpoints for Simulation control (Phase 2)
│   │           └── communication_bindings.py # API endpoints for CommunicationBinding resource (Phase 3)
│   ├── core/               # Core application settings and configuration
│   │   ├── __init__.py
│   │   └── config.py       # Pydantic settings management (loads .env)
│   ├── crud/               # CRUD (Create, Read, Update, Delete) database operations
│   │   ├── __init__.py
│   │   ├── base.py         # Base class for CRUD operations (optional, for common methods)
│   │   ├── crud_project.py       # CRUD functions for Project model
│   │   ├── crud_machine_model.py # CRUD functions for MachineModel model
│   │   ├── crud_component.py     # CRUD functions for Component model
│   │   ├── crud_connection.py    # CRUD functions for Connection model
│   │   └── crud_communication_binding.py # CRUD functions for CommunicationBinding model (Phase 3)
│   ├── db/                 # Database connection and session management
│   │   ├── __init__.py
│   │   └── session.py      # SQLAlchemy engine and session setup
│   ├── models/             # SQLAlchemy database models (table definitions)
│   │   ├── __init__.py
│   │   ├── project.py          # SQLAlchemy model for 'projects' table
│   │   ├── machine_model.py    # SQLAlchemy model for 'machine_models' table
│   │   ├── component.py        # SQLAlchemy model for 'components' table
│   │   ├── connection.py       # SQLAlchemy model for 'connections' table
│   │   └── communication_binding.py # SQLAlchemy model for 'communication_bindings' table (Phase 3)
│   ├── schemas/            # Pydantic schemas for data validation and serialization (API request/response shapes)
│   │   ├── __init__.py
│   │   ├── project.py          # Pydantic schemas for Project resource
│   │   ├── machine_model.py    # Pydantic schemas for MachineModel resource
│   │   ├── component.py        # Pydantic schemas for Component resource
│   │   ├── connection.py       # Pydantic schemas for Connection resource
│   │   ├── simulation.py       # Pydantic schemas for Simulation resource (Phase 2)
│   │   └── communication_binding.py # Pydantic schemas for CommunicationBinding resource (Phase 3)
│   └── services/           # Business logic and coordination services
│       ├── __init__.py
│       ├── simulation_service.py # Manages simulation execution (Phase 2)
│       └── communication_service.py # Manages external communication (Phase 3)
└── migrations/             # Alembic database migration scripts
    ├── __init__.py
    ├── env.py              # Alembic environment setup (connects to DB, defines migration context)
    ├── script.py.mako      # Template for generating new migration scripts
    └── versions/           # Individual migration files generated by Alembic
        ├── __init__.py
        ├── ..._initial.py # Initial migration script (projects table) - Check actual filename
        ├── ..._models_connections.py # Migration script for machine_models, components, connections tables - Check actual filename
        └── 9258b9590c2d_...py # Migration script for communication_bindings table (Phase 3)
```

## 5. Core Backend Components (Current Implementation)

*   **FastAPI Application (`app/main.py`):**
    *   Initializes the `FastAPI` instance.
    *   Includes the main API router (`app.api.api_v1.api.api_router`).
    *   Configures CORS middleware based on `settings.BACKEND_CORS_ORIGINS`.
*   **Configuration (`app/core/config.py`):**
    *   Uses `pydantic-settings` to load configuration from environment variables and `.env` files.
    *   Defines settings like API prefix, CORS origins, and database connection details.
    *   Dynamically assembles the `DATABASE_URI` for SQLite, placing the DB file in the project root.
*   **Database Session (`app/db/session.py`):**
    *   Creates the SQLAlchemy engine using the `DATABASE_URI` from settings.
    *   Creates a `SessionLocal` factory for generating database sessions.
    *   Provides a dependency (`get_db`) for use in API endpoints to manage session lifecycle per request.
*   **SQLAlchemy Models (`app/models/`):**
    *   Define the database table structures as Python classes.
    *   Includes `Project`, `MachineModel`, `Component`, `Connection`, `CommunicationBinding`.
*   **Pydantic Schemas (`app/schemas/`):**
    *   Define the expected data shapes for API requests and responses.
    *   Ensure data validation and provide clear API contracts.
    *   Includes schemas for `Project`, `MachineModel`, `Component`, `Connection`, `CommunicationBinding`.
    *   Includes schemas for `Simulation` (Phase 2).
*   **CRUD Operations (`app/crud/`):**
    *   Contain functions that interact directly with the database via SQLAlchemy sessions.
    *   Abstract the database logic away from the API endpoints.
    *   Includes CRUD functions for `Project`, `MachineModel`, `Component`, `Connection`, `CommunicationBinding`.
*   **API Endpoints (`app/api/api_v1/endpoints/`):**
    *   Define the actual HTTP routes (e.g., `/projects/`, `/projects/{project_id}`).
    *   Use FastAPI decorators (`@router.get`, `@router.post`, etc.).
    *   Inject dependencies like the database session (`Depends(get_db)`).
    *   Call CRUD functions to interact with the database.
    *   Use Pydantic schemas for request body validation and response serialization.
    *   Implements standard CRUD endpoints for `Project`, `MachineModel`, `Component`, `Connection`, `CommunicationBinding` resources.
    *   Includes endpoints for `Simulation` control (Phase 2).
*   **API Router (`app/api/api_v1/api.py`):**
    *   Aggregates individual endpoint routers (`projects`, `machine_models`, `components`, `connections`, `simulation`, `communication_bindings`) into a single main router for version 1 of the API.
*   **Services (`app/services/`):**
    *   `simulation_service.py`: Contains logic for managing and running simulations, including component execution order.
    *   `communication_service.py`: Contains logic for managing external communication (OPC UA connection, subscription, read/write implemented).

## 6. Database Migrations (Alembic)

*   **Purpose:** Manages changes to the database schema over time in a structured way.
*   **Configuration:** `alembic.ini` (points to migration scripts, database URL). `migrations/env.py` (configures how Alembic connects to the DB and finds models).
*   **Usage:**
    *   `alembic revision --autogenerate -m "Description"`: Detects changes in SQLAlchemy models (`app/models/`) and generates a new migration script in `migrations/versions/`.
    *   `alembic upgrade head`: Applies all pending migrations to the database.
    *   `alembic downgrade -1`: Reverts the last applied migration.
*   **Current State:**
    *   Three migration files exist (check `migrations/versions` for exact filenames):
        *   Initial migration (`projects` table).
        *   Second migration (`machine_models`, `components`, `connections` tables).
        *   Third migration (`communication_bindings` table - `9258b9590c2d`).
    *   All migrations up to `9258b9590c2d` (or latest) have been applied. The database schema is up-to-date.

## 7. Development Roadmap & Next Steps

Based on `README.md` and `ARCHITECTURE.md`:

1.  ~~**Apply Initial Migration:** Run `alembic upgrade head` to create the database schema.~~ **(DONE)**
2.  ~~**Implement Phase 1 Resources:**~~ **(DONE)**
    *   ~~Define SQLAlchemy models (`app/models/`) for `MachineModel`, `Component`, `Connection`.~~
    *   ~~Define corresponding Pydantic schemas (`app/schemas/`).~~
    *   ~~Implement CRUD functions (`app/crud/`) for these models.~~
    *   ~~Create API endpoints (`app/api/api_v1/endpoints/`) for these resources.~~
    *   ~~Generate and apply a new Alembic migration for these tables.~~
3.  **Phase 2: Basic Simulation:** Implement simple built-in component logic and simulation control. **(Mostly DONE)**
    *   Simulation service structure created (`app/services/simulation_service.py`). **(DONE)**
    *   API endpoints (`/start`, `/stop`, `/status`) implemented. **(DONE)**
    *   Component loading from DB implemented. **(DONE)**
    *   Basic logic for 'Sensor', 'Heater', 'Actuator', 'Valve' components implemented. **(DONE)**
    *   Connection handling refined (source/target ports). **(DONE)**
    *   **Simulation loop improved:** Uses topological sort for dependency handling. **(DONE)**
    *   *Next steps for Phase 2:* Implement logic for more component types (ongoing refinement).
4.  **Phase 3: Communication & HIL:** Implement OPC UA communication, bindings, and HIL loop. **(In Progress)**
    *   Added `asyncua` dependency. **(DONE)**
    *   Implemented `CommunicationBinding` resource (Model, Schema, CRUD, API). **(DONE)**
    *   Applied Alembic migration for `communication_bindings`. **(DONE)**
    *   Created `CommunicationService` structure (`app/services/communication_service.py`). **(DONE)**
    *   Implemented core OPC UA connection, subscription, read/write logic in `CommunicationService`. **(DONE)**
    *   Integrated `CommunicationService` into `SimulationService` for HIL mode. **(DONE)**
    *   *Next steps for Phase 3:* Test and refine HIL simulation with actual bindings and a running OPC UA server. Debug communication logic.
5.  **Phase 4: FMU Integration:** Add support for importing and simulating FMUs. **(In Progress)**
    *   Added `fmpy` dependency. **(DONE)**
    *   Integrated basic FMU loading, instantiation, `doStep`, and cleanup logic into `SimulationService`. **(DONE)**
    *   *Next steps for Phase 4:* Implement API/UI for managing FMU files, refine variable mapping/type handling, add testing (unit tests or with actual FMUs).
6.  **Phase 5: Test Automation:** Develop the test execution service and UI.
7.  **Frontend Development:** Design and implement the user interface (Technology TBD).

This documentation provides a snapshot of the project as of 2025-04-11 ~3:54 PM. Refer to the source code, `README.md`, and `ARCHITECTURE.md` for the most current details.