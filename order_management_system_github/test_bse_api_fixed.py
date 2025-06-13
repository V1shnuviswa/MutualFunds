#!/usr/bin/env python
"""
BSE STAR MF API Testing Script

This script demonstrates how to test the BSE STAR MF integration through the FastAPI endpoints.
It includes examples for authentication, client registration, and order placement.

Usage:
    1. First run the API server: python run_api_server.py
    2. Then run this script: python test_bse_api_fixed.py
"""

import requests
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bse_api_calls.log'),
        logging.StreamHandler()
    ]
)

# Set up loggers
logger = logging.getLogger('bse_test')
requests_logger = logging.getLogger('urllib3')
requests_logger.setLevel(logging.DEBUG)

# API base URL
API_BASE_URL = "http://localhost:8000"

# Authentication credentials for BSE STAR MF Demo
USER_CREDENTIALS = {
    "username": "6385101",  # Demo BSE User ID
    "password": "Abc@1234"  # Demo BSE Password
}

# BSE demo credentials for API calls
BSE_CREDENTIALS = {
    "userId": "6385101",  # Demo BSE User ID
    "memberId": "63851",  # Demo BSE Member ID
    "passKey": "PassKey123"  # Demo BSE PassKey
}

# Sample client data - Update with actual test client data
CLIENT_DATA = {
    "clientCode": f"TEST{datetime.now().strftime('%y%m%d%H%M')}",  # Unique client code
    "clientName": "Test Client",
    "pan": "ABCDE1234F",
    "email": "test@example.com",
    "mobile": "9999999999",
    "dob": "01/01/1990",
    "gender": "M",
    "address1": "123 Test Street",
    "address2": "Test Area",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "bankName": "State Bank of India",
    "bankAccount": "12345678901",
    "ifscCode": "SBIN0001234",
    "holdingMode": "Single"
}

# Sample lumpsum order data with demo BSE credentials
LUMPSUM_ORDER_DATA = {
    "TransCode": "NEW",
    "TransNo": f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "OrderId": "",
    "UserID": USER_CREDENTIALS["username"],  # Using demo BSE User ID
    "MemberId": BSE_CREDENTIALS["memberId"],  # Using demo BSE Member ID
    "ClientCode": CLIENT_DATA["clientCode"],  # Using test client code
    "SchemeCd": "132LGDG",  # Demo scheme code for testing
    "BuySell": "P",
    "BuySellType": "FRESH",
    "DPTxn": "P",  # Physical mode
    "OrderVal": 5000.00,  # Minimum amount for demo
    "Qty": None,  # Required for redemption orders only
    "FolioNo": "",  # Leave empty for new folios
    "IPAdd": "127.0.0.1",  # Local machine IP
    "EUIN": "",  # No EUIN for demo
    "EUINDecl": "N",  # No EUIN declaration
    "SubBrCode": "",  # No sub-broker code
    "DPC": "N",  # DPC flag
    "KYCStatus": "Y",  # KYC status required
    "MinRedeem": "N",  # Not a minimum redemption
    "Remarks": "Demo lumpsum order",  # Updated remark
    "PassKey": BSE_CREDENTIALS["passKey"]  # Using demo BSE PassKey
}

# Sample SIP order data for demo environment
SIP_ORDER_DATA = {
    "transaction_code": "NEW",
    "unique_ref_no": f"SIP{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "user_id": USER_CREDENTIALS["username"],  # Using demo BSE User ID
    "member_id": BSE_CREDENTIALS["memberId"],  # Using demo BSE Member ID
    "client_code": CLIENT_DATA["clientCode"],  # Using test client code
    "scheme_code": "132LGDG",  # Demo scheme code for testing
    "transaction_type": "PURCHASE",
    "frequency_type": "MONTHLY",
    "frequency_allowed": 1,
    "installment_amount": 1000,  # Minimum amount for demo SIP
    "no_of_installments": 12,
    "start_date": (date.today().replace(day=1) + date.resolution * 32).replace(day=1).strftime("%Y-%m-%d"),  # First day of next month
    "first_order_today": False,
    "mandate_id": "BSE000000000001",  # Demo mandate ID
    "dp_txn_mode": "PHYSICAL",
    "folio_no": "",
    "remarks": "Demo SIP Order",
    "kyc_status": "Y",
    "euin": "",
    "euin_declaration": False,
    "sub_broker_arn": "",
    "ip_address": "127.0.0.1"
}

def authenticate() -> Optional[str]:
    """Authenticate with the API and get access token"""
    logger.info("=== Authenticating with BSE API ===")
    
    try:
        # Using form data for authentication as expected by OAuth2
        logger.debug(f"Sending auth request to {API_BASE_URL}/auth/login")
        logger.debug(f"Auth credentials: username={USER_CREDENTIALS['username']}")
        
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data=USER_CREDENTIALS,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        logger.debug(f"Auth response status: {response.status_code}")
        logger.debug(f"Auth response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            token_data = response.json()
            logger.info("Authentication successful!")
            logger.debug(f"Full token data: {token_data}")
            return token_data["access_token"]
        else:
            logger.error(f"Authentication failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        logger.exception("Authentication error")
        return None

def register_client(token: str) -> bool:
    """Register a client with BSE"""
    logger.info("=== Registering Client with BSE API ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Start registration process
        logger.debug(f"Starting client registration at {API_BASE_URL}/api/v1/registration/start")
        response = requests.post(
            f"{API_BASE_URL}/api/v1/registration/start",
            headers=headers
        )
        
        logger.debug(f"Registration start response: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Failed to start registration: {response.text}")
            return False
            
        reg_data = response.json()
        client_code = reg_data["client_code"]
        session_token = reg_data["session_token"]
        
        logger.info(f"Started registration for client: {client_code}")
        logger.debug(f"Session token: {session_token}")
        
        # Step 1: Personal details
        step1_data = {
            "client_name": CLIENT_DATA["clientName"],
            "email": CLIENT_DATA["email"],
            "mobile": CLIENT_DATA["mobile"],
            "investment_mode": CLIENT_DATA["holdingMode"]
        }
        
        logger.debug(f"Sending step 1 data: {json.dumps(step1_data, indent=2)}")
        response = requests.post(
            f"{API_BASE_URL}/api/v1/registration/step/1?client_code={client_code}",
            headers={**headers, "session_token": session_token},
            json=step1_data
        )
        
        logger.debug(f"Step 1 response: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Failed at step 1: {response.text}")
            return False
            
        logger.info("Step 1 completed successfully")
        
        # Complete registration
        logger.debug("Completing registration process")
        response = requests.post(
            f"{API_BASE_URL}/api/v1/registration/complete?client_code={client_code}",
            headers={**headers, "session_token": session_token}
        )
        
        if response.status_code == 200:
            client_data = response.json()
            logger.info(f"Client registration completed! Client code: {client_data['client_code']}")
            return True
        else:
            logger.error(f"Failed to complete registration: {response.text}")
            return False
            
    except Exception as e:
        logger.exception("Client registration error")
        return False

def place_lumpsum_order(token: str) -> bool:
    """Place a lumpsum order with BSE"""
    logger.info("=== Placing Lumpsum Order with BSE API ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Create order data for request
        order_data = LUMPSUM_ORDER_DATA.copy()
        logger.info(f"Placing lumpsum order for client: {order_data['ClientCode']}")
        logger.info(f"Scheme: {order_data['SchemeCd']}, Amount: {order_data['OrderVal']}")
        logger.debug(f"Full order data: {json.dumps(order_data, indent=2)}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/orders/lumpsum",
            headers=headers,
            json=order_data
        )
        
        logger.debug(f"Order response status: {response.status_code}")
        logger.debug(f"Order response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            order_data = response.json()
            logger.info("Lumpsum order placed successfully!")
            logger.info(f"Order ID: {order_data['order_id']}")
            logger.info(f"BSE Order ID: {order_data.get('bse_order_id', 'N/A')}")
            logger.debug(f"Full response: {json.dumps(order_data, indent=2)}")
            return True
        else:
            logger.error(f"Failed to place lumpsum order: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.exception("Lumpsum order error")
        return False

def place_sip_order(token: str) -> bool:
    """Place a SIP order with BSE"""
    print("\n=== Placing SIP Order with BSE API ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Use a hardcoded encrypted password for testing
        # In a real scenario, we would get this from BSE authentication
        encrypted_password = "vAcs+23BFK3j4BPrvf1j0vbIj6aTc6hGK33y7v7Ksts"
        
        # Update order data with encrypted password
        order_data = SIP_ORDER_DATA.copy()
        order_data["password"] = encrypted_password
        
        print(f"Placing SIP order for client: {order_data['client_code']}")
        print(f"Scheme: {order_data['scheme_code']}, Amount: {order_data['installment_amount']}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/orders/sip",
            headers=headers,
            json=order_data
        )
        
        if response.status_code == 200:
            order_data = response.json()
            print(f"✅ SIP order placed successfully!")
            print(f"SIP ID: {order_data['sip_id']}")
            print(f"BSE SIP Reg ID: {order_data.get('bse_sip_reg_id', 'N/A')}")
            print(f"Status: {order_data['status']}")
            print(f"BSE Remarks: {order_data.get('bse_remarks', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to place SIP order: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ SIP order error: {str(e)}")
        return False

def check_order_status(token: str, order_id: str) -> bool:
    """Check the status of an order"""
    print(f"\n=== Checking Order Status for {order_id} ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/orders/{order_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            order_data = response.json()
            print(f"✅ Order status retrieved successfully!")
            print(f"Order ID: {order_data['orderId']}")
            print(f"Status: {order_data['orderStatus']}")
            print(f"Client: {order_data['clientCode']}")
            print(f"Scheme: {order_data['schemeCode']}")
            print(f"Amount: {order_data.get('amount', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to get order status: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Order status check error: {str(e)}")
        return False

def main():
    """Main function to run the tests"""
    print("BSE STAR MF API Testing Script")
    print("==============================")
    
    # Authenticate
    token = authenticate()
    if not token:
        print("Cannot proceed without authentication")
        return
    
    # Ask user what to test
    print("\nWhat would you like to test?")
    print("1. Register a client")
    print("2. Place a lumpsum order")
    print("3. Place a SIP order")
    print("4. Check order status")
    print("5. Run all tests")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-5): ").strip()
    
    if choice == "1":
        register_client(token)
    elif choice == "2":
        place_lumpsum_order(token)
    elif choice == "3":
        place_sip_order(token)
    elif choice == "4":
        order_id = input("Enter order ID to check: ").strip()
        check_order_status(token, order_id)
    elif choice == "5":
        # Run all tests in sequence
        client_success = register_client(token)
        if client_success:
            lumpsum_success = place_lumpsum_order(token)
            sip_success = place_sip_order(token)
    else:
        print("Exiting...")

if __name__ == "__main__":
    main()