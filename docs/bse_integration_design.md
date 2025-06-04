# BSE SOAP API Integration Design

This document outlines the design for integrating BSE STAR MF SOAP APIs into the existing FastAPI-based Order Management System, based on the reference implementation provided.

## 1. Overview

The goal is to replace the simulated BSE interactions with actual SOAP calls for:
- User Authentication (getPassword)
- Client Registration (if applicable based on reference analysis - `bse_client.py` suggests this)
- Order Placement (Lumpsum, SIP)

We will use the `zeep` library for SOAP communication.

## 2. Core Modules

A new package `src/bse_integration` will be created to encapsulate all BSE SOAP interaction logic.

### 2.1. `src/bse_integration/config.py`
- Will use Pydantic `BaseSettings` to load configuration from environment variables or a `.env` file.
- Parameters:
    - `BSE_USER_ID`
    - `BSE_PASSWORD`
    - `BSE_MEMBER_CODE`
    - `BSE_ORDER_ENTRY_WSDL` (e.g., `https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl`)
    - `BSE_REGISTRATION_WSDL` (e.g., `https://bsestarmfdemo.bseindia.com/StarMFCommonAPI/StarMFCommonAPI.svc?wsdl` - *assuming registration uses a different WSDL based on reference paths*)
    - `BSE_AUTH_WSDL` (Likely same as Order Entry WSDL, but confirm from reference `bse_auth.py` usage)
    - `BSE_SESSION_TIMEOUT` (e.g., 3600 seconds)

### 2.2. `src/bse_integration/exceptions.py`
- Define custom exceptions for BSE integration errors, inheriting from a base `BSEIntegrationError`.
- Examples: `BSEAuthError`, `BSEOrderError`, `BSEClientRegError`, `BSETransportError`, `BSESoapFault`.
- Map specific BSE error codes (from reference `bse_auth.py` and potentially others) to these exceptions.

### 2.3. `src/bse_integration/auth.py`
- Class `BSEAuthenticator` (inspired by `BSEMFAuth` in reference).
- Responsibilities:
    - Initialize `zeep` client for the authentication service.
    - Implement `authenticate(passkey)` method to call BSE's `getPassword` SOAP method.
    - Manage session state: store `encrypted_password` and `session_valid_until`.
    - Implement `get_encrypted_password()` method, handling automatic re-authentication if session is expired (using the last successful `passkey`).
    - Handle SOAP faults, transport errors, and specific authentication error codes, raising exceptions from `exceptions.py`.
    - Use `async/await` for SOAP calls if `zeep` supports it well with the target WSDL.

### 2.4. `src/bse_integration/client_registration.py`
- Class `BSEClientRegistrar` (inspired by `BSEClientRegistration` in reference `bse_client.py`).
- Responsibilities:
    - Initialize `zeep` client for the client registration service (potentially StarMFCommonAPI).
    - Implement methods for client registration SOAP calls (e.g., `register_client(client_data)`).
    - Construct SOAP request messages based on required fields (referencing `fields.py` from reference).
    - Parse SOAP responses.
    - Handle errors and raise exceptions from `exceptions.py`.
    - Use `async/await`.

### 2.5. `src/bse_integration/order.py`
- Class `BSEOrderPlacer` (inspired by `SOAPMessageHandler` in reference `bse_order_manage.py` and logic in `orders_api.py`).
- Responsibilities:
    - Initialize `zeep` client for the order entry service.
    - Implement methods for placing orders: `place_lumpsum_order(order_data, encrypted_password)`, `place_sip_order(sip_data, encrypted_password)`.
    - Construct SOAP order request messages, including the `encrypted_password` obtained from `BSEAuthenticator`.
    - Map data from FastAPI request schemas (`schemas.LumpsumOrderCreate`, `schemas.SIPOrderCreate`) to SOAP fields.
    - Parse SOAP responses (success codes, BSE order IDs, remarks).
    - Handle errors and raise exceptions from `exceptions.py`.
    - Use `async/await`.

## 3. Integration Points

### 3.1. Dependencies
- Add `zeep` to `/home/ubuntu/order_management_system/requirements.txt`.
- Create instances of `BSEAuthenticator`, `BSEClientRegistrar`, `BSEOrderPlacer` (potentially as FastAPI dependencies or singletons).

### 3.2. Authentication Middleware/Dependency
- The existing `dependencies.get_current_active_user` handles API-level auth (JWT).
- BSE authentication needs to happen *before* placing orders.
- The `BSEAuthenticator` instance can be managed globally or passed to the order placement functions.

### 3.3. Router Modifications (`src/routers/orders.py`)
- Inject `BSEAuthenticator` and `BSEOrderPlacer` dependencies.
- In `place_lumpsum_order` and `register_sip_order`:
    - Remove database checks for client/scheme existence if BSE handles this validation.
    - Remove duplicate `uniqueRefNo` check if BSE handles it (or keep as a pre-check).
    - **Crucially:** Before constructing the SOAP request:
        - Call `bse_authenticator.get_encrypted_password()` to get the valid encrypted password (this might trigger re-authentication).
    - Call `bse_order_placer.place_lumpsum_order()` or `bse_order_placer.place_sip_order()`, passing the order data and encrypted password.
    - Remove the simulated BSE interaction logic.
    - Update `crud.update_order_status` call with actual data from the BSE SOAP response (BSE Order ID, status, remarks).
    - Map the BSE SOAP response to the FastAPI response model (`schemas.LumpsumOrderResponse`, `schemas.SIPOrderResponse`).
    - Implement try/except blocks to catch `BSEIntegrationError` exceptions and return appropriate HTTP responses (e.g., 400, 500, 503).

### 3.4. New Client Registration Endpoint (Optional)
- If client registration via SOAP is required:
    - Create `src/routers/clients.py`.
    - Define a new endpoint (e.g., `/api/v1/clients/register`).
    - Inject `BSEClientRegistrar` dependency.
    - Define request/response schemas in `src/schemas.py`.
    - Call `bse_client_registrar.register_client()`.
    - Handle responses and errors.

## 4. Error Handling Strategy
- The `bse_integration` modules will raise specific exceptions defined in `src/bse_integration/exceptions.py`.
- FastAPI routers will catch these exceptions and map them to appropriate HTTP status codes and error responses.
- Log errors comprehensively, including SOAP request/response details where permissible.

## 5. Database Schema
- Review existing `models.py` (Order, SIPRegistration).
- Ensure fields exist to store relevant BSE data: `bse_order_id`, `bse_sip_reg_id`, `bse_status_code`, `bse_remarks`.
- Add fields if necessary.

## 6. Next Steps
- Implement the `bse_integration` package based on this design.
- Update `requirements.txt`.
- Modify routers to use the new integration modules.
- Perform thorough testing and validation.

