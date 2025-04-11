import os
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator, model_validator, AnyUrl
from typing import List, Union, Dict, Any

# Load environment variables from .env file if it exists
from dotenv import load_dotenv
load_dotenv() # Looks for .env in current working dir or parent dirs

# Define project base directory relative to this file's location
# config.py -> app -> digital_twin_platform -> project_root
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Digital Twin & Testing Platform"

    # Backend CORS origins
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:8080", "http://127.0.0.1:8080",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str) and v.startswith("[") and v.endswith("]"):
             return [i.strip().strip("'\"") for i in v[1:-1].split(",") if i.strip().strip("'\"")]
        elif v is None or v == "":
             default_value = cls.model_fields['BACKEND_CORS_ORIGINS'].default
             return default_value if default_value else []
        raise ValueError(f"Invalid CORS origins format: {v}")

    # --- SQLite Database Configuration ---
    # Define the path for the SQLite database file relative to the project root
    SQLITE_DB_FILE: str = os.getenv("SQLITE_DB_FILE", "digital_twin.db")
    DATABASE_URI: str | None = None # Will be assembled below

    @model_validator(mode='before')
    @classmethod
    def assemble_db_connection(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("DATABASE_URI") is not None:
            # If DATABASE_URI is explicitly provided (e.g., in .env), use it
            return values

        # Assemble SQLite URI
        db_filename = values.get("SQLITE_DB_FILE", cls.model_fields['SQLITE_DB_FILE'].default)
        # Ensure the path is absolute, placing the db in the project root
        db_path = os.path.join(PROJECT_ROOT_DIR, db_filename)
        values["DATABASE_URI"] = f"sqlite+pysqlite:///{db_path}" # Use pysqlite driver
        # Note: For Windows paths, ensure correct handling if needed, but usually works.
        # For async: "sqlite+aiosqlite:///{db_path}"

        return values

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

# Print the calculated DB URI for verification during startup (optional)
print(f"Using Database URI: {settings.DATABASE_URI}")