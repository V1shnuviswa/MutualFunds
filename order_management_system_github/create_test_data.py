import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import User, Client, Scheme

def create_test_data():
    """
    Create test data in the database including:
    - Test client with code 0000100013 (the one registered with BSE)
    - Test scheme with code EDWRG
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
        
        # Create test client
        test_client = Client(
            client_code="0000100013",
            client_name="Vishnu Viswakumar",
            pan="AKUPV4977J",
            kyc_status="Y",
            account_type="Individual",
            holding_type="SI",
            tax_status="01",
            created_by_user_id=1  # Assuming user ID 1 exists
        )
        
        # Check if client already exists
        existing_client = db.query(Client).filter(Client.client_code == "0000100013").first()
        if existing_client:
            print(f"Client with code 0000100013 already exists")
        else:
            db.add(test_client)
            print(f"Added test client with code 0000100013")
        
        # Create test scheme
        test_scheme = Scheme(
            scheme_code="EDWRG",
            scheme_name="Test Equity Scheme Growth",
            amc_code="EDW",
            rta_code="CAM",
            isin="INF123456789",
            category="Equity",
            is_active=True
        )
        
        # Check if scheme already exists
        existing_scheme = db.query(Scheme).filter(Scheme.scheme_code == "EDWRG").first()
        if existing_scheme:
            print(f"Scheme with code EDWRG already exists")
        else:
            db.add(test_scheme)
            print(f"Added test scheme with code EDWRG")
        
        # Commit changes
        db.commit()
        print("Successfully created test data")
        return True
        
    except Exception as e:
        print(f"Error creating test data: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if create_test_data():
        print("Test data creation completed successfully")
    else:
        print("Test data creation failed")
        sys.exit(1) 