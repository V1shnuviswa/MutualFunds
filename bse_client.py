# bse_client.py

from flask import Blueprint, request, jsonify
import logging
import requests
from typing import Dict, List, Optional, Union, Any
from requests.exceptions import RequestException
from config import BASE_URL, REGISTRATION_PATH, BSE_USER_ID, BSE_MEMBER_CODE, BSE_PASSWORD
from .fields import CLIENT_REGISTRATION_FIELDS, MINIMUM_REQUIRED_FIELDS
from models.client_schema import (
    ClientRegistration, Gender, AccountType, CommunicationMode, HoldingNature,
    StateCode, CountryCode, DividendPayMode, OccupationCode, PANExemptCategory
)
from pydantic import ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Blueprint for client registration routes
client_bp = Blueprint('client', __name__)

def format_validation_error(error):
    """Format validation error messages to be more user-friendly"""
    field = error['loc'][0]
    error_type = error['type']
    
    # Handle missing required fields
    if error_type == 'value_error.missing':
        return f"The field '{field}' is mandatory and must be filled"
    
    # Handle invalid data types
    if error_type == 'type_error':
        if error.get('ctx', {}).get('expected_type') == 'string':
            return f"The field '{field}' must be text"
        return f"The field '{field}' has an invalid data type"
    
    # Handle enum validation errors
    if error_type == 'type_error.enum':
        if field == 'Gender':
            valid_values = [e.value for e in Gender]
            return f"Invalid gender. Please select from: {', '.join(valid_values)}"
        elif field == 'AccountType1':
            valid_values = [e.value for e in AccountType]
            return f"Invalid account type. Please select from: {', '.join(valid_values)}"
        elif field == 'CommunicationMode':
            valid_values = [e.value for e in CommunicationMode]
            return f"Invalid communication mode. Please select from: {', '.join(valid_values)}"
        elif field == 'HoldingNature':
            valid_values = [e.value for e in HoldingNature]
            return f"Invalid holding nature. Please select from: {', '.join(valid_values)}"
        elif field == 'State':
            valid_values = [f"{e.value} ({e.name.replace('_', ' ')})" for e in StateCode]
            return f"Invalid state code. Please select from: {', '.join(valid_values)}"
        elif field == 'Country':
            valid_values = [f"{e.value} ({e.name.replace('_', ' ')})" for e in CountryCode]
            return f"Invalid country code. Please select from: {', '.join(valid_values)}"
        elif field == 'DividendPayMode':
            valid_values = [f"{e.value} ({e.name.replace('_', ' ')})" for e in DividendPayMode]
            return f"Invalid dividend pay mode. Please select from: {', '.join(valid_values)}"
        elif field == 'OccupationCode':
            valid_values = [f"{e.value} ({e.name.replace('_', ' ')})" for e in OccupationCode]
            return f"Invalid occupation code. Please select from: {', '.join(valid_values)}"
        elif field.endswith('ExemptCategory'):
            valid_values = [f"{e.value} ({e.name.replace('_', ' ')})" for e in PANExemptCategory]
            return f"Invalid PAN exempt category. Please select from: {', '.join(valid_values)}"
    
    # Handle string length errors
    if error_type == 'value_error.any_str.max_length':
        max_length = error['ctx']['limit_value']
        return f"The field '{field}' cannot be longer than {max_length} characters"
    
    if error_type == 'value_error.any_str.min_length':
        min_length = error['ctx']['limit_value']
        return f"The field '{field}' must be at least {min_length} characters long"
    
    # Handle regex pattern errors
    if error_type == 'value_error.str.regex':
        if 'PAN' in field:
            return f"Invalid PAN format for {field}. PAN should be in format: ABCDE1234F"
        elif field == 'MICRNo1':
            return f"Invalid MICR number. MICR should be 9 digits"
        elif field == 'IFSCCode1':
            return f"Invalid IFSC code. IFSC should be in format: ABCD0123456"
        elif field == 'Pincode':
            return f"Invalid pincode. Pincode should be 6 digits"
        elif field.endswith('Exempt') or field.endswith('Flag'):
            return f"The field '{field}' must be either 'Y' or 'N'"
        elif field == 'TaxStatus':
            return f"Invalid tax status code. Must be a 2-digit number"
    
    # Handle email validation errors
    if error_type == 'value_error.email':
        return f"Invalid email address format"
    
    # Handle date format errors
    if 'DOB' in field and 'Invalid date format' in error.get('msg', ''):
        return f"Invalid date format for {field}. Please use DD/MM/YYYY format"
    
    # Return original error message if no specific formatting is defined
    return error.get('msg', f"Invalid value for field '{field}'")

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
        """Convert client data dictionary to pipe-separated string."""
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
        """Create the API request payload."""
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

    def register_client(
        self,
        client_data: Dict[str, Any],
        fields: List[str] = CLIENT_REGISTRATION_FIELDS,
        filler1: Optional[str] = "",
        filler2: Optional[str] = ""
    ) -> Dict[str, Any]:
        """Register a new client with BSE."""
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
        fields: List[str] = CLIENT_REGISTRATION_FIELDS,
        filler1: Optional[str] = "",
        filler2: Optional[str] = ""
    ) -> Dict[str, Any]:
        """Update existing client details with BSE."""
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
        """Send POST request to BSE API."""
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

# Route handlers
@client_bp.route('/register', methods=['POST'])
def register_client():
    """Register a new client with parameter validation using Pydantic."""
    try:
        # Get client registration data from request
        client_data = request.get_json()
        if not client_data:
            return jsonify({
                'status': 'error',
                'message': 'No client data provided',
                'details': 'Please provide client registration data'
            }), 400

        # Validate data using Pydantic model
        try:
            validated_data = ClientRegistration(**client_data)
        except ValidationError as e:
            formatted_errors = [
                {
                    'field': error['loc'][0],
                    'error': format_validation_error(error)
                }
                for error in e.errors()
            ]
            
            return jsonify({
                'status': 'error',
                'message': 'Validation failed',
                'errors': formatted_errors,
                'details': 'Please correct the following errors and try again'
            }), 400

        # Initialize BSE client registration service
        bse_client = BSEClientRegistration()
        
        # Register client with BSE using validated data
        response = bse_client.register_client(validated_data.dict(exclude_none=True))
        
        # Log successful registration
        logger.info(f"Successfully registered client with code: {validated_data.ClientCode}")
        
        return jsonify({
            'status': 'success',
            'message': 'Client registered successfully',
            'data': response
        }), 201

    except Exception as e:
        logger.error(f"Error registering client: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'details': 'An unexpected error occurred. Please try again later.'
        }), 500

@client_bp.route('/validate', methods=['POST'])
def validate_registration_data():
    """Validate client registration data without submitting to BSE."""
    try:
        # Get client registration data from request
        client_data = request.get_json()
        if not client_data:
            return jsonify({
                'status': 'error',
                'message': 'No client data provided',
                'details': 'Please provide client registration data'
            }), 400

        # Validate data using Pydantic model
        try:
            validated_data = ClientRegistration(**client_data)
            return jsonify({
                'status': 'success',
                'message': 'All parameters are valid',
                'data': validated_data.dict(exclude_none=True)
            }), 200
        except ValidationError as e:
            formatted_errors = [
                {
                    'field': error['loc'][0],
                    'error': format_validation_error(error)
                }
                for error in e.errors()
            ]
            
            return jsonify({
                'status': 'error',
                'message': 'Validation failed',
                'errors': formatted_errors,
                'details': 'Please correct the following errors and try again'
            }), 400

    except Exception as e:
        logger.error(f"Error validating client data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'details': 'An unexpected error occurred. Please try again later.'
        }), 500
