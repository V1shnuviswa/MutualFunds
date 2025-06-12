# Order Management System API Usage Guide

## Lumpsum Order Example

To place a lumpsum order, send a POST request to `/api/v1/orders/lumpsum` with the following JSON payload:

```json
{
  "uniqueRefNo": "ORD123456789",
  "clientCode": "CLIENT001",
  "schemeCode": "BSE123456", 
  "transactionType": "PURCHASE",
  "dpTxnMode": "P",
  "amount": 5000,
  "quantity": null,
  "folioNo": "",
  "euinDeclared": "Y", 
  "euin": "",
  "subArnCode": "",
  "remarks": "Test lumpsum order",
  "ipAddress": "127.0.0.1"
}
```

### Required Fields:

- `uniqueRefNo`: A unique reference number for this order
- `clientCode`: Client code registered with BSE
- `schemeCode`: BSE scheme code for the mutual fund
- `transactionType`: Either "PURCHASE" or "REDEMPTION"
- `dpTxnMode`: Transaction mode (P = Physical, D = Demat)
- Either `amount` or `quantity` must be provided

### Response:

```json
{
  "message": "Order placed successfully",
  "order_id": "12345",
  "unique_ref_no": "ORD123456789",
  "bse_order_id": "BSE12345",
  "status": "SUCCESS",
  "bse_status_code": "1",
  "bse_remarks": "Order placed successfully"
}
```

## Common Errors

1. **Authentication Error**: Make sure you're authenticated. Send a POST request to `/auth/login` first.

2. **Invalid Input**: Ensure all required fields are provided.

3. **BSE Connection Error**: If BSE services are unavailable, the API will return a 502 error.

## Authorizing in Swagger UI

1. Click on the "Authorize" button in Swagger UI
2. Use the `/auth/login` endpoint to get a token
3. Copy the token and paste it in the "Value" field (prefix with "Bearer ")
4. Click "Authorize" 