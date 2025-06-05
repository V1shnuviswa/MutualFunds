"""BSE STAR MF Price Discovery Module

This module handles NAV price discovery and other price-related operations through BSE STAR MF.
"""

import asyncio
import logging
from datetime import date, datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from requests.exceptions import RequestException
from requests import Session

from .config import bse_settings
from .exceptions import (
    BSEIntegrationError,
    BSEAuthError,
    BSEValidationError,
    BSESoapFault,
    BSETransportError
)
from .. import schemas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BSEPriceDiscovery:
    """Handles NAV price discovery and other price-related operations through BSE STAR MF."""
    
    def __init__(self) -> None:
        """Initialize the BSE Price Discovery service."""
        self.wsdl_url = bse_settings.web_service_wsdl
        self.user_id = bse_settings.BSE_USER_ID
        self.member_id = bse_settings.BSE_MEMBER_CODE

        if not self.wsdl_url:
            raise BSEIntegrationError("BSE_WEB_SERVICE_WSDL is not configured.")
        if not self.user_id or not self.member_id:
            raise BSEIntegrationError("BSE User ID or Member ID not configured.")

        try:
            session = Session()
            transport = Transport(session=session, timeout=bse_settings.REQUEST_TIMEOUT)
            self.client = Client(wsdl_url=self.wsdl_url, transport=transport)
            logger.info("BSE Price Discovery service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BSE Price Discovery service: {e}", exc_info=True)
            raise BSEIntegrationError(f"Failed to initialize BSE Price Discovery service: {str(e)}")

    async def get_nav(self, nav_request: schemas.NAVRequest, encrypted_password: str) -> schemas.NAVResponse:
        """
        Fetches NAV for a given scheme code.
        
        Args:
            nav_request: NAVRequest object containing scheme details
            encrypted_password: Encrypted password for BSE authentication
            
        Returns:
            NAVResponse object containing NAV details
        """
        if not encrypted_password:
            raise BSEValidationError("Encrypted password is required for NAV discovery")

        params = {
            "Flag": "N",  # N for normal request, H for historical
            "UserId": self.user_id,
            "MemberId": self.member_id,
            "Password": encrypted_password,
            "FromDate": nav_request.date.strftime("%d/%m/%Y") if nav_request.date else "",
            "ToDate": nav_request.date.strftime("%d/%m/%Y") if nav_request.date else "",
            "SchemeCode": nav_request.scheme_code,
            "ClientCode": nav_request.client_code or ""
        }

        logger.info(f"Fetching NAV for scheme: {nav_request.scheme_code}")
        return await self._send_soap_request("getLatestNAV", params)

    async def get_historical_nav(
        self, 
        scheme_code: str, 
        from_date: date,
        to_date: date,
        encrypted_password: str
    ) -> List[schemas.NAVResponse]:
        """
        Fetches historical NAV for a given scheme code and date range.
        
        Args:
            scheme_code: BSE scheme code
            from_date: Start date for historical NAV
            to_date: End date for historical NAV
            encrypted_password: Encrypted password for BSE authentication
            
        Returns:
            List of NAVResponse objects containing historical NAV details
        """
        if not encrypted_password:
            raise BSEValidationError("Encrypted password is required for NAV discovery")

        params = {
            "Flag": "H",  # H for historical NAV
            "UserId": self.user_id,
            "MemberId": self.member_id,
            "Password": encrypted_password,
            "FromDate": from_date.strftime("%d/%m/%Y"),
            "ToDate": to_date.strftime("%d/%m/%Y"),
            "SchemeCode": scheme_code,
            "ClientCode": ""  # Optional for historical NAV
        }

        logger.info(f"Fetching historical NAV for scheme: {scheme_code}")
        return await self._send_soap_request("getHistoricalNAV", params)

    async def get_scheme_master(self, encrypted_password: str) -> List[Dict[str, Any]]:
        """
        Fetches the complete scheme master from BSE.
        
        Args:
            encrypted_password: Encrypted password for BSE authentication
            
        Returns:
            List of dictionaries containing scheme details
        """
        if not encrypted_password:
            raise BSEValidationError("Encrypted password is required for scheme master")

        params = {
            "UserId": self.user_id,
            "MemberId": self.member_id,
            "Password": encrypted_password,
            "ClientCode": ""  # Optional for scheme master
        }

        logger.info("Fetching scheme master")
        return await self._send_soap_request("getMFSchemeMaster", params)

    async def _send_soap_request(self, soap_method: str, params: Dict[str, Any]) -> Any:
        """Send SOAP request to BSE and parse response"""
        try:
            if not hasattr(self.client.service, soap_method):
                raise BSEIntegrationError(f"SOAP method {soap_method} not found")

            def soap_call():
                return getattr(self.client.service, soap_method)(**params)

            response = await asyncio.to_thread(soap_call)
            logger.debug(f"BSE Response: {response}")
            
            return self._parse_response(str(response), soap_method)

        except Fault as e:
            logger.error(f"SOAP fault: {e}", exc_info=True)
            raise BSESoapFault(f"SOAP fault: {str(e)}")
        except TransportError as e:
            logger.error(f"Transport error: {e}", exc_info=True)
            raise BSETransportError(f"Transport error: {str(e)}")
        except RequestException as e:
            logger.error(f"Network error: {e}", exc_info=True)
            raise BSETransportError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise BSEIntegrationError(f"Unexpected error: {str(e)}")

    def _parse_response(self, response_str: str, method: str) -> Any:
        """
        Parses BSE response string into appropriate format based on method.
        
        Args:
            response_str: Raw response string from BSE SOAP API
            method: SOAP method name to determine parsing logic
            
        Returns:
            Parsed response in appropriate format
        """
        try:
            parts = [part.strip() for part in response_str.split("|")]
            
            if len(parts) < 3:
                raise BSEIntegrationError(f"Invalid response format: {response_str}")

            status_code = parts[0]
            message = parts[1]

            if status_code != bse_settings.SUCCESS_CODE:
                raise BSEIntegrationError(f"BSE Error: {message}")

            if method == "getLatestNAV":
                return schemas.NAVResponse(
                    scheme_code=parts[2],
                    scheme_name=parts[5],
                    nav=Decimal(parts[3]) if parts[3] else Decimal("0"),
                    nav_date=datetime.strptime(parts[4], "%d/%m/%Y").date() if parts[4] else date.today(),
                    status=message,
                    status_code=status_code,
                    message=None if status_code == bse_settings.SUCCESS_CODE else message
                )
            
            elif method == "getHistoricalNAV":
                nav_list = []
                # Process multiple NAV records
                for i in range(2, len(parts), 4):
                    if i + 3 < len(parts):
                        nav_list.append(schemas.NAVResponse(
                            scheme_code=parts[i],
                            scheme_name=parts[i+3],
                            nav=Decimal(parts[i+1]) if parts[i+1] else Decimal("0"),
                            nav_date=datetime.strptime(parts[i+2], "%d/%m/%Y").date() if parts[i+2] else date.today(),
                            status=message,
                            status_code=status_code,
                            message=None
                        ))
                return nav_list
            
            elif method == "getMFSchemeMaster":
                scheme_list = []
                # Process scheme master records
                for i in range(2, len(parts), 6):
                    if i + 5 < len(parts):
                        scheme_list.append({
                            "scheme_code": parts[i],
                            "rta_scheme_code": parts[i+1],
                            "scheme_name": parts[i+2],
                            "amc_code": parts[i+3],
                            "scheme_type": parts[i+4],
                            "scheme_plan": parts[i+5]
                        })
                return scheme_list
            
            else:
                raise BSEIntegrationError(f"Unknown method: {method}")

        except Exception as e:
            logger.error(f"Error parsing response: {e}", exc_info=True)
            raise BSEIntegrationError(f"Failed to parse response: {str(e)}") 