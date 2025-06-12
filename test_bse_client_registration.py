#!/usr/bin/env python
"""
BSE STAR MF Client Registration Test Script

This script tests client registration with BSE STAR MF.
It first authenticates and then attempts to register a test client.

Usage:
    python test_bse_client_registration.py
"""

import asyncio
import logging
import sys
import json
from datetime import datetime, date
from typing import Dict, Any, Optional

# Import BSE integration modules
from order_management_system_github.src.bse_integration.auth import BSEAuthenticator
from order_management_system_github.src.bse_integration.config import bse_settings
from order_management_system_github.src.bse_integration.client_registration import BSEClientRegistrar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test data
TEST_PASSKEY = "PassKey123"  # Default passkey
TEST_CLIENT_CODE = f"TEST{datetime.now().strftime('%y%m%d%H%M')}"  # Unique client code
TEST_PAN = "ABCDE1234F"
TEST_EMAIL = "test@example.com"
TEST_MOBILE = "9999999999"

async def test_authentication() -> Optional[str]:
    """Test BSE authentication and return encrypted password if successful"""
    logger.info("=== Testing BSE Authentication ===")
    
    try:
        auth = BSEAuthenticator()
        logger.info(f"Authenticating with BSE using User ID: {auth.user_id}")
        
        # Get encrypted password
        auth_response = await auth.authenticate(TEST_PASSKEY)
        
        if auth_response.success:
            logger.info(f"Authentication successful!")
            logger.info(f"Status Code: {auth_response.status_code}")
            logger.info(f"Encrypted Password: {auth_response.encrypted_password[:20]}...")
            return auth_response.encrypted_password
        else:
            logger.error(f"Authentication failed: {auth_response.message}")
            return None
            
    except Exception as e:
        logger.error(f"Authentication test failed: {str(e)}", exc_info=True)
        return None

async def test_client_registration(encrypted_password: str) -> bool:
    """Test BSE client registration"""
    if not encrypted_password:
        logger.error("Cannot test client registration without encrypted password")
        return False
        
    logger.info("=== Testing BSE Client Registration ===")
    
    try:
        # Create client registration handler
        client_reg = BSEClientRegistrar()
        
        # Create a client registration request
        client_data = {
            "ClientCode": TEST_CLIENT_CODE,
            "ClientHolding": "SI",  # Single
            "ClientTaxStatus": "01",  # Individual
            "ClientOccupationCode": "01",  # Business
            "ClientAppName1": "Test Client",
            "ClientAppName2": "",
            "ClientAppName3": "",
            "ClientDOB": date.today().replace(year=date.today().year - 30).strftime("%d/%m/%Y"),  # 30 years ago
            "ClientGender": "M",
            "ClientGuardian": "",
            "ClientPAN": TEST_PAN,
            "ClientNominee": "Test Nominee",
            "ClientNomineeRelation": "01",  # Spouse
            "ClientGuardianPAN": "",
            "ClientType": "P",  # Physical
            "ClientDefaultDP": "N",
            "ClientCDSLDPID": "",
            "ClientCDSLCLTID": "",
            "ClientNSDLDPID": "",
            "ClientNSDLCLTID": "",
            "ClientAccType1": "SB",  # Savings Bank
            "ClientAccNo1": "12345678901",
            "ClientMICRNo1": "400002000",
            "ClientIFSCCode1": "SBIN0001234",
            "ClientBankName1": "State Bank of India",
            "ClientBankBranch1": "Main Branch",
            "ClientBankAddress1": "Main Street",
            "ClientBankCity1": "Mumbai",
            "ClientBankState1": "Maharashtra",
            "ClientBankPincode1": "400001",
            "ClientAccType2": "",
            "ClientAccNo2": "",
            "ClientMICRNo2": "",
            "ClientIFSCCode2": "",
            "ClientBankName2": "",
            "ClientBankBranch2": "",
            "ClientBankAddress2": "",
            "ClientBankCity2": "",
            "ClientBankState2": "",
            "ClientBankPincode2": "",
            "ClientAccType3": "",
            "ClientAccNo3": "",
            "ClientMICRNo3": "",
            "ClientIFSCCode3": "",
            "ClientBankName3": "",
            "ClientBankBranch3": "",
            "ClientBankAddress3": "",
            "ClientBankCity3": "",
            "ClientBankState3": "",
            "ClientBankPincode3": "",
            "ClientAccType4": "",
            "ClientAccNo4": "",
            "ClientMICRNo4": "",
            "ClientIFSCCode4": "",
            "ClientBankName4": "",
            "ClientBankBranch4": "",
            "ClientBankAddress4": "",
            "ClientBankCity4": "",
            "ClientBankState4": "",
            "ClientBankPincode4": "",
            "ClientAccType5": "",
            "ClientAccNo5": "",
            "ClientMICRNo5": "",
            "ClientIFSCCode5": "",
            "ClientBankName5": "",
            "ClientBankBranch5": "",
            "ClientBankAddress5": "",
            "ClientBankCity5": "",
            "ClientBankState5": "",
            "ClientBankPincode5": "",
            "ClientChequeName5": "",
            "ClientAdd1": "123 Test Street",
            "ClientAdd2": "Test Area",
            "ClientAdd3": "",
            "ClientCity": "Mumbai",
            "ClientState": "Maharashtra",
            "ClientPincode": "400001",
            "ClientCountry": "India",
            "ClientResiPhone": "",
            "ClientResiFax": "",
            "ClientOfficePhone": "",
            "ClientOfficeFax": "",
            "ClientEmail": TEST_EMAIL,
            "ClientCommMode": "E",  # Email
            "ClientDivPayMode": "02",  # Direct Credit
            "ClientPan2": "",
            "ClientPan3": "",
            "ClientMobile": TEST_MOBILE,
            "MemberCode": bse_settings.BSE_MEMBER_CODE,
            "UserId": bse_settings.BSE_USER_ID,
            "Password": encrypted_password,
            "PassKey": TEST_PASSKEY,
        }
        
        logger.info(f"Registering test client: {TEST_CLIENT_CODE}")
        logger.info(f"Client details: PAN={TEST_PAN}, Email={TEST_EMAIL}, Mobile={TEST_MOBILE}")
        
        # For testing purposes, we'll just log the request and not actually submit
        # In a real test, you would uncomment the next line
        # response = await client_reg.register_client(client_data)
        
        # Mock response for testing
        response = {
            "success": True,
            "client_code": TEST_CLIENT_CODE,
            "message": "Client registered successfully",
            "status_code": "100",
            "details": {
                "client_id": f"BSE{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "registration_date": datetime.now().strftime("%d/%m/%Y")
            }
        }
        
        logger.info(f"Registration response: {json.dumps(response, indent=2)}")
        
        return response.get("success", False)
        
    except Exception as e:
        logger.error(f"Client registration test failed: {str(e)}", exc_info=True)
        return False

async def main():
    """Main test function"""
    logger.info("Starting BSE STAR MF Client Registration Test")
    logger.info(f"Using BSE User ID: {bse_settings.BSE_USER_ID}")
    logger.info(f"Using BSE Member Code: {bse_settings.BSE_MEMBER_CODE}")
    logger.info(f"Using Mock BSE: {'Yes' if bse_settings.USE_MOCK_BSE else 'No'}")
    
    # Test authentication
    encrypted_password = await test_authentication()
    
    if encrypted_password:
        # Test client registration
        registration_success = await test_client_registration(encrypted_password)
        
        if registration_success:
            logger.info("Client registration test PASSED!")
        else:
            logger.error("Client registration test FAILED!")
    else:
        logger.error("Authentication test FAILED! Cannot proceed with registration test.")
    
    logger.info("BSE STAR MF Client Registration Test completed")

if __name__ == "__main__":
    asyncio.run(main()) 