# /home/ubuntu/order_management_system/src/bse_integration/client_registration.py

import logging
from typing import Dict, Any, List, Optional

import requests
from requests.exceptions import RequestException

from .config import bse_settings
from .exceptions import (
    BSEIntegrationError, BSEClientRegError, BSETransportError, BSEValidationError
)
from .fields import CLIENT_REGISTRATION_FIELDS # Import the fields

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class BSEClientRegistrar:
    """
    Handles client registration and updates with the BSE STAR MF API using direct POST requests.
    Based on the reference implementation: https://github.com/V1shnuviswa/MutualFunds/blob/main/bse_client.py
    """

    def __init__(self) -> None:
        """
        Initialize BSE Client Registrar.
        """
        self.user_id = bse_settings.BSE_USER_ID
        self.member_id = bse_settings.BSE_MEMBER_CODE
        self.password = bse_settings.BSE_PASSWORD
        self.base_url = bse_settings.BSE_BASE_URL
        self.endpoint_path = bse_settings.BSE_REGISTRATION_PATH

        self._validate_credentials(self.user_id, self.member_id, self.password)
        self.url = self._build_url(self.base_url, self.endpoint_path)
        logger.info(f"Initialized BSEClientRegistrar for endpoint: {self.url}")

    @staticmethod
    def _validate_credentials(user_id: str, member_code: str, password: str) -> None:
        """Validate BSE credentials."""
        if not all([user_id, member_code, password]):
            raise BSEValidationError("BSE User ID, Member Code, and Password are required")
        if not isinstance(user_id, str) or not isinstance(member_code, str) or not isinstance(password, str):
            raise BSEValidationError("Credentials must be strings")

    @staticmethod
    def _build_url(base_url: str, endpoint_path: str) -> str:
        """Build the complete API URL."""
        return base_url.rstrip("/") + endpoint_path

    def _validate_client_data(self, client_data: Dict[str, Any], fields: List[str]) -> None:
        """Validate client data against required fields."""
        if not isinstance(client_data, dict):
            raise BSEValidationError("Client data must be a dictionary")
        # Basic check for ClientCode, add more checks based on MINIMUM_REQUIRED_FIELDS if needed
        required_fields = ["ClientCode"] 
        missing_fields = [field for field in required_fields if not client_data.get(field)]
        if missing_fields:
            raise BSEValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def _to_param_str(self, client_data: Dict[str, Any], fields: List[str]) -> str:
        """
        Convert client data dictionary to pipe-separated string based on specified fields.
        """
        try:
            # Ensure all fields from the list are present, defaulting to empty string if missing in client_data
            return "|".join(str(client_data.get(field, "")).strip() for field in fields)
        except Exception as e:
            logger.error(f"Error converting client data to parameter string: {e}")
            raise BSEValidationError(f"Error formatting client data: {str(e)}")

    def _construct_payload(self, regn_type: str, param_str: str, filler1: Optional[str] = "", filler2: Optional[str] = "") -> Dict[str, str]:
        """
        Create the API request payload with registration details and credentials.
        """
        if regn_type not in ["NEW", "MOD"]:
            raise BSEValidationError("Registration type must be either 'NEW' or 'MOD'")
        
        return {
            "UserId": self.user_id,
            "MemberCode": self.member_id,
            "Password": self.password,
            "RegnType": regn_type,
            "Param": param_str,
            "Filler1": filler1 or "",
            "Filler2": filler2 or ""
        }

    def _post(self, payload: Dict[str, str]) -> Dict[str, Any]:
        """Send POST request to BSE API and return response as dictionary."""
        headers = {"Content-Type": "application/json"}
        try:
            logger.debug(f"Sending POST request to {self.url} with payload: {payload}")
            response = requests.post(self.url, json=payload, headers=headers, timeout=30)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            # Assuming the response is JSON as per reference _post method
            response_json = response.json()
            logger.debug(f"Received response: {response_json}")
            return response_json
            
        except RequestException as e:
            logger.error(f"API request failed: {e}", exc_info=True)
            raise BSETransportError(f"API request failed: {str(e)}")
        except ValueError as e: # Catches JSON decoding errors
            logger.error(f"Invalid JSON response: {e}", exc_info=True)
            raise BSEClientRegError(f"Invalid API response format: {str(e)}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during POST request: {e}", exc_info=True)
            raise BSEIntegrationError(f"Unexpected error during POST: {str(e)}")

    def register_client(self, client_data: Dict[str, Any], filler1: Optional[str] = "", filler2: Optional[str] = "") -> Dict[str, Any]:
        """
        Register a new client with BSE.
        """
        logger.info(f"Registering new client with code: {client_data.get('ClientCode')}")
        self._validate_client_data(client_data, CLIENT_REGISTRATION_FIELDS)
        
        try:
            param_str = self._to_param_str(client_data, CLIENT_REGISTRATION_FIELDS)
            payload = self._construct_payload("NEW", param_str, filler1, filler2)
            response = self._post(payload)
            # TODO: Add specific parsing/validation of the response JSON based on actual API docs
            # Example: Check response['Status'] or similar
            logger.info(f"Client registration API call successful for {client_data.get('ClientCode')}")
            return response
        except Exception as e:
            logger.error(f"Failed to register client {client_data.get('ClientCode')}: {e}", exc_info=True)
            # Re-raise specific exceptions if they are already BSEIntegrationError types
            if isinstance(e, BSEIntegrationError):
                raise
            raise BSEClientRegError(f"Failed to register client: {str(e)}")

    def update_client(self, client_data: Dict[str, Any], filler1: Optional[str] = "", filler2: Optional[str] = "") -> Dict[str, Any]:
        """
        Update existing client details with BSE.
        """
        logger.info(f"Updating client with code: {client_data.get('ClientCode')}")
        self._validate_client_data(client_data, CLIENT_REGISTRATION_FIELDS)
        
        try:
            param_str = self._to_param_str(client_data, CLIENT_REGISTRATION_FIELDS)
            payload = self._construct_payload("MOD", param_str, filler1, filler2)
            response = self._post(payload)
            # TODO: Add specific parsing/validation of the response JSON based on actual API docs
            logger.info(f"Client update API call successful for {client_data.get('ClientCode')}")
            return response
        except Exception as e:
            logger.error(f"Failed to update client {client_data.get('ClientCode')}: {e}", exc_info=True)
            if isinstance(e, BSEIntegrationError):
                raise
            raise BSEClientRegError(f"Failed to update client: {str(e)}")


