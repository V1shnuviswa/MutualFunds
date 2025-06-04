# BSE SOAP Integration External Validation Guide

This document provides step-by-step instructions for validating the BSE SOAP integration in an environment with network access to BSE STAR MF endpoints.

## Prerequisites

1. An environment with network access to BSE STAR MF endpoints
2. BSE STAR MF credentials (User ID, Password, Member Code)
3. The Order Management System codebase (`order_management_system.zip`)

## Setup Instructions

### 1. Deploy the Code

```bash
# Extract the code
unzip order_management_system.zip -d order_management_system
cd order_management_system

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python setup_db.py
```

### 2. Configure BSE Credentials

Create a `.env` file in the project root with the following content:

```
# BSE STAR MF Credentials
BSE_USER_ID=your_bse_user_id
BSE_PASSWORD=your_bse_password
BSE_MEMBER_CODE=your_bse_member_code

# BSE STAR MF WSDL URLs
# For Demo environment
BSE_AUTH_WSDL=https://bsestarmfdemo.bseindia.com/MFUploadService/MFUploadService.svc?wsdl
BSE_ORDER_ENTRY_WSDL=https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl
BSE_CLIENT_REG_WSDL=https://bsestarmfdemo.bseindia.com/ClientRegistration/ClientRegistration.svc?wsdl

# For Production environment (uncomment when ready)
# BSE_AUTH_WSDL=https://bsestarmf.bseindia.com/MFUploadService/MFUploadService.svc?wsdl
# BSE_ORDER_ENTRY_WSDL=https://bsestarmf.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl
# BSE_CLIENT_REG_WSDL=https://bsestarmf.bseindia.com/ClientRegistration/ClientRegistration.svc?wsdl

# BSE Session Timeout (in seconds)
BSE_SESSION_TIMEOUT=28800
```

### 3. Run the Test Script

Create a test script to validate connectivity:

```bash
# Copy the test script
cp /path/to/bse_test_connectivity.py .

# Run the test script
python bse_test_connectivity.py
```

The test script should output a successful authentication response if connectivity is working correctly.

## Validation Steps

### 1. Test Authentication

1. Start the API server:
   ```bash
   cd order_management_system
   uvicorn src.main:app --reload
   ```

2. Create a test user:
   ```bash
   curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpassword","email":"test@example.com"}'
   ```

3. Get an authentication token:
   ```bash
   curl -X POST "http://localhost:8000/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpassword"}'
   ```

4. Test BSE authentication:
   ```bash
   curl -X POST "http://localhost:8000/orders/bse-auth" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"passKey":"YOUR_PASS_KEY"}'
   ```

### 2. Test Lumpsum Order Placement

```bash
curl -X POST "http://localhost:8000/orders/lumpsum" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "schemeCode": "BSE_SCHEME_CODE",
    "clientCode": "CLIENT_CODE",
    "transactionType": "PURCHASE",
    "amount": 5000,
    "folioNo": "",
    "uniqueRefNo": "REF123456",
    "passkey": "YOUR_PASS_KEY"
  }'
```

### 3. Test SIP Order Registration

```bash
curl -X POST "http://localhost:8000/orders/sip" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "schemeCode": "BSE_SCHEME_CODE",
    "clientCode": "CLIENT_CODE",
    "frequency": "MONTHLY",
    "installmentAmount": 1000,
    "noOfInstallments": 12,
    "startDate": "2025-07-01",
    "mandateId": "MANDATE123",
    "folioNo": "",
    "uniqueRefNo": "SIPREF123456",
    "passkey": "YOUR_PASS_KEY"
  }'
```

## Troubleshooting

### Check Logs

Monitor the application logs for detailed information:

```bash
tail -f uvicorn.log
```

### Common Issues

1. **Authentication Failures**
   - Verify BSE credentials in the `.env` file
   - Check if the BSE user account is active
   - Ensure the passkey format is correct

2. **Connection Timeouts**
   - Verify network connectivity to BSE endpoints
   - Check if any firewall is blocking outbound SOAP requests
   - Ensure the WSDL URLs are correct for your environment (Demo/Production)

3. **SOAP Faults**
   - Check the request payload format
   - Verify that all required fields are provided
   - Ensure date formats match BSE requirements (DD/MM/YYYY)

## Logging Enhancement

To enable more detailed logging for troubleshooting:

1. Edit `src/bse_integration/auth.py` and `src/bse_integration/order.py`
2. Change the logging level:
   ```python
   logging.basicConfig(level=logging.DEBUG)  # Change from INFO to DEBUG
   ```

3. Add request/response payload logging with sensitive data masking:
   ```python
   # Example for masking sensitive data in logs
   def _mask_sensitive_data(self, data):
       masked_data = data.copy()
       if "Password" in masked_data:
           masked_data["Password"] = "********"
       return masked_data
   
   # Log masked request data
   masked_request = self._mask_sensitive_data(request_data)
   logger.debug(f"BSE Auth Request: {masked_request}")
   ```

## Next Steps After Validation

1. Implement proper error handling based on actual BSE responses
2. Add retry mechanisms for transient failures
3. Implement comprehensive logging for production use
4. Consider adding monitoring for BSE API health
5. Develop a test suite for regression testing

## Support

For issues related to the BSE integration, please refer to:
1. BSE STAR MF documentation
2. The reference GitHub repository: https://github.com/V1shnuviswa/MutualFunds
3. The BSE integration code in `src/bse_integration/`
