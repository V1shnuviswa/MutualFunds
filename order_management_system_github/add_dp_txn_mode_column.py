#!/usr/bin/env python3
"""
Script to add the missing dp_txn_mode column to the orders table.
This fixes the SQLite error when creating lumpsum orders.
"""

import sqlite3
import os

# Database path
DB_PATH = "order_management_system_github/order_management.db"

def add_dp_txn_mode_column():
    """Add dp_txn_mode column to orders table if it doesn't exist."""
    
    if not os.path.exists(DB_PATH):
        print(f"Database file not found: {DB_PATH}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'dp_txn_mode' in columns:
            print("Column 'dp_txn_mode' already exists in orders table.")
            return True
        
        # Add the column
        print("Adding 'dp_txn_mode' column to orders table...")
        cursor.execute("ALTER TABLE orders ADD COLUMN dp_txn_mode VARCHAR(10)")
        
        # Commit the changes
        conn.commit()
        print("Successfully added 'dp_txn_mode' column to orders table.")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'dp_txn_mode' in columns:
            print("Verification successful: 'dp_txn_mode' column exists.")
            return True
        else:
            print("Verification failed: 'dp_txn_mode' column not found.")
            return False
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Adding missing dp_txn_mode column to orders table...")
    success = add_dp_txn_mode_column()
    
    if success:
        print("\nMigration completed successfully!")
        print("You can now test the lumpsum order endpoint.")
    else:
        print("\nMigration failed!")
        print("Please check the error messages above.")
