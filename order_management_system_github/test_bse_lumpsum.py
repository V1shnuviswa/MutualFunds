#!/usr/bin/env python3

import requests
import json

print("Testing the BSE-compliant lumpsum order endpoint...")
BASE_URL = "http://localhost:8000"
BSE_LUMPSUM_ENDPOINT = "/api/v1/bse/lumpsum"

# Create a valid payload based on BSE STAR MF specifications
payload = {
    "TransCode": "NEW",
    "TransNo": "20240101MEMBER-000001",
    "UserId": "USER1",
    "MemberId": "MEMBER01",
    "ClientCode": "CLIENT001",
    "SchemeCd": "BSE123456",
    "BuySell": "P",
    "BuySellType": "FRESH",
    "DPTxn": "P",
    "Amount": 5000,
    "DPC": "N",
    "Password": "encrypted_password",
    "PassKey": "PASSKEY123"
}

# Send the request
print(f"Sending POST request to {BASE_URL}{BSE_LUMPSUM_ENDPOINT}")
print(f"Request payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}{BSE_LUMPSUM_ENDPOINT}",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Response status code: {response.status_code}")
    if response.status_code == 422:
        print("Unprocessable Entity Error (422) - Check your payload format")
        error_detail = response.json()
        print(f"Error details: {json.dumps(error_detail, indent=2)}")
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")

except Exception as e:
    print(f"Error occurred: {str(e)}")

print("\nTest complete.") 