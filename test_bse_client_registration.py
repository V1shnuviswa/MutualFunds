#!/usr/bin/env python3
"""
Test script for BSE client registration using the API.
This script demonstrates how to register a client with BSE STAR MF.
"""

import requests
import json
from datetime import datetime

# API configuration
BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/auth/login"
REGISTER_URL = f"{BASE_URL}/api/v1/bse/clients/register"
GENERATE_CODE_URL = f"{BASE_URL}/api/v1/bse/clients/generate-code"

# Authentication credentials
USERNAME = "6385101"
PASSWORD = "Abc@1234"

def get_access_token():
    """Get access token from API"""
    print("Getting access token...")
    response = requests.post(
        AUTH_URL,
        data={"username": USERNAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print(f"Access token: {access_token[:10]}...")
        return access_token
    else:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        return None

def generate_client_code(access_token, client_data):
    """Generate client code using API"""
    print("Generating client code...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.post(
        GENERATE_CODE_URL,
        headers=headers,
        json=client_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Generated client code: {result.get('client_code')}")
        return result.get("client_code")
    else:
        print(f"Client code generation failed: {response.status_code}")
        print(response.text)
        return None

def register_client(access_token, client_data):
    """Register client using API"""
    print("Registering client...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    print("\nSending client data:")
    print(json.dumps(client_data, indent=2))
    
    response = requests.post(
        REGISTER_URL,
        headers=headers,
        json=client_data
    )
    
    print(f"\nResponse status code: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Raw response body: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Client registration successful: {result.get('message')}")
        return result
    else:
        print(f"Client registration failed: {response.status_code}")
        try:
            error_details = response.json()
            print(f"Error details: {json.dumps(error_details, indent=2)}")
        except:
            print(f"Raw error response: {response.text}")
        return None

def main():
    """Main function"""
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("Failed to get access token. Exiting.")
        return
    
    # Client data for code generation
    client_name_data = {
        "PrimaryHolderFirstName": "John",
        "PrimaryHolderLastName": "Doe",
        "PrimaryHolderDOB": "01/01/1990"
    }
    
    # Generate client code
    client_code = generate_client_code(access_token, client_name_data)
    if not client_code:
        # Use a default code if generation fails
        client_code = "0000000004"  # Exactly 10 characters
    
    # Create client registration data
    client_data = {
    "ClientCode": "0111100011",  # Mandatory
    "PrimaryHolderFirstName": "Vishnu",  # Mandatory
    "PrimaryHolderMiddleName": "",  # Optional
    "PrimaryHolderLastName": "Viswakumar",  # Optional
    "TaxStatus": "01",  # Mandatory
    "Gender": "M",  # Mandatory for Individual, NRI and Minor clients
    "PrimaryHolderDOB": "06/09/2004",  # Mandatory (DD/MM/YYYY)
    "OccupationCode": "07",  # Mandatory 01/02/03/04/05/06/07/08/09/10
    "HoldingNature": "SI",  # Mandatory SI/JO/AS
    "SecondHolderFirstName": "",  # Conditional Mandatory if Mode of Holding is JO/AS
    "SecondHolderMiddleName": "",  # Optional
    "SecondHolderLastName": "",  # Conditional Mandatory if Mode of Holding is JO/AS
    "ThirdHolderFirstName": "",  # Optional
    "ThirdHolderMiddleName": "",  # Optional
    "ThirdHolderLastName": "",  # Optional; Mandatory if First Name mentioned
    "SecondHolderDOB": "",  # Conditional Mandatory if Holding is JO/AS
    "ThirdHolderDOB": "",  # Conditional Mandatory if Third holder present
    "GuardianFirstName": "",  # Conditional Mandatory for Minor investment
    "GuardianMiddleName": "",  # Conditional Mandatory for Minor investment
    "GuardianLastName": "",  # Conditional Mandatory for Minor investment
    "GuardianDOB": "",  # Optional; Mandatory for Minor clients (DD/MM/YYYY)
    "PrimaryHolderPANExempt": "N",  # Mandatory
    "SecondHolderPANExempt": "",  # Mandatory if Joint holding and name provided
    "ThirdHolderPANExempt": "",  # Mandatory if Third Holder name provided
    "GuardianPANExempt": "",  # Conditional Mandatory for Minor clients
    "PrimaryHolderPAN": "STUPV4977J",  # Conditional Mandatory if PAN Exempt = N
    "SecondHolderPAN": "",  # Conditional Mandatory if PAN Exempt = N and name provided
    "ThirdHolderPAN": "",  # Conditional Mandatory if PAN Exempt = N and name provided
    "GuardianPAN": "",  # Conditional Mandatory if Guardian name is provided
    "PrimaryExemptCategory": "",  # Conditional Mandatory if PAN Exempt = Y
    "SecondExemptCategory": "",  # Conditional Mandatory if PAN Exempt = Y
    "ThirdExemptCategory": "",  # Conditional Mandatory if PAN Exempt = Y
    "GuardianExemptCategory": "",  # Conditional Mandatory if PAN Exempt = Y
    "ClientType": "P",  # Mandatory (D/P)
    "PMS": "",  # Optional (Y/N)
    "DefaultDP": "",  # Conditional Mandatory if ClientType = D CDSL/NSDL 
    "CDSLDPID": "",  # Conditional Mandatory if Default DP = CDSL
    "CDSLCLTID": "",  # Conditional Mandatory if Default DP = CDSL
    "CMBPID": "",  # Conditional Mandatory if PMS = Y and DP = NSDL
    "NSDLDPID": "",  # Conditional Mandatory if Default DP = NSDL
    "NSDLCLTID": "",  # Conditional Mandatory if Default DP = NSDL
    "AccountType1": "SB",  # Mandatory (SB/CB/NE/NO)
    "AccountNo1": "159012010000322",  # Mandatory
    "MICRNo1": "",  # Optional
    "IFSCCode1": "UBIN0815900",  # Mandatory
    "DefaultBankFlag1": "Y",  # Mandatory (Y/N)
    "AccountType2": "",  # Optional
    "AccountNo2": "",  # Conditional Mandatory if present
    "MICRNo2": "",  # Optional
    "IFSCCode2": "",  # Conditional Mandatory if present
    "DefaultBankFlag2": "",  # Conditional Mandatory if present
    "AccountType3": "",  # Optional
    "AccountNo3": "",  # Conditional Mandatory if present
    "MICRNo3": "",  # Optional
    "IFSCCode3": "",  # Conditional Mandatory if present
    "DefaultBankFlag3": "",  # Conditional Mandatory if present
    "AccountType4": "",  # Optional
    "AccountNo4": "",  # Conditional Mandatory if present
    "MICRNo4": "",  # Optional
    "IFSCCode4": "",  # Conditional Mandatory if present
    "DefaultBankFlag4": "",  # Conditional Mandatory if present
    "AccountType5": "",  # Optional
    "AccountNo5": "",  # Conditional Mandatory if present
    "MICRNo5": "",  # Optional
    "IFSCCode5": "",  # Conditional Mandatory if present
    "DefaultBankFlag5": "",  # Conditional Mandatory if present
    "ChequeName": "",  # Optional
    "DividendPayMode": "02",  # Mandatory (01 = Reinvest, 02 = Payout, 03 = Switch, 04 = Direct Credit, 05 = NEFT/RTGS, 06 = ECS, 07 = NACH, 08 = Auto Sweep, 09 = Systematic Transfer Plan)
    "Address1": "24 1B Rishab avenue",  # Mandatory
    "Address2": "Rajakilpakkam",  # Optional
    "Address3": "Tambaram",  # Optional
    "City": "Chennai",  # Mandatory
    "State": "TN",  # Mandatory
    "Pincode": "600073",  # Mandatory
    "Country": "India",  # Mandatory
    "ResPhone": "",  # Optional
    "ResFax": "",  # Optional
    "OffPhone": "",  # Optional
    "OffFax": "",  # Optional
    "Email": "vishnuviswa1970@gmail.com",  # Mandatory
    "CommunicationMode": "E",  # Mandatory P-Physical, E-Email, M-Mobile
    "ForeignAddress1": "",  # Conditional Mandatory for NRI
    "ForeignAddress2": "",  # Optional
    "ForeignAddress3": "",  # Optional
    "ForeignCity": "",  # Conditional Mandatory for NRI
    "ForeignPincode": "",  # Conditional Mandatory for NRI
    "ForeignState": "",  # Conditional Mandatory for NRI
    "ForeignCountry": "",  # Conditional Mandatory for NRI
    "ForeignResPhone": "",  # Optional
    "ForeignResFax": "",  # Optional
    "ForeignOffPhone": "",  # Optional
    "ForeignOffFax": "",  # Optional
    "IndianMobile": "7010598418",  # Mandatory
    "PrimaryHolderKYCType": "C",  # Mandatory (K/C/B/E)
    "PrimaryHolderCKYC": "50052556759765",  # Conditional Mandatory if KYC Type = C
    "SecondHolderKYCType": "",  # Optional
    "SecondHolderCKYC": "",  # Conditional Mandatory if KYC Type = C
    "ThirdHolderKYCType": "",  # Optional
    "ThirdHolderCKYC": "",  # Conditional Mandatory if KYC Type = C
    "GuardianKYCType": "",  # Optional
    "GuardianCKYC": "",  # Conditional Mandatory if KYC Type = C and Minor
    "PrimaryHolderKRAExemptRefNo": "",  # Conditional Mandatory if Primary Holder PAN Exempt
    "SecondHolderKRAExemptRefNo": "",  # Conditional Mandatory if Second Holder PAN Exempt
    "ThirdHolderKRAExemptRefNo": "",  # Conditional Mandatory if Third Holder PAN Exempt
    "GuardianExemptRefNo": "",  # Conditional Mandatory if Guardian PAN Exempt
    "AadhaarUpdated": "",  # Optional (Y/N)
    "MapinId": "",  # Optional
    "PaperlessFlag": "Z",  # Mandatory; P = Paper, Z = Paperless
    "LEINo": "",  # Optional
    "LEIValidity": "",  # Conditional Mandatory (DD/MM/YYYY)
    "MobileDeclarationFlag": "SE",  # Conditional Mandatory if Mobile No. provided
    "EmailDeclarationFlag": "SE",  # Conditional Mandatory if Email Id provided
    "SecondHolderEmail": "",  # Mandatory if Mode of Holding is JO/AS
    "SecondHolderEmailDeclaration": "",  # Conditional Mandatory if Email provided
    "SecondHolderMobile": "",  # Mandatory if Mode of Holding is JO/AS
    "SecondHolderMobileDeclaration": "",  # Conditional Mandatory if Mobile No. provided
    "ThirdHolderEmail": "",  # Mandatory if Third Holder is present
    "ThirdHolderEmailDeclaration": "",  # Conditional Mandatory if Email provided
    "ThirdHolderMobile": "",  # Mandatory if Third Holder is present
    "ThirdHolderMobileDeclaration": "",  # Conditional Mandatory if Mobile No. provided
    "GuardianRelationship": "",  # Conditional Mandatory; 23 - FATHER, 24 - MOTHER, etc.
    "NominationOpt": "Y",  # Optional for Demat; Mandatory for Non-Demat SI Holding
    "NominationAuthMode": "O",  # Optional; W = Wet, E = eSign, O = OTP
    "Nominee1Name": "Srisha Viswakumar",  # Conditional Mandatory if NominationOpt = Y
    "Nominee1Relationship": "13",  # Conditional Mandatory if Nominee present
    "Nominee1ApplicablePercent": "100",  # Conditional Mandatory if Nominee present
    "Nominee1MinorFlag": "N",  # Conditional Mandatory if Nominee present
    "Nominee1DOB": "",  # Conditional Mandatory if MinorFlag = Y
    "Nominee1Guardian": "",  # Optional
    "Nominee1GuardianPAN": "",  # Optional
    "Nominee1IdentityType": "1",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1IDNumber": "HKBPS9322D",  # Conditional Mandatory if ID Type provided
    "Nominee1Email": "srisha1010@gmail.com",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Mobile": "9941239973",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Address1": "24 1B Rishab avenue",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Address2": "Rajakilpakkam",  # Optional
    "Nominee1Address3": "Tambaram",  # Optional
    "Nominee1City": "Chennai",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Pincode": "600073",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Country": "India",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee2Name": "",  # Conditional Mandatory if Nominee1 < 100%
    "Nominee2Relationship": "",  # Conditional Mandatory if Nominee2 available
    "Nominee2ApplicablePercent": "",  # Conditional Mandatory if Nominee2 available
    "Nominee2MinorFlag": "",  # Conditional Mandatory if Nominee2 available
    "Nominee2DOB": "",  # Conditional Mandatory if Nominee2 available
    "Nominee2Guardian": "",  # Optional
    "Nominee2GuardianPAN": "",  # Optional
    "Nominee2IdentityType": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2IDNumber": "",  # Conditional Mandatory based on ID Type
    "Nominee2Email": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Mobile": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Address1": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Address2": "",  # Optional
    "Nominee2Address3": "",  # Optional
    "Nominee2City": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Pincode": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Country": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee3Name": "",  # Conditional Mandatory if % < 100%
    "Nominee3Relationship": "",  # Conditional Mandatory if Nominee3 available
    "Nominee3ApplicablePercent": "",  # Conditional Mandatory if Nominee3 available
    "Nominee3MinorFlag": "",  # Conditional Mandatory if Nominee3 available
    "Nominee3DOB": "",  # Conditional Mandatory if Nominee3 available
    "Nominee3Guardian": "",  # Optional
    "Nominee3GuardianPAN": "",  # Optional
    "Nominee3IdentityType": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3IDNumber": "",  # Conditional Mandatory based on ID Type
    "Nominee3Email": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Mobile": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Address1": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Address2": "",  # Optional
    "Nominee3Address3": "",  # Optional
    "Nominee3City": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Pincode": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Country": "",  # Conditional Mandatory if Nominee3 Opted
    "NomineeSOAFlag": "Y",  # Mandatory if NomineeOpt = Y; Y/N display in SOA
    "Filler1": "",  # Optional
    "Filler2": "",  # Optional
    "Filler3": "",  # Optional
    "Filler4": "",  # Optional
    "Filler5": "",  # Optional
    "Filler6": "",  # Optional
    "Filler7": "",  # Optional
    "Filler8": "",  # Optional
    }
    
    # Register client
    result = register_client(access_token, client_data)
    if result:
        print("\nClient registration completed successfully.")
        print("BSE API Response Details:")
        print(json.dumps(result, indent=2))
        
        # Extract BSE response details
        if "details" in result:
            bse_response = result.get("details", {})
            print("\nBSE Status Code:", bse_response.get("Status"))
            print("BSE Remarks:", bse_response.get("Remarks"))
            print("BSE Filler1:", bse_response.get("Filler1"))
            print("BSE Filler2:", bse_response.get("Filler2"))
    else:
        print("\nClient registration failed.")

if __name__ == "__main__":
    main()
