# /home/ubuntu/test_client_registration.py

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import requests

# Import mock config
from tests.test_config import mock_bse_settings

# Mock the bse_settings import
sys.modules['src.bse_integration.config'] = MagicMock()
sys.modules['src.bse_integration.config'].bse_settings = mock_bse_settings

# Now import the modules
from src.bse_integration.client_registration import BSEClientRegistrar
from src.bse_integration.exceptions import BSEClientRegError, BSETransportError, BSEValidationError
from src.bse_integration.fields import CLIENT_REGISTRATION_FIELDS

# Sample valid client data for testing
SAMPLE_CLIENT_DATA = {
    "ClientCode": "TEST001",
    "PrimaryHolderFirstName": "Test",
    "PrimaryHolderLastName": "User",
    "TaxStatus": "01", # Resident Individual
    "Gender": "M",
    "PrimaryHolderDOB": "01/01/1990",
    "OccupationCode": "01", # Business
    "HoldingNature": "SI", # Single
    "DividendPayMode": "01", # Credit To Bank
    "PrimaryHolderPANExempt": "N",
    "PrimaryHolderPAN": "ABCDE1234F",
    "AccountType1": "SB", # Savings Bank
    "AccountNo1": "1234567890",
    "MICRNo1": "",
    "IFSCCode1": "ABCD0123456",
    "DefaultBankFlag1": "Y",
    "Address1": "123 Test Street",
    "City": "TestCity",
    "State": "27", # Maharashtra
    "Pincode": "400001",
    "Country": "IND",
    "Email": "test.user@example.com",
    "CommunicationMode": "EMAIL",
    "IndianMobileNo": "9876543210",
    "MobileDeclarationFlag": "Y",
    "EmailDeclarationFlag": "Y",
    # Add other fields from CLIENT_REGISTRATION_FIELDS with default/empty values if needed
}
# Ensure all fields are present for param string generation
for field in CLIENT_REGISTRATION_FIELDS:
    if field not in SAMPLE_CLIENT_DATA:
        SAMPLE_CLIENT_DATA[field] = ""

class TestBSEClientRegistrar(unittest.TestCase):

    def setUp(self):
        """Set up the BSEClientRegistrar instance for each test."""
        # Mock settings if needed, but defaults should work if config is present
        self.registrar = BSEClientRegistrar()

    @patch("src.bse_integration.client_registration.requests.post")
    def test_register_client_success(self, mock_post):
        """Test successful client registration."""
        # Configure mock response for success
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Assume a simple success JSON response format (adjust based on actual API)
        mock_response.json.return_value = {"Status": "1", "Message": "Success", "ClientCode": "TEST001"}
        mock_post.return_value = mock_response

        response = self.registrar.register_client(SAMPLE_CLIENT_DATA)

        self.assertIsNotNone(response)
        self.assertEqual(response["Status"], "1")
        self.assertEqual(response["Message"], "Success")
        mock_post.assert_called_once()
        # Check payload details if necessary
        call_args, call_kwargs = mock_post.call_args
        self.assertEqual(call_kwargs["json"]["RegnType"], "NEW")
        self.assertIn("TEST001", call_kwargs["json"]["Param"])

    @patch("src.bse_integration.client_registration.requests.post")
    def test_update_client_success(self, mock_post):
        """Test successful client update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Status": "1", "Message": "Client details updated successfully", "ClientCode": "TEST001"}
        mock_post.return_value = mock_response

        response = self.registrar.update_client(SAMPLE_CLIENT_DATA)

        self.assertIsNotNone(response)
        self.assertEqual(response["Status"], "1")
        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        self.assertEqual(call_kwargs["json"]["RegnType"], "MOD")
        self.assertIn("TEST001", call_kwargs["json"]["Param"])

    @patch("src.bse_integration.client_registration.requests.post")
    def test_api_error_http_exception(self, mock_post):
        """Test handling of API returning an HTTP error status."""
        mock_response = MagicMock()
        mock_response.status_code = 500 # Internal Server Error
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        mock_post.return_value = mock_response

        with self.assertRaises(BSETransportError):
            self.registrar.register_client(SAMPLE_CLIENT_DATA)
        mock_post.assert_called_once()

    @patch("src.bse_integration.client_registration.requests.post")
    def test_invalid_json_response(self, mock_post):
        """Test handling of API returning non-JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Decoding JSON has failed") # Simulate JSON decode error
        mock_post.return_value = mock_response

        with self.assertRaises(BSEClientRegError) as cm:
            self.registrar.register_client(SAMPLE_CLIENT_DATA)
        self.assertIn("Invalid API response format", str(cm.exception))
        mock_post.assert_called_once()

    @patch("src.bse_integration.client_registration.requests.post")
    def test_network_error(self, mock_post):
        """Test handling of network errors during API call."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection timed out")

        with self.assertRaises(BSETransportError):
            self.registrar.register_client(SAMPLE_CLIENT_DATA)
        mock_post.assert_called_once()

    def test_validation_error_missing_field(self):
        """Test validation error for missing required fields."""
        invalid_data = SAMPLE_CLIENT_DATA.copy()
        del invalid_data["ClientCode"] # Remove a required field

        with self.assertRaises(BSEValidationError) as cm:
            self.registrar.register_client(invalid_data)
        self.assertIn("Missing required fields: ClientCode", str(cm.exception))

    def test_validation_error_invalid_regn_type(self):
        """Test validation error for invalid registration type."""
        with self.assertRaises(BSEValidationError) as cm:
            # Call internal method directly for this specific validation
            self.registrar._construct_payload("INVALID", "param_str")
        self.assertIn("Registration type must be either 'NEW' or 'MOD'", str(cm.exception))

if __name__ == "__main__":
    # Run tests from the project root directory
    # Example: python /home/ubuntu/test_client_registration.py
    unittest.main()

