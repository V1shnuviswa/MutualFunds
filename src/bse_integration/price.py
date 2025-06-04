from datetime import date, datetime
from typing import Dict, Any, Optional
from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from requests.exceptions import RequestException
import logging
from ..schemas import NAVRequest
from .exceptions import (
    BSEIntegrationError,
    BSEAuthError,
    BSEValidationError,
    BSESoapFault,
    BSETransportError
)

logger = logging.getLogger(__name__)

class BSEPriceDiscovery:
    """Handles NAV price discovery for mutual fund schemes through BSE STAR MF."""
    
    def __init__(self, wsdl_url: Optional[str] = None):
        """Initialize the BSE Price Discovery service."""
        self.wsdl_url = wsdl_url or "https://www.bsestarmf.in/StarMFWebService/StarMFWebService.svc?wsdl"
        try:
            transport = Transport(timeout=30)  # 30 seconds timeout
            self.client = Client(wsdl_url=self.wsdl_url, transport=transport)
            logger.info("BSE Price Discovery service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BSE Price Discovery service: {e}", exc_info=True)
            raise BSEIntegrationError(f"Failed to initialize BSE Price Discovery service: {str(e)}")

    async def get_nav(self, nav_request: NAVRequest, encrypted_password: str) -> Dict[str, Any]:
        """
        Fetches NAV for a given scheme code.
        
        Args:
            nav_request: NAVRequest object containing scheme details
            encrypted_password: Encrypted password for BSE authentication
            
        Returns:
            Dict containing NAV details including:
            - nav: Current NAV
            - nav_date: Date of NAV
            - scheme_name: Name of the scheme
        """
        if not encrypted_password:
            raise BSEValidationError("Encrypted password is required for NAV discovery")

        soap_method_name = "getLatestNAV"  # Replace with actual BSE SOAP method name

        request_payload = {
            "Flag": "N",  # Assuming N for normal request
            "UserId": nav_request.user_id,
            "Password": encrypted_password,
            "SchemeCode": nav_request.scheme_code,
            "Date": nav_request.date.strftime("%d/%m/%Y") if nav_request.date else datetime.now().strftime("%d/%m/%Y")
        }

        logger.info(f"Attempting to fetch NAV for scheme: {nav_request.scheme_code}")
        logger.debug(f"NAV request payload: {request_payload}")

        try:
            if not hasattr(self.client.service, soap_method_name):
                raise BSEIntegrationError(f"SOAP method {soap_method_name} not found in WSDL {self.wsdl_url}")

            # Run the blocking SOAP call in a separate thread
            def soap_call():
                return self.client.service[soap_method_name](**request_payload)

            response = await asyncio.to_thread(soap_call)
            logger.debug(f"Raw BSE NAV response: {response}")

            # Parse the response
            parsed_response = self._parse_nav_response(str(response))
            
            if not parsed_response["success"]:
                logger.warning(f"BSE NAV fetch failed: {parsed_response['message']}")
                raise BSEIntegrationError(f"BSE NAV fetch failed: {parsed_response['message']}")

            logger.info(f"Successfully fetched NAV for scheme: {nav_request.scheme_code}")
            return parsed_response

        except Fault as e:
            logger.error(f"SOAP fault during NAV fetch: {e}", exc_info=True)
            raise BSESoapFault(f"SOAP fault during NAV fetch: {str(e)}")
        except TransportError as e:
            logger.error(f"Transport error during NAV fetch: {e}", exc_info=True)
            raise BSETransportError(f"Transport error during NAV fetch: {str(e)}")
        except RequestException as e:
            logger.error(f"Network error during NAV fetch: {e}", exc_info=True)
            raise BSETransportError(f"Network error during NAV fetch: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during NAV fetch: {e}", exc_info=True)
            raise BSEIntegrationError(f"Unexpected error during NAV fetch: {str(e)}")

    def _parse_nav_response(self, response_str: str) -> Dict[str, Any]:
        """
        Parses the BSE NAV response string into a structured format.
        
        Args:
            response_str: Raw response string from BSE SOAP API
            
        Returns:
            Dict containing parsed NAV information
        """
        try:
            # Example response format (adjust based on actual BSE response):
            # "100|Success|SchemeCode|NAV|NAVDate|SchemeName"
            parts = response_str.split("|")
            
            if len(parts) < 6:
                return {
                    "success": False,
                    "message": "Invalid response format from BSE"
                }

            status_code, message, scheme_code, nav, nav_date, scheme_name = parts[:6]
            
            return {
                "success": status_code == "100",
                "status_code": status_code,
                "message": message,
                "scheme_code": scheme_code,
                "nav": float(nav) if nav else None,
                "nav_date": datetime.strptime(nav_date, "%d/%m/%Y").date() if nav_date else None,
                "scheme_name": scheme_name
            }
        except Exception as e:
            logger.error(f"Error parsing NAV response: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to parse NAV response: {str(e)}"
            } 