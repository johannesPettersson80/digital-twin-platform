# Digital Twin & Testing Platform

A web-based platform for creating digital twins of machines, enabling simulation, testing, and hardware-in-the-loop (HIL) validation. Inspired by OpenCommissioning, this project prioritizes ease of use and a modern technology stack.

**Target Audience:** Automation engineers, machine builders, simulation specialists, educators.

## Key Features

*   **Model Definition:** Define machine components, connections, and properties through a structured API.
*   **Simulation Engine:** Run discrete-time simulations based on defined models and component logic. Supports dependency-aware execution order via topological sort.
*   **Hardware-in-the-Loop (HIL):** Connect simulations to real-world hardware via OPC UA communication bindings.
*   **RESTful API:** Manage projects, models, components, connections, simulations, and communication bindings via a FastAPI backend.
*   **Database Persistence:** Uses SQLAlchemy and Alembic for robust data storage and schema migrations (SQLite backend).
*   **FMU Integration (Basic):** Supports loading and simulating Functional Mock-up Units (FMUs) via FMPy (requires testing and API/UI).
*   **(Planned) Web Frontend:** A user-friendly interface for interacting with the platform (details TBD).

## Technology Stack

*   **Backend:** Python, FastAPI, Uvicorn
*   **Database:** SQLAlchemy, Alembic, SQLite (initially)
*   **Communication:** Asyncua (for OPC UA)
*   **Modeling:** Pydantic
*   **FMU Handling:** FMPy

<!--
## Development Status (as of 2025-04-11)

*   **Architecture:** Defined in `ARCHITECTURE.md`. Uses a Python/FastAPI backend, a web frontend (TBD), and SQLite for the database.
*   **Core Backend & Modeling:** Complete (Projects, Models, Components, Connections API/DB).
*   **Basic Simulation:** Mostly Complete (Simulation service, API, basic component logic, topological sort).
*   **Communication & HIL (OPC UA):** Implementation complete, requires testing and refinement.
*   **FMU Integration:** Basic simulation service integration complete (loading, stepping, cleanup via FMPy). Requires API/UI for management and testing.

(Consider moving detailed status history to a CHANGELOG.md)
-->
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

<!--
## Next Steps / Roadmap

*   Test and refine HIL functionality with real OPC UA servers.
*   Implement logic for a wider variety of component types.
*   Develop the web frontend.
*   Add comprehensive unit and integration tests.
*   Explore alternative database backends (e.g., PostgreSQL).
*   Define clear contribution guidelines.
*   Choose and add a project license.

(Consider using GitHub Issues or Projects for detailed task tracking)
-->

## Contributing

Contributions are welcome! Please refer to the `CONTRIBUTING.md` file (to be created) for guidelines.

## License

This project is currently unlicensed. A license will be added soon.

## Further Documentation

Refer to `PROJECT_DOCS.md` and `ARCHITECTURE.md` for more in-depth technical details.