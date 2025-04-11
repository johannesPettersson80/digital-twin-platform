# Digital Twin & Testing Platform

This project aims to build a web-based system for testing and simulating machines, inspired by OpenCommissioning but with a focus on ease of use.

## Current Status (as of 2025-04-11 ~3:54 PM)

*   **Architecture:** Defined in `ARCHITECTURE.md`. Uses a Python/FastAPI backend, a web frontend (TBD), and SQLite for the database.
*   **Phase 1 (Core Backend & Modeling):** Complete.
    *   FastAPI application structure is set up (`app/main.py`).
    *   Configuration uses Pydantic and `.env` files (`app/core/config.py`).
    *   Database connection uses SQLAlchemy with SQLite (`app/db/session.py`).
    *   Resources implemented (Model, Schema, CRUD, API Endpoint): `Project`, `MachineModel`, `Component`, `Connection`.
    *   Alembic is configured and all migrations are applied (`alembic upgrade head`).
*   **Phase 2 (Basic Simulation):** Mostly Complete.
    *   Simulation service created (`app/services/simulation_service.py`).
    *   Simulation API endpoints implemented (`/api/v1/simulations/start`, `/stop`, `/{id}/status`).
    *   Basic component logic implemented for 'Sensor', 'Heater', 'Actuator', 'Valve'.
    *   Refined connection handling: Added `source_port`/`target_port` to connections.
    *   **Simulation loop improved:** Now uses topological sort to handle execution dependencies (`app/services/simulation_service.py`).
*   **Phase 3 (Communication & HIL):** In Progress.
    *   Added `asyncua` dependency for OPC UA. **(DONE)**
    *   Implemented `CommunicationBinding` resource (Model, Schema, CRUD, API). **(DONE)**
    *   Added Alembic migration for `communication_bindings` table. **(DONE)**
    *   Created `CommunicationService` (`app/services/communication_service.py`). **(DONE)**
    *   Implemented core OPC UA connection, subscription, read/write logic in `CommunicationService`. **(DONE)**
    *   Integrated `CommunicationService` into `SimulationService` to enable HIL mode (`simulation_mode='hil'`). **(DONE)**

## Setup & Running Locally

1.  **Navigate to Project Root:**
    Open your terminal in this directory (`C:\2.Private\projects\digital_twin_platform`).

2.  **Create Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    # source venv/bin/activate # Linux/macOS
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt # Make sure to re-run if requirements changed
    ```

4.  **Apply Database Migrations:**
    This command creates the `digital_twin.db` file (if it doesn't exist) and applies all schema changes defined in the migration files.
    ```bash
    alembic upgrade head
    ```

5.  **Run Development Server:**
    This starts the FastAPI backend server.
    ```bash
    # Option 1: Using the run script (handles port check, uses port 7777 by default)
    python run.py

    # Option 2: Running uvicorn directly (e.g., on port 7778)
    # Note: --reload flag can sometimes cause issues with port cleanup on Windows.
    # uvicorn app.main:app --host 127.0.0.1 --port 7778 --reload
    uvicorn app.main:app --host 127.0.0.1 --port 7778
    ```
    The API should be accessible at the specified port (e.g., `http://127.0.0.1:7778`), and the interactive documentation (Swagger UI) at `<base_url>/docs`.

## Alembic Migrations

*   **Generate a new migration (after changing models):**
    ```bash
    alembic revision --autogenerate -m "Description of changes"
    ```
*   **Apply migrations:**
    ```bash
    alembic upgrade head
    ```
*   **Downgrade migrations:**
    ```bash
    alembic downgrade -1 # Downgrade one revision
    alembic downgrade base # Downgrade all
    ```

## Next Steps

*   Test and refine Phase 3 (HIL):
    *   Configure `CommunicationBinding`s for a test model.
    *   Run simulations in `hil` mode against a running OPC UA server.
    *   Debug and refine OPC UA connection, subscription, and read/write logic.
*   Implement logic for more component types (Phase 2 refinement).
*   Refer to `PROJECT_DOCS.md` and `ARCHITECTURE.md` for more details.