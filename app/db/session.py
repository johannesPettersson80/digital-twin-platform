from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Remove declarative_base import, as Base is now defined in app.db.base

from app.core.config import settings

# Check if the database URI indicates SQLite
is_sqlite = settings.DATABASE_URI and settings.DATABASE_URI.startswith("sqlite")

connect_args = {}
if is_sqlite:
    # SQLite specific argument needed for FastAPI/multi-threaded access
    connect_args = {"check_same_thread": False}

# Create the SQLAlchemy engine
engine = create_engine(
    str(settings.DATABASE_URI), # Ensure the URI is a string
    pool_pre_ping=True, # Good practice, though less critical for SQLite
    connect_args=connect_args
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is now defined in app.db.base and models are imported there.
# No need to define Base or import models here anymore.
# Dependency to get DB session (can be used in FastAPI endpoints)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()