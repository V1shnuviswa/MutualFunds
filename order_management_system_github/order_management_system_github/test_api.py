import requests
import json

# Test the lumpsum order endpoint
base_url = "http://localhost:8000"

# Login to get token
login_data = {
    "username": "admin",
    "password": "password"
}

# Get auth token
print("Attempting login...")
login_response = requests.post(f"{base_url}/auth/login", data=login_data)
print(f"Login Status Code: {login_response.status_code}")
print(f"Login Response: {login_response.text}")

if login_response.status_code == 200:
    token = login_response.json().get("access_token")
    print(f"Got token: {token[:10]}...")

    # Set headers with token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Sample payload for lumpsum order
    payload = {
        "uniqueRefNo": "ORD123456789",
        "clientCode": "CLIENT001",
        "schemeCode": "BSE123456",
        "transactionType": "PURCHASE",
        "dpTxnMode": "P",
        "amount": 5000,
        "folioNo": "FOLIO123456",
        "euinDeclared": "Y",
        "euin": "E123456",
        "subArnCode": "SA001",
        "remarks": "Sample lumpsum purchase order",
        "ipAddress": "192.168.1.100",
        "allUnitsFlag": False,
        "kycStatus": "Y"
    }

    print(f"\nSending lumpsum order with payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: {headers}")
    
    # Make the API call
    response = requests.post(f"{base_url}/api/v1/orders/lumpsum", headers=headers, json=payload)

    # Print status code and response
    print(f"Lumpsum Order Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print("\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
else:
    print(f"Login failed: {login_response.text}") 