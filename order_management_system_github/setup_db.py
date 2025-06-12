import os
import sys
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from src.database import Base
from src.models import (
    User, Client, Scheme, Order, SIPRegistration, 
    Mandate, OrderStatusHistory
)

def setup_database():
    """
    Set up the database and create all tables.
    """
    # Get database URL from environment variable or use default SQLite database
    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///./order_management.db"  # This is correct as setup_db.py is now in the root directory
    )

    print(f"Setting up database at: {database_url}")

    try:
        # Create engine
        engine = create_engine(database_url)

        # Create database if it doesn't exist
        if not database_exists(engine.url):
            create_database(engine.url)
            print("Created new database")
        else:
            print("Database already exists")

        # Create all tables
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("Successfully created all tables")

        return True

    except Exception as e:
        print(f"Error setting up database: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    # Add current directory to Python path since we're in the root
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    if setup_database():
        print("Database setup completed successfully")
        sys.exit(0)
    else:
        print("Database setup failed", file=sys.stderr)
        sys.exit(1) 