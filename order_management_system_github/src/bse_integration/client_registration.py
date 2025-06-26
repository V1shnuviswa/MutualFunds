"""BSE STAR MF Client Registration Module

This module handles client registration with BSE STAR MF using REST API.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import time

import requests
from requests.exceptions import RequestException

from .config import bse_settings
from .exceptions import (
    BSEIntegrationError, BSEClientRegError, BSETransportError, BSEValidationError,
)
from .fields import CLIENT_REGISTRATION_FIELDS, MINIMUM_REQUIRED_FIELDS

# Configure logging (use WARNING as default in production)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class BSEClientRegistrar:
    """
    Manages client registration with the BSE STAR MF using REST API.
    """

    def __init__(self) -> None:
        """Initialize BSE Client Registration handler."""
        self.user_id = bse_settings.BSE_USER_ID
        self.member_code = bse_settings.BSE_MEMBER_CODE
        self.password = bse_settings.BSE_PASSWORD
        self.url = bse_settings.BSE_UCC_REGISTER_URL or "https://bsestarmfdemo.bseindia.com/BSEMFWEBAPI/UCCAPI/UCCRegistrationV183"
        
        # Validate essential config
        if not self.user_id:
            raise BSEValidationError("BSE User ID is required")
        if not self.password:
            raise BSEValidationError("BSE Password is required")
        if not self.member_code:
            raise BSEValidationError("BSE Member Code is required")
        if not self.url:
            raise BSEValidationError("BSE UCC Registration URL is required")
        
        logger.info(f"Initialized BSE Client Registration handler with URL: {self.url}")

    def _validate_mandatory_fields(self, client_data: Dict[str, Any]) -> None:
        """
        Validate mandatory fields for client registration.
        
        Args:
            client_data: Client registration data
            
        Raises:
            BSEValidationError: If mandatory fields are missing
        """
        mandatory_fields = [
            "ClientCode", "PrimaryHolderFirstName", "TaxStatus", 
            "Gender", "DOB", "OccupationCode", "HoldingNature",
            "PrimaryHolderPANExempt", "ClientType", "AccountType1", 
            "AccountNo1", "IFSCCode1", "DefaultBankFlag1", 
            "DividendPayMode", "Address1", "City", "State", 
            "Pincode", "Country", "Email", "CommunicationMode", 
            "IndianMobile", "PrimaryHolderKYCType", "PaperlessFlag"
        ]
        
        # Conditional mandatory fields based on other field values
        if client_data.get("HoldingNature") in ["JO", "AS"]:
            mandatory_fields.extend(["SecondHolderFirstName", "SecondHolderLastName", "SecondHolderDOB"])
            
        if client_data.get("PrimaryHolderPANExempt") == "N":
            mandatory_fields.append("PrimaryHolderPAN")
            
        if client_data.get("ClientType") == "D":
            mandatory_fields.append("DefaultDP")
            
        if client_data.get("DefaultDP") == "CDSL":
            mandatory_fields.extend(["CDSLDPID", "CDSLCLTID"])
            
        if client_data.get("DefaultDP") == "NSDL":
            mandatory_fields.extend(["NSDLDPID", "NSDLCLTID"])
            
        missing_fields = [field for field in mandatory_fields if not client_data.get(field)]
        if missing_fields:
            raise BSEValidationError(f"Missing mandatory fields: {', '.join(missing_fields)}")

    def _to_param_str(self, client_data: Dict[str, Any]) -> str:
        """
        Convert client data dictionary to pipe-separated string.
        
        Args:
            client_data: Client registration data
            
        Returns:
            Pipe-separated string of client data values
        """
        # The BSE API requires exactly 183 fields in a specific order
        # We'll use the keys from client_data in their original order
        # This assumes the client_data dictionary is properly structured with all 183 fields
        
        # Simply join all values with pipe separator
        param_str = "|".join(str(value).strip() for value in client_data.values())
        logger.debug(f"Generated param string (first 50 chars): {param_str[:50]}...")
        return param_str

    def _construct_payload(self, regn_type: str, client_data: Dict[str, Any],
                         filler1: str = "", filler2: str = "") -> Dict[str, Any]:
        """
        Construct payload for BSE client registration API.
        
        Args:
            regn_type: Registration type (NEW/MOD)
            client_data: Client registration data
            filler1: Optional filler field
            filler2: Optional filler field
            
        Returns:
            Payload dictionary for BSE API
        """
        # Following the exact structure from the example code
        return {
            "UserId": self.user_id,
            "MemberCode": self.member_code,
            "Password": self.password,
            "RegnType": regn_type,
            "Param": self._to_param_str(client_data),
            "Filler1": filler1,
            "Filler2": filler2
        }

    async def register_client(self, client_data: Dict[str, Any],
                        filler1: str = "", filler2: str = "") -> Dict[str, Any]:
        """
        Register a new client with BSE.
        
        Args:
            client_data: Client registration data
            filler1: Optional filler field
            filler2: Optional filler field
            
        Returns:
            BSE API response
            
        Raises:
            BSEIntegrationError: If registration fails
        """
        try:
            # Check if we have the required number of fields
            if len(client_data) != 183:
                logger.warning(f"Client data contains {len(client_data)} fields, but BSE requires exactly 183 fields.")
            
            # Construct payload exactly as in the example
            payload = self._construct_payload("NEW", client_data, filler1, filler2)
            logger.info(f"Registering client with code: {client_data.get('ClientCode')}")
            logger.debug(f"Registration payload: {payload}")
            
            # Send request
            response = await self._post(payload)
            logger.info(f"Registration response: {response}")
            
            return response
        except Exception as e:
            logger.error(f"Client registration failed: {e}", exc_info=True)
            raise BSEIntegrationError(f"Client registration failed: {str(e)}")

    async def update_client(self, client_data: Dict[str, Any],
                      filler1: str = "", filler2: str = "") -> Dict[str, Any]:
        """
        Update an existing client with BSE.
        
        Args:
            client_data: Client registration data
            filler1: Optional filler field
            filler2: Optional filler field
            
        Returns:
            BSE API response
            
        Raises:
            BSEIntegrationError: If update fails
        """
        try:
            # Validate mandatory fields
            self._validate_mandatory_fields(client_data)
            
            # Construct payload
            payload = self._construct_payload("MOD", client_data, filler1, filler2)
            logger.info(f"Updating client with code: {client_data.get('ClientCode')}")
            logger.debug(f"Update payload: {payload}")
            
            # Send request
            response = await self._post(payload)
            logger.info(f"Update response: {response}")
            
            return response
        except Exception as e:
            logger.error(f"Client update failed: {e}", exc_info=True)
            raise BSEIntegrationError(f"Client update failed: {str(e)}")

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send POST request to BSE API.
        
        Args:
            payload: Request payload
            
        Returns:
            BSE API response
            
        Raises:
            BSEIntegrationError: If API call fails
        """
        try:
            headers = {"Content-Type": "application/json"}
            
            # Log the full request details for debugging
            logger.debug(f"Request URL: {self.url}")
            logger.debug(f"Request headers: {headers}")
            logger.debug(f"Request payload: {payload}")
            
            # Use requests in async context
            import asyncio
            response = await asyncio.to_thread(
                requests.post,
                self.url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Log the full response for debugging
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response body: {response.text}")
            
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                json_response = response.json()
                # Log the parsed JSON response
                logger.info(f"Parsed BSE API response: {json_response}")
                return json_response
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response.text}")
                return {"Status": "999", "Remarks": f"Failed to parse response: {str(e)}", "Filler1": "", "Filler2": ""}
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}", exc_info=True)
            raise BSEIntegrationError(f"API request failed: {str(e)}")

    def create_client_code(self, client_data: Dict[str, Any]) -> str:
        """
        Generates a unique ClientCode using: DT<FirstName><LastName><YYYY from DOB>
        
        Args:
            client_data: Client data containing FirstName, LastName, and PrimaryHolderDOB
            
        Returns:
            Generated client code
        """
        first = client_data.get("PrimaryHolderFirstName", "").strip().title()
        last = client_data.get("PrimaryHolderLastName", "").strip().title()
        dob = client_data.get("PrimaryHolderDOB", "").strip()
        try:
            year = datetime.strptime(dob, "%d/%m/%Y").year
        except ValueError:
            year = "0000"
        code = f"DT{first}{last}{year}"
        return code.upper()
