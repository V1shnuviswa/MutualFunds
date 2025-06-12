# /home/ubuntu/order_management_system/src/database.py

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

# Use the absolute path to the existing database
DATABASE_URL = "sqlite+aiosqlite:///C:/Users/Vishnu/Downloads/order_management_system_github/order_management_system_github/order_management.db"

# SQLAlchemy setup for ORM (synchronous for model definition)
engine = create_engine(
    DATABASE_URL.replace("+aiosqlite", ""), connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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

