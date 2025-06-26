# /home/ubuntu/order_management_system/src/database.py

import os
import time
import sqlite3
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

# Use the absolute path to the existing database

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'order_management.db'}")


# SQLAlchemy setup for ORM (synchronous for model definition)
engine = create_engine(
    DATABASE_URL.replace("+aiosqlite", ""), connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevents session from being expired
)
Base = declarative_base()
metadata = MetaData()

# Databases setup for async database access in FastAPI
database = Database(DATABASE_URL)

def get_db():
    db = SessionLocal()
    print(f"DEBUG: Session object created: {db}")
    try:
        yield db
    finally:
        print("DEBUG: Closing database session.")
        db.close()

# Helper function to execute database operations with retry logic for SQLite locks
def execute_with_retry(db_session, operation_func, max_retries=3, retry_delay=1):
    """
    Execute a database operation with retry logic for SQLite locks
    
    Args:
        db_session: SQLAlchemy session
        operation_func: Function that performs the database operation
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        
    Returns:
        Result of the operation function
    """
    for attempt in range(max_retries):
        try:
            result = operation_func(db_session)
            return result
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                print(f"Database locked, retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                raise
        except Exception as e:
            raise

async def connect_db():
    await database.connect()

async def disconnect_db():
    await database.disconnect()

# Function to create tables (should not be called if tables already exist)
def create_tables():
    # Import models here to ensure they are registered with Base
    from . import models # noqa
    print("WARNING: This will create new tables if they don't exist. Existing data will be preserved.")
    Base.metadata.create_all(bind=engine)

