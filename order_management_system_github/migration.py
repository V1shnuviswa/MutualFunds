import os
import sys
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from sqlalchemy import create_engine
from src.database import Base

def create_postgres_db(postgres_url):
    """Create PostgreSQL database if it doesn't exist"""
    # Extract database name from URL
    db_name = postgres_url.split('/')[-1]
    # Create connection URL to postgres database (needed to create the target database)
    postgres_base_url = '/'.join(postgres_url.split('/')[:-1]) + '/postgres'
    
    # Connect to postgres database
    conn = psycopg2.connect(postgres_base_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"Database '{db_name}' created successfully")
    else:
        print(f"Database '{db_name}' already exists")
    
    cursor.close()
    conn.close()

def migrate_data(sqlite_path, postgres_url):
    """Migrate data from SQLite to PostgreSQL"""
    # Connect to SQLite database
    sqlite_conn = sqlite3.connect(sqlite_path)
    
    # Connect to PostgreSQL database
    postgres_engine = create_engine(postgres_url)
    
    # Get list of tables from SQLite
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", sqlite_conn)
    
    # Create tables in PostgreSQL
    print("Creating tables in PostgreSQL...")
    Base.metadata.create_all(postgres_engine)
    
    # Migrate data for each table
    for table_name in tables['name'].tolist():
        try:
            print(f"Migrating table: {table_name}")
            # Read data from SQLite
            df = pd.read_sql(f"SELECT * FROM {table_name}", sqlite_conn)
            
            if not df.empty:
                # Write data to PostgreSQL
                df.to_sql(table_name, postgres_engine, if_exists='append', index=False)
                print(f"  Migrated {len(df)} rows from '{table_name}'")
            else:
                print(f"  Table '{table_name}' is empty - no data to migrate")
        except Exception as e:
            print(f"  Error migrating table '{table_name}': {e}")
    
    # Close connections
    sqlite_conn.close()
    
    print("Migration completed successfully")

if __name__ == "__main__":
    # Set up paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    
    # SQLite database path (source)
    sqlite_path = os.getenv("SQLITE_PATH", "order_management.db")
    
    # PostgreSQL connection URL (target)
    postgres_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/order_management"
    )
    
    print(f"Starting migration from SQLite ({sqlite_path}) to PostgreSQL ({postgres_url})")
    
    try:
        # Create PostgreSQL database if needed
        create_postgres_db(postgres_url)
        
        # Migrate data
        migrate_data(sqlite_path, postgres_url)
        
        print("Migration completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"Error during migration: {e}", file=sys.stderr)
        sys.exit(1) 