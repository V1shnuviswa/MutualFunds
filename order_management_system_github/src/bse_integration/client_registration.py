# /home/ubuntu/order_management_system/src/bse_integration/client_registration.py

"""BSE STAR MF Client Registration Module

This module handles client registration and updates with BSE STAR MF using REST API.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import requests
from requests.exceptions import RequestException

from .config import bse_settings
from .exceptions import (
    BSEIntegrationError, BSEClientRegError, BSETransportError, BSEValidationError,
    BSESoapFault
)
from .fields import CLIENT_REGISTRATION_FIELDS, MINIMUM_REQUIRED_FIELDS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BSEClientRegistrar:
    """
    Handles client registration and updates with the BSE STAR MF API using REST.
    Supports both new registrations and modifications of existing clients.
    """

    def __init__(self) -> None:
        """Initialize BSE Client Registrar."""
        self.user_id = bse_settings.BSE_USER_ID
        self.member_id = bse_settings.BSE_MEMBER_CODE
        self.password = bse_settings.BSE_PASSWORD
        self.base_url = bse_settings.common_api
        self.endpoint = bse_settings.CLIENT_REGISTRATION

        if not all([self.user_id, self.member_id, self.password]):
            raise BSEValidationError("BSE User ID, Member Code, and Password are required")

        self.url = f"{self.base_url}{self.endpoint}"
        logger.info(f"Initialized BSE Client Registrar")

    def _validate_client_data(self, client_data: Dict[str, Any], is_new: bool = True) -> None:
        """
        Validate client data against BSE requirements.
        
        Args:
            client_data: Dictionary containing client details
            is_new: Whether this is a new registration (True) or modification (False)
        """
        if not isinstance(client_data, dict):
            raise BSEValidationError("Client data must be a dictionary")

        # Check required fields
        required_fields = MINIMUM_REQUIRED_FIELDS if is_new else ["ClientCode"]
        missing_fields = [field for field in required_fields if not client_data.get(field)]
        if missing_fields:
            raise BSEValidationError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate field formats
        self._validate_field_formats(client_data)

    def _validate_field_formats(self, client_data: Dict[str, Any]) -> None:
        """Validate formats of client data fields."""
        # Client Code (max 10 chars)
        if len(str(client_data.get("ClientCode", ""))) > 10:
            raise BSEValidationError("ClientCode must not exceed 10 characters")

        # PAN validation (if provided)
        pan = client_data.get("PrimaryHolderPAN")
        if pan and (len(pan) != 10 or not pan.isalnum()):
            raise BSEValidationError("Invalid PAN format")

        # Mobile number validation (if provided)
        mobile = client_data.get("IndianMobileNo")
        if mobile and (len(str(mobile)) != 10 or not str(mobile).isdigit()):
            raise BSEValidationError("Invalid mobile number format")

        # Email validation (if provided)
        email = client_data.get("Email")
        if email and ("@" not in email or "." not in email):
            raise BSEValidationError("Invalid email format")

        # Date validations
        date_fields = [
            "PrimaryHolderDOB", "SecondHolderDOB", "ThirdHolderDOB",
            "GuardianDOB", "Nominee1DOB", "Nominee2DOB", "Nominee3DOB"
        ]
        for field in date_fields:
            date_str = client_data.get(field)
            if date_str:
                try:
                    datetime.strptime(date_str, "%d/%m/%Y")
                except ValueError:
                    raise BSEValidationError(f"Invalid date format for {field}. Use DD/MM/YYYY")

        # Percentage validations
        percentage_fields = ["Nominee1Percentage", "Nominee2Percentage", "Nominee3Percentage"]
        total_percentage = 0
        for field in percentage_fields:
            value = client_data.get(field)
            if value:
                try:
                    percentage = float(value)
                    if not 0 <= percentage <= 100:
                        raise BSEValidationError(f"{field} must be between 0 and 100")
                    total_percentage += percentage
                except ValueError:
                    raise BSEValidationError(f"Invalid percentage value for {field}")

        if total_percentage > 0 and total_percentage != 100:
            raise BSEValidationError("Total nominee percentage must equal 100")

    def _to_param_str(self, client_data: Dict[str, Any]) -> str:
        """
        Convert client data to BSE's pipe-separated format.
        
        Args:
            client_data: Dictionary containing client details
            
        Returns:
            Pipe-separated string of client data
        """
        try:
            values = []
            for field in CLIENT_REGISTRATION_FIELDS:
                value = client_data.get(field, "")
                # Handle special cases
                if isinstance(value, bool):
                    value = "Y" if value else "N"
                elif isinstance(value, (int, float)):
                    value = str(value)
                elif value is None:
                    value = ""
                values.append(str(value).strip())
            return "|".join(values)
        except Exception as e:
            logger.error(f"Error converting client data to parameter string: {e}")
            raise BSEValidationError(f"Error formatting client data: {str(e)}")

    def _construct_payload(self, regn_type: str, param_str: str, filler1: str = "", filler2: str = "") -> Dict[str, str]:
        """
        Create the API request payload.
        
        Args:
            regn_type: Registration type ("NEW" or "MOD")
            param_str: Pipe-separated client data string
            filler1: Optional filler field 1
            filler2: Optional filler field 2
            
        Returns:
            Dictionary containing the API request payload
        """
        if regn_type not in ["NEW", "MOD"]:
            raise BSEValidationError("Registration type must be either 'NEW' or 'MOD'")
        
        return {
            "UserId": self.user_id,
            "MemberCode": self.member_id,
            "Password": self.password,
            "RegnType": regn_type,
            "Param": param_str,
            "Filler1": filler1,
            "Filler2": filler2
        }

    def _post(self, payload: Dict[str, str]) -> Dict[str, Any]:
        """
        Send POST request to BSE API.
        
        Args:
            payload: API request payload
            
        Returns:
            Dictionary containing the API response
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            logger.debug(f"Sending request to {self.url}")
            response = requests.post(
                self.url,
                json=payload,
                headers=headers,
                timeout=bse_settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            response_data = response.json()
            logger.debug(f"Received response: {response_data}")

            # Check for BSE error responses
            if response_data.get("StatusCode") != bse_settings.SUCCESS_CODE:
                raise BSEClientRegError(
                    f"BSE Error: {response_data.get('Remarks', 'Unknown error')}"
                )

            return response_data

        except RequestException as e:
            logger.error(f"API request failed: {e}", exc_info=True)
            raise BSETransportError(f"API request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}", exc_info=True)
            raise BSEClientRegError(f"Invalid API response format: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise BSEIntegrationError(f"Unexpected error: {str(e)}")

    def register_client(self, client_data: Dict[str, Any], filler1: str = "", filler2: str = "") -> Dict[str, Any]:
        """
        Register a new client with BSE.
        
        Args:
            client_data: Dictionary containing client details
            filler1: Optional filler field 1
            filler2: Optional filler field 2
            
        Returns:
            Dictionary containing the registration response
        """
        logger.info(f"Registering new client with code: {client_data.get('ClientCode')}")
        
        try:
            # Validate client data for new registration
            self._validate_client_data(client_data, is_new=True)
            
            # Convert to BSE format and send request
            param_str = self._to_param_str(client_data)
            payload = self._construct_payload("NEW", param_str, filler1, filler2)
            response = self._post(payload)
            
            logger.info(f"Successfully registered client {client_data.get('ClientCode')}")
            return response

        except Exception as e:
            logger.error(f"Failed to register client {client_data.get('ClientCode')}: {e}", exc_info=True)
            if isinstance(e, BSEIntegrationError):
                raise
            raise BSEClientRegError(f"Failed to register client: {str(e)}")

    def update_client(self, client_data: Dict[str, Any], filler1: str = "", filler2: str = "") -> Dict[str, Any]:
        """
        Update existing client details with BSE.
        
        Args:
            client_data: Dictionary containing client details to update
            filler1: Optional filler field 1
            filler2: Optional filler field 2
            
        Returns:
            Dictionary containing the update response
        """
        logger.info(f"Updating client with code: {client_data.get('ClientCode')}")
        
        try:
            # Validate client data for modification
            self._validate_client_data(client_data, is_new=False)
            
            # Convert to BSE format and send request
            param_str = self._to_param_str(client_data)
            payload = self._construct_payload("MOD", param_str, filler1, filler2)
            response = self._post(payload)
            
            logger.info(f"Successfully updated client {client_data.get('ClientCode')}")
            return response

        except Exception as e:
            logger.error(f"Failed to update client {client_data.get('ClientCode')}: {e}", exc_info=True)
            if isinstance(e, BSEIntegrationError):
                raise
            raise BSEClientRegError(f"Failed to update client: {str(e)}")

    def get_client_details(self, client_code: str) -> Dict[str, Any]:
        """
        Fetch client details from BSE.
        
        Args:
            client_code: Client code to fetch details for
            
        Returns:
            Dictionary containing client details
        """
        logger.info(f"Fetching details for client: {client_code}")
        
        try:
            payload = {
                "UserId": self.user_id,
                "MemberCode": self.member_id,
                "Password": self.password,
                "ClientCode": client_code
            }
            
            response = self._post(payload)
            logger.info(f"Successfully fetched details for client {client_code}")
            return response

        except Exception as e:
            logger.error(f"Failed to fetch client details for {client_code}: {e}", exc_info=True)
            if isinstance(e, BSEIntegrationError):
                raise
            raise BSEClientRegError(f"Failed to fetch client details: {str(e)}")


