# /home/ubuntu/order_management_system/src/database.py

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

DATABASE_URL = "sqlite+aiosqlite:///./order_management.db"

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
    try:
        yield db
    finally:
        db.close()

async def connect_db():
    await database.connect()

async def disconnect_db():
    await database.disconnect()

# Function to create tables (call this once at startup if needed)
def create_tables():
    # Import models here to ensure they are registered with Base
    from . import models # noqa
    Base.metadata.create_all(bind=engine)

