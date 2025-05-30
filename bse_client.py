# bse_client.py

import logging
import requests
from typing import Dict, List, Optional, Union, Any
from requests.exceptions import RequestException
from config import BASE_URL, REGISTRATION_PATH, BSE_USER_ID, BSE_MEMBER_CODE, BSE_PASSWORD
from fields import CLIENT_REGISTRATION_FIELDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BSEError(Exception):
    """Base exception class for BSE-related errors."""
    pass

class BSEAPIError(BSEError):
    """Exception raised for BSE API errors."""
    pass

class BSEValidationError(BSEError):
    """Exception raised for validation errors."""
    pass

class BSEClientRegistration:
    """
    A class to handle client registration and updates with the BSE (Bombay Stock Exchange) API.
    
    This class provides methods to:
    1. Register new clients
    2. Update existing client details 
    3. Convert form data into the required BSE API format
    
    Attributes:
        user_id (str): BSE user ID for authentication
        member_code (str): BSE member code for authentication
        password (str): BSE password for authentication
        url (str): Complete API endpoint URL
        
    Example:
        >>> client = BSEClientRegistration()
        >>> response = client.register_client({
        ...     "ClientCode": "CLIENT001",
        ...     "FirstName": "John",
        ...     "LastName": "Doe"
        ... }, CLIENT_REGISTRATION_FIELDS)
    """

    def __init__(
        self,
        user_id: str = BSE_USER_ID,
        member_code: str = BSE_MEMBER_CODE,
        password: str = BSE_PASSWORD,
        base_url: str = BASE_URL,
        endpoint_path: str = REGISTRATION_PATH
    ) -> None:
        """Initialize with BSE credentials and API endpoint details."""
        self._validate_credentials(user_id, member_code, password)
        self.user_id = user_id
        self.member_code = member_code
        self.password = password
        self.url = self._build_url(base_url, endpoint_path)
        logger.info(f"Initialized BSEClientRegistration with member code: {member_code}")

    @staticmethod
    def _validate_credentials(user_id: str, member_code: str, password: str) -> None:
        """Validate BSE credentials."""
        if not all([user_id, member_code, password]):
            raise BSEValidationError("All credentials (user_id, member_code, password) are required")
        if not isinstance(user_id, str) or not isinstance(member_code, str) or not isinstance(password, str):
            raise BSEValidationError("Credentials must be strings")

    @staticmethod
    def _build_url(base_url: str, endpoint_path: str) -> str:
        """Build the complete API URL."""
        return f"{base_url.rstrip('/')}{endpoint_path}"

    def _validate_client_data(self, client_data: Dict[str, Any], fields: List[str]) -> None:
        """Validate client data against required fields."""
        if not isinstance(client_data, dict):
            raise BSEValidationError("Client data must be a dictionary")
        
        required_fields = ["ClientCode"]  # Add other required fields as needed
        missing_fields = [field for field in required_fields if not client_data.get(field)]
        
        if missing_fields:
            raise BSEValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def _to_param_str(self, client_data: Dict[str, Any], fields: List[str]) -> str:
        """
        Convert client data dictionary to pipe-separated string based on specified fields.
        
        Args:
            client_data: Dictionary containing client details
            fields: List of field names in required order
            
        Returns:
            Pipe-separated string of client data values
        """
        try:
            return "|".join(str(client_data.get(field, "")).strip() for field in fields)
        except Exception as e:
            logger.error(f"Error converting client data to parameter string: {e}")
            raise BSEValidationError(f"Error formatting client data: {str(e)}")

    def _construct_payload(
        self,
        regn_type: str,
        param_str: str,
        filler1: Optional[str] = "",
        filler2: Optional[str] = ""
    ) -> Dict[str, str]:
        """
        Create the API request payload with registration details and credentials.
        
        Args:
            regn_type: Registration type ("NEW" or "MOD")
            param_str: Pipe-separated client details
            filler1: Optional additional data
            filler2: Optional additional data
            
        Returns:
            Dictionary containing the API request payload
        """
        if regn_type not in ["NEW", "MOD"]:
            raise BSEValidationError("Registration type must be either 'NEW' or 'MOD'")

        return {
            "UserId": self.user_id,
            "MemberCode": self.member_code,
            "Password": self.password,
            "RegnType": regn_type,
            "Param": param_str,
            "Filler1": filler1,
            "Filler2": filler2
        }

    @staticmethod
    def build_param_from_ui(form_data: Dict[str, Any]) -> str:
        """
        Convert UI form data to BSE API format.
        
        Args:
            form_data: Dictionary containing client details from UI form
            
        Returns:
            String with values separated by pipes (|) in BSE-specified order
            
        Raises:
            BSEValidationError: If form data is invalid
        """
        if not isinstance(form_data, dict):
            raise BSEValidationError("Form data must be a dictionary")
            
        try:
            return "|".join(str(form_data.get(field, "")).strip() for field in CLIENT_REGISTRATION_FIELDS)
        except Exception as e:
            logger.error(f"Error processing UI form data: {e}")
            raise BSEValidationError(f"Error processing form data: {str(e)}")

    def register_client(
        self,
        client_data: Dict[str, Any],
        fields: List[str],
        filler1: Optional[str] = "",
        filler2: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Register a new client with BSE.
        
        Args:
            client_data: Dictionary with client details
            fields: List of field names in required order
            filler1: Optional additional data
            filler2: Optional additional data
            
        Returns:
            API response as dictionary
            
        Raises:
            BSEValidationError: If client data is invalid
            BSEAPIError: If API request fails
        """
        logger.info(f"Registering new client with code: {client_data.get('ClientCode')}")
        self._validate_client_data(client_data, fields)
        
        try:
            param_str = self._to_param_str(client_data, fields)
            payload = self._construct_payload("NEW", param_str, filler1, filler2)
            return self._post(payload)
        except Exception as e:
            logger.error(f"Error registering client: {e}")
            raise BSEAPIError(f"Failed to register client: {str(e)}")

    def update_client(
        self,
        client_data: Dict[str, Any],
        fields: List[str],
        filler1: Optional[str] = "",
        filler2: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Update existing client details with BSE.
        
        Args:
            client_data: Dictionary with updated client details
            fields: List of field names in required order
            filler1: Optional additional data
            filler2: Optional additional data
            
        Returns:
            API response as dictionary
            
        Raises:
            BSEValidationError: If client data is invalid
            BSEAPIError: If API request fails
        """
        logger.info(f"Updating client with code: {client_data.get('ClientCode')}")
        self._validate_client_data(client_data, fields)
        
        try:
            param_str = self._to_param_str(client_data, fields)
            payload = self._construct_payload("MOD", param_str, filler1, filler2)
            return self._post(payload)
        except Exception as e:
            logger.error(f"Error updating client: {e}")
            raise BSEAPIError(f"Failed to update client: {str(e)}")

    def _post(self, payload: Dict[str, str]) -> Dict[str, Any]:
        """
        Send POST request to BSE API and return response as dictionary.
        
        Args:
            payload: Request payload
            
        Returns:
            API response as dictionary
            
        Raises:
            BSEAPIError: If request fails or response is invalid
        """
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"API request failed: {e}")
            raise BSEAPIError(f"API request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise BSEAPIError(f"Invalid API response: {str(e)}")

client = BSEClientRegistration()
