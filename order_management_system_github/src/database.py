# /home/ubuntu/order_management_system/src/database.py

import os
import time
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
from sqlalchemy.engine.url import make_url

# Database connection configuration
# PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is not set in the environment!")


# SQLAlchemy setup for ORM (synchronous for model definition)
url = make_url(DATABASE_URL)

connect_args = {}
if 'localhost' not in url.host and '127.0.0.1' not in url.host:
    connect_args = {"sslmode": "require"}

# SQLAlchemy setup for ORM (synchronous for model definition)
engine = create_engine(DATABASE_URL, connect_args=connect_args)  # 👈 updated this line
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
) # Prevents session from being expired

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

