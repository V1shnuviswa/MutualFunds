# BSE Client Registration Module Update Notes

## Summary

The BSE client registration functionality within the Order Management System has been updated based on the reference implementation provided in the GitHub repository: https://github.com/V1shnuviswa/MutualFunds.

The primary change involves switching from a SOAP/WSDL-based approach (using `zeep`) to a direct HTTP POST request method (using `requests`) for client registration and updates, as indicated by the reference code.

## Key Changes

1.  **Switched to `requests.post`**: The `BSEClientRegistrar` class in `src/bse_integration/client_registration.py` now uses the `requests` library to send POST requests directly to the BSE Client Master API endpoint, instead of using the `zeep` library for SOAP calls.
2.  **Configuration Update**: The `src/bse_integration/config.py` file has been updated to include the `BSE_BASE_URL` and `BSE_REGISTRATION_PATH` as defined in the reference repository's `config.py`. The previous `BSE_REGISTRATION_WSDL` is no longer used for this module.
3.  **Field Definitions (`fields.py`)**: A new file, `src/bse_integration/fields.py`, has been created based on the reference repository. This file defines the exact order and names of the 131 fields required for the pipe-separated parameter string (`Param`) in the API payload.
4.  **Payload Construction**: The `_construct_payload` method now builds a JSON payload containing `UserId`, `MemberCode`, `Password`, `RegnType` ("NEW" or "MOD"), and the pipe-separated `Param` string, matching the structure used in the reference code.
5.  **Parameter String Formatting (`_to_param_str`)**: This method now correctly generates the pipe-separated string using the field order defined in `fields.py`.
6.  **Validation**: Basic validation for credentials and required fields (like `ClientCode`) has been implemented. More comprehensive validation based on `MINIMUM_REQUIRED_FIELDS` from `fields.py` can be added if needed.
7.  **Error Handling**: Error handling has been updated to catch `requests.exceptions.RequestException`, `HTTPError`, and `ValueError` (for JSON decoding issues), mapping them to appropriate custom exceptions (`BSETransportError`, `BSEClientRegError`).
8.  **Removed SOAP Logic**: All `zeep`-related imports and logic have been removed from `client_registration.py`.

## Validation

-   Due to the previously identified network restrictions preventing connections to external BSE endpoints from this sandbox environment, end-to-end validation with the live BSE API was not possible.
-   A unit test suite (`test_client_registration.py`) has been created using Python's `unittest` framework and the `unittest.mock` library.
-   These tests mock the `requests.post` call to simulate successful API responses, HTTP errors, network errors, and invalid JSON responses.
-   The tests verify:
    -   Correct payload construction for NEW and MOD registration types.
    -   Successful handling of mocked API success responses.
    -   Correct exception handling for various error scenarios (network, HTTP, invalid JSON).
    -   Input validation logic (missing fields, invalid registration type).

## Next Steps (External Validation)

-   The updated code, particularly `client_registration.py`, needs to be tested in an environment with network access to the BSE STAR MF Demo/Production API endpoint (`https://bsestarmfdemo.bseindia.com/StarMFCommonAPI/ClientMaster/Registration` or production equivalent).
-   Run the unit tests (`python /home/ubuntu/test_client_registration.py`) in the target environment to confirm basic logic.
-   Perform actual client registration and update calls using the API endpoints (e.g., via `curl` or a test script calling the `BSEClientRegistrar` methods) with valid credentials and test data.
-   Analyze the actual JSON responses from the BSE API and update the response parsing logic in `_post` and the calling methods (`register_client`, `update_client`) if necessary. The current implementation assumes a simple JSON structure based on the reference; the actual structure might differ.
-   Refine error handling based on specific error messages or status codes returned by the live API.

## Files Modified/Added

-   `/home/ubuntu/order_management_system/src/bse_integration/client_registration.py` (Modified)
-   `/home/ubuntu/order_management_system/src/bse_integration/config.py` (Modified)
-   `/home/ubuntu/order_management_system/src/bse_integration/fields.py` (Added)
-   `/home/ubuntu/test_client_registration.py` (Added)

