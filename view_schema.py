"""
Simple script to view the database schema.
"""
import sqlite3

def view_table_schema(table_name):
    """View the schema of a specific table"""
    print(f"\n=== Table: {table_name} ===")
    
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    print(f"Columns ({len(columns)}):")
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, is_pk = col
        print(f"  {col_name} ({col_type}){' PRIMARY KEY' if is_pk else ''}{' NOT NULL' if not_null else ''}")
    
    conn.close()

def main():
    """View schemas for all tables"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        view_table_schema(table[0])
    
    conn.close()

if __name__ == "__main__":
    main() 