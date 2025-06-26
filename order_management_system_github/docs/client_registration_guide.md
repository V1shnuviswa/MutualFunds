# BSE Client Registration Guide

This guide explains how to register clients with BSE STAR MF using the Order Management System API.

## Client Registration Options

The system provides two ways to register clients with BSE STAR MF:

1. **Step-by-Step Registration Process** - A multi-step workflow that guides users through the registration process
2. **Direct BSE Registration** - A single-step process for direct registration with BSE

Both approaches are handled by the same module and ultimately register the client with BSE STAR MF.

## Step-by-Step Registration Process

This approach breaks down the registration into multiple steps:

1. Start registration (`/api/v1/registration/start`)
2. Complete steps 1-8 (`/api/v1/registration/step/{step_number}`)
3. Complete registration (`/api/v1/registration/complete`)

This approach is recommended for user interfaces that need to guide users through the registration process.

## Direct BSE Registration

This approach allows direct registration with BSE in a single step:

1. Generate client code (optional) (`/api/v1/bse/clients/generate-code`)
2. Register client (`/api/v1/bse/clients/register`)

This approach is recommended for automated processes or when all client information is already available.

## Mandatory Fields

Based on BSE requirements, the following fields are mandatory for client registration:

| Field | Description | Example |
|-------|-------------|---------|
| ClientCode | Unique client code | "DTJOHNDOE1990" |
| PrimaryHolderFirstName | First name of primary holder | "John" |
| TaxStatus | Tax status code | "01" (Individual) |
| Gender | Gender (M/F/O) | "M" |
| DOB | Date of birth (DD/MM/YYYY) | "01/01/1990" |
| OccupationCode | Occupation code (01-10) | "01" (Business) |
| HoldingNature | Holding nature (SI/JO/AS) | "SI" (Single) |
| PrimaryHolderPANExempt | PAN exempt flag (Y/N) | "N" |
| PrimaryHolderPAN | PAN number (if not exempt) | "ABCDE1234F" |
| ClientType | Client type (D/P) | "P" (Physical) |
| AccountType1 | Account type (SB/CB/NE/NO) | "SB" (Savings) |
| AccountNo1 | Account number | "12345678901" |
| IFSCCode1 | IFSC code | "HDFC0000001" |
| DefaultBankFlag1 | Default bank flag (Y/N) | "Y" |
| DividendPayMode | Dividend pay mode | "01" (Reinvest) |
| Address1 | Address line 1 | "123 Main Street" |
| City | City | "Mumbai" |
| State | State | "Maharashtra" |
| Pincode | Pincode | "400001" |
| Country | Country | "India" |
| Email | Email address | "john.doe@example.com" |
| CommunicationMode | Communication mode (P/E/M) | "E" (Email) |
| IndianMobile | Mobile number | "9876543210" |
| PrimaryHolderKYCType | KYC type (K/C/B/E) | "K" (KYC) |
| PaperlessFlag | Paperless flag (P/Z) | "Z" (Paperless) |

### Conditional Mandatory Fields

Some fields are mandatory only under certain conditions:

1. If `HoldingNature` is "JO" (Joint) or "AS" (Anyone or Survivor):
   - SecondHolderFirstName
   - SecondHolderLastName
   - SecondHolderDOB

2. If `PrimaryHolderPANExempt` is "N":
   - PrimaryHolderPAN

3. If `ClientType` is "D" (Demat):
   - DefaultDP

4. If `DefaultDP` is "CDSL":
   - CDSLDPID
   - CDSLCLTID

5. If `DefaultDP` is "NSDL":
   - NSDLDPID
   - NSDLCLTID

## API Endpoints

### Authentication

```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=6385101&password=Abc@1234
```

### Direct BSE Registration

#### Generate Client Code

```
POST /api/v1/bse/clients/generate-code
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "PrimaryHolderFirstName": "John",
  "PrimaryHolderLastName": "Doe",
  "DOB": "01/01/1990"
}
```

#### Register Client

```
POST /api/v1/bse/clients/register
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "ClientCode": "DTJOHNDOE1990",
  "PrimaryHolderFirstName": "John",
  "PrimaryHolderLastName": "Doe",
  "TaxStatus": "01",
  "Gender": "M",
  "DOB": "01/01/1990",
  "OccupationCode": "01",
  "HoldingNature": "SI",
  "PrimaryHolderPANExempt": "N",
  "PrimaryHolderPAN": "ABCDE1234F",
  "ClientType": "P",
  "AccountType1": "SB",
  "AccountNo1": "12345678901",
  "IFSCCode1": "HDFC0000001",
  "DefaultBankFlag1": "Y",
  "DividendPayMode": "01",
  "Address1": "123 Main Street",
  "City": "Mumbai",
  "State": "Maharashtra",
  "Pincode": "400001",
  "Country": "India",
  "Email": "john.doe@example.com",
  "CommunicationMode": "E",
  "IndianMobile": "9876543210",
  "PrimaryHolderKYCType": "K",
  "PaperlessFlag": "Z"
}
```

#### Update Client

```
POST /api/v1/bse/clients/update
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "ClientCode": "DTJOHNDOE1990",
  ... (fields to update)
}
```

### Step-by-Step Registration

#### Start Registration

```
POST /api/v1/registration/start
Content-Type: application/json
Authorization: Bearer <access_token>
```

#### Process Step 1

```
POST /api/v1/registration/step/1
Content-Type: application/json
Authorization: Bearer <access_token>

{
  ... (step 1 data)
}
```

#### Complete Registration

```
POST /api/v1/registration/complete
Content-Type: application/json
Authorization: Bearer <access_token>
```

## Sample Code

See the `test_bse_client_registration.py` and `test_client_registration.ps1` scripts for complete examples of client registration.

## Reference Codes

### Tax Status Codes

- 01: Individual
- 02: On Behalf of Minor
- 03: HUF
- 04: Company
- 05: AOP/BOI
- 06: Partnership Firm
- 07: Trust
- 08: NRI
- 09: FII
- 10: FPI

### Occupation Codes

- 01: Business
- 02: Services
- 03: Professional
- 04: Agriculture
- 05: Retired
- 06: Housewife
- 07: Student
- 08: Others
- 09: Not Specified
- 10: Doctor

### KYC Types

- K: KYC
- C: CKYC
- B: Both
- E: EKYC

### Holding Nature

- SI: Single
- JO: Joint
- AS: Anyone or Survivor 