# Order Management System API Structure

This document outlines the proposed API structure for the Order Management System, inspired by the BSE StAR MF Webservice Structure document provided.
The API will use JSON for request and response bodies.

## Base URL

`/api/v1` (Placeholder)

## Authentication

### POST /auth/login

Authenticates a user/member and returns a session token for subsequent requests.

**Request Body:**

```json
{
  "userId": "string",
  "memberId": "string",
  "password": "string", // Plain password, system handles encryption/hashing
  "passKey": "string" // Optional, based on PDF
}
```

**Response Body (Success):**

```json
{
  "status": "Success",
  "token": "string", // Session token (e.g., JWT)
  "message": "Authentication successful."
}
```

**Response Body (Error):**

```json
{
  "status": "Failed",
  "message": "Error description (e.g., Invalid credentials)"
}
```

## Order Management

### POST /orders/lumpsum

Places a new lumpsum purchase or redemption order.

**Request Body:**

```json
{
  "transactionType": "PURCHASE | REDEMPTION",
  "uniqueRefNo": "string", // Client-generated unique reference
  "clientCode": "string",
  "schemeCode": "string",
  "amount": "number",
  "folioNo": "string", // Optional, required for redemption/additional purchase
  "dpTxnMode": "string", // Optional (e.g., 'P' for Physical, 'D' for Demat)
  "kycStatus": "Y | N",
  "euin": "string", // Optional
  "euinDeclared": "Y | N", // Optional
  "ipAddress": "string" // Optional
  // Add other relevant optional fields from PDF as needed: 
  // subArnCode, remarks, dpcFlag, etc.
}
```

**Response Body (Success):**

```json
{
  "statusCode": "100", // Example success code from PDF
  "message": "Order placed successfully.",
  "clientCode": "string",
  "orderId": "string", // System-generated order ID
  "uniqueRefNo": "string",
  "bseRemarks": "string", // Optional
  "successFlag": "Y"
}
```

**Response Body (Error):**

```json
{
  "statusCode": "string", // Error code from PDF
  "message": "Error description",
  "clientCode": "string",
  "uniqueRefNo": "string",
  "successFlag": "N"
}
```

### POST /orders/sip

Registers a new Systematic Investment Plan (SIP).

**Request Body:**

```json
{
  "uniqueRefNo": "string",
  "schemeCode": "string",
  "clientCode": "string",
  "folioNo": "string", // Optional
  "amount": "number",
  "frequency": "MONTHLY | QUARTERLY | etc.", // Based on allowed values
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "firstOrderToday": "Y | N",
  "mandateId": "string", // Optional
  "euin": "string", // Optional
  "euinDeclared": "Y | N", // Optional
  "ipAddress": "string" // Optional
  // Add other relevant optional fields from PDF as needed: 
  // subArnCode, remarks, dpcFlag, brokerage, etc.
}
```

**Response Body (Success):**

```json
{
  "statusCode": "100", // Example success code
  "message": "SIP registration successful.",
  "clientCode": "string",
  "sipRegId": "string", // System-generated SIP registration ID
  "uniqueRefNo": "string",
  "bseRemarks": "string", // Optional
  "successFlag": "Y"
}
```

**Response Body (Error):**

```json
{
  "statusCode": "string", // Error code
  "message": "Error description",
  "clientCode": "string",
  "uniqueRefNo": "string",
  "successFlag": "N"
}
```

## Reporting

### GET /reports/order_status

Retrieves the status of orders based on specified criteria.

**Query Parameters:**

- `clientCode` (string, required)
- `fromDate` (string, YYYY-MM-DD, required)
- `toDate` (string, YYYY-MM-DD, required)
- `orderId` (string, optional)
- `status` (string, optional) - e.g., 'PENDING', 'EXECUTED', 'REJECTED'
- `memberId` (string, required) - Assuming needed based on PDF context

**Response Body (Success):**

```json
{
  "status": "Success",
  "data": [
    {
      "orderId": "string",
      "orderDate": "YYYY-MM-DD",
      "orderTime": "HH:MM:SS",
      "clientCode": "string",
      "clientName": "string", // Optional
      "schemeCode": "string",
      "schemeName": "string", // Optional
      "orderType": "PURCHASE | REDEMPTION | SIP | etc.",
      "quantity": "number", // Or amount depending on context
      "price": "number", // NAV
      "folioNo": "string",
      "orderStatus": "string", // e.g., 'Processed', 'Rejected'
      "allotmentDate": "YYYY-MM-DD", // Optional
      "transactionType": "string",
      "remarks": "string" // Optional
      // Add other relevant fields from PDF response as needed
    }
    // ... more orders
  ]
}
```

**Response Body (Error):**

```json
{
  "status": "Failed",
  "message": "Error description"
}
```

## Notes

- This structure focuses on core order management functions (Auth, Lumpsum, SIP, Status).
- The PDF describes many other functions (Client Mgmt, Mandates, Payments, etc.) which can be added later.
- Error handling details and specific codes need further refinement based on the PDF's error code sections.
- Data validation rules for each field need to be implemented based on the PDF.
- The choice between SOAP/WSDL (as heavily featured in the PDF) and JSON (used here) depends on the final requirements. JSON is generally preferred for new web APIs.

