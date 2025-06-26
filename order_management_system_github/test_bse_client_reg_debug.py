#!/usr/bin/env python3
"""
Test script for BSE client registration with detailed debugging.
This script directly tests the BSEClientRegistrar class.
"""

import asyncio
import logging
import json
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bse_client_reg_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the path
sys.path.append('.')

# Import the BSEClientRegistrar
from src.bse_integration.client_registration import BSEClientRegistrar
from src.bse_integration.exceptions import BSEIntegrationError, BSEValidationError

async def test_client_registration():
    """Test BSE client registration with a sample client"""
    try:
        # Create client registrar
        client_registrar = BSEClientRegistrar()
        
        # Sample client data with all required fields in the correct order
        client_data = {
            "ClientCode": "0000000004",
            "PrimaryHolderFirstName": "Vishnu",
            "PrimaryHolderMiddleName": "",
            "PrimaryHolderLastName": "Viswa",
            "TaxStatus": "01",                     # Individual
            "Gender": "M",
            "DOB": "06/09/2004",                   # DD/MM/YYYY format
            "OccupationCode": "01",                # Business
            "HoldingNature": "SI",                 # Single
            "DividendPayMode": "01",               # Reinvest
            "SecondHolderFirstName": "",
            "SecondHolderMiddleName": "",
            "SecondHolderLastName": "",
            "ThirdHolderFirstName": "",
            "ThirdHolderMiddleName": "",
            "ThirdHolderLastName": "",
            "SecondHolderDOB": "",
            "ThirdHolderDOB": "",
            "GuardianFirstName": "",
            "GuardianMiddleName": "",
            "GuardianLastName": "",
            "GuardianDOB": "",
            "PrimaryHolderPANExempt": "N",
            "SecondHolderPANExempt": "",
            "ThirdHolderPANExempt": "",
            "GuardianPANExempt": "",
            "PrimaryHolderPAN": "ABCDE1234F",
            "SecondHolderPAN": "",
            "ThirdHolderPAN": "",
            "GuardianPAN": "",
            "PrimaryExemptCategory": "",
            "SecondExemptCategory": "",
            "ThirdExemptCategory": "",
            "GuardianExemptCategory": "",
            "ClientType": "P",                     # Physical
            "PMS": "N",
            "DefaultDP": "",                       # Empty for Physical
            "CDSLDPID": "",                        # Empty for Physical
            "CDSLCLTID": "",                       # Empty for Physical
            "CMBPID": "",
            "NSDLDPID": "",                        # Empty for Physical
            "NSDLCLTID": "",                       # Empty for Physical
            "AccountType1": "SB",                  # Savings Bank
            "AccountNo1": "12345678901",
            "MICRNo1": "",
            "IFSCCode1": "HDFC0000001",
            "DefaultBankFlag1": "Y",
            "AccountType2": "",
            "AccountNo2": "",
            "MICRNo2": "",
            "IFSCCode2": "",
            "DefaultBankFlag2": "",
            "AccountType3": "",
            "AccountNo3": "",
            "MICRNo3": "",
            "IFSCCode3": "",
            "DefaultBankFlag3": "",
            "AccountType4": "",
            "AccountNo4": "",
            "MICRNo4": "",
            "IFSCCode4": "",
            "DefaultBankFlag4": "",
            "AccountType5": "",
            "AccountNo5": "",
            "MICRNo5": "",
            "IFSCCode5": "",
            "DefaultBankFlag5": "",
            "ChequeName": "Vishnu Viswa",
            "Address1": "123 Main Street",
            "Address2": "",
            "Address3": "",
            "City": "Mumbai",
            "State": "Maharashtra",
            "Pincode": "400001",
            "Country": "India",
            "ResPhone": "",
            "ResFax": "",
            "OffPhone": "",
            "OffFax": "",
            "Email": "vishnuviswa1970@gmail.com",
            "CommunicationMode": "E",              # Email
            "ForeignAddress1": "",
            "ForeignAddress2": "",
            "ForeignAddress3": "",
            "ForeignCity": "",
            "ForeignPincode": "",
            "ForeignState": "",
            "ForeignCountry": "",
            "ForeignResPhone": "",
            "ForeignResFax": "",
            "ForeignOffPhone": "",
            "ForeignOffFax": "",
            "IndianMobile": "7010598418",
            "Nominee1Name": "",
            "Nominee1Relationship": "",
            "Nominee1Percentage": "",
            "Nominee1MinorFlag": "",
            "Nominee1DOB": "",
            "Nominee1Guardian": "",
            "Nominee2Name": "",
            "Nominee2Relationship": "",
            "Nominee2Percentage": "",
            "Nominee2MinorFlag": "",
            "Nominee2DOB": "",
            "Nominee2Guardian": "",
            "Nominee3Name": "",
            "Nominee3Relationship": "",
            "Nominee3Percentage": "",
            "Nominee3MinorFlag": "",
            "Nominee3DOB": "",
            "Nominee3Guardian": "",
            "PrimaryHolderKYCType": "K",           # KYC
            "PrimaryHolderCKYCNumber": "",
            "SecondHolderKYCType": "",
            "SecondHolderCKYCNumber": "",
            "ThirdHolderKYCType": "",
            "ThirdHolderCKYCNumber": "",
            "GuardianKYCType": "",
            "GuardianCKYCNumber": "",
            "PrimaryHolderKRAExemptRefNo": "",
            "SecondHolderKRAExemptRefNo": "",
            "ThirdHolderKRAExemptRefNo": "",
            "GuardianKRAExemptRefNo": "",
            "AadhaarUpdated": "",
            "MapinId": "",
            "PaperlessFlag": "Z",                  # Paperless
            "LEINo": "",
            "LEIValidity": "",
            "MobileDeclarationFlag": "Y",
            "EmailDeclarationFlag": "Y"
        }
        
        # Log the client data
        logger.info("Client data for registration:")
        logger.info(json.dumps(client_data, indent=2))
        
        # Register client
        logger.info("Registering client...")
        response = await client_registrar.register_client(client_data)
        
        # Log the response
        logger.info("Registration response:")
        logger.info(json.dumps(response, indent=2))
        
        # Check response status
        if response.get("Status") == "100":
            logger.info("Client registration successful!")
        else:
            logger.error(f"Client registration failed with status {response.get('Status')}: {response.get('Remarks')}")
        
        return response
    
    except BSEValidationError as e:
        logger.error(f"Validation error: {e}")
        return {"error": str(e)}
    
    except BSEIntegrationError as e:
        logger.error(f"Integration error: {e}")
        return {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"error": str(e)}

if __name__ == "__main__":
    logger.info("Starting BSE client registration test")
    
    # Run the test
    result = asyncio.run(test_client_registration())
    
    # Print the result
    print("\nFinal result:")
    print(json.dumps(result, indent=2)) 