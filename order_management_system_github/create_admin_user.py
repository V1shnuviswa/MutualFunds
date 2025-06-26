import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import User
from src.security import get_password_hash

def create_admin_user():
    """
    Create an admin user in the database
    """
    # Get database URL from environment variable or use default PostgreSQL database
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/order_management"
    )
    
    print(f"Connecting to database at: {database_url}")
    
    try:
        # Create engine and session
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.user_id == "6385101").first()
        if existing_user:
            print(f"User with ID 6385101 already exists")
            return True
            
        # Create new user
        hashed_password = get_password_hash("Abc@1234")
        new_user = User(
            user_id="6385101",
            member_id="63851",
            password_hash=hashed_password,
            pass_key="PassKey123"
        )
        
        # Add to database
        db.add(new_user)
        db.commit()
        
        print(f"Successfully created admin user with ID: 6385101")
        return True
        
    except Exception as e:
        print(f"Error creating admin user: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if create_admin_user():
        print("Admin user creation completed successfully")
    else:
        print("Admin user creation failed")
        sys.exit(1) 