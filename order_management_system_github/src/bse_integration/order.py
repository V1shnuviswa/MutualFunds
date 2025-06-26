#/home/ubuntu/order_management_system/src/bse_integration/order.py

"""
BSE STAR MF Order Management System

This module handles all types of orders with BSE STAR MF using SOAP.
Supports: Lumpsum, SIP, XSIP, Switch, Spread orders with all operations.
"""
"""
BSE STAR MF Order Management System

This module handles all types of orders with BSE STAR MF using SOAP.
Supports: Lumpsum, SIP, XSIP, Switch, Spread orders with all operations.
"""
import os
import json
import logging
import asyncio
import xml.etree.ElementTree as ET
from time import time
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from requests import Session, RequestException
from zeep import Client, Transport, Settings
from zeep.cache import SqliteCache
from zeep.exceptions import Fault, TransportError
from zeep.plugins import HistoryPlugin  # <-- Added for envelope tracking
from lxml import etree  # <-- Required to print XML nicely
from .. import schemas
from .config import bse_settings
from typing import Union
import re

from .validators import (
    validate_transaction_code, validate_reference_number,
    validate_member_code, validate_client_code, validate_scheme_code,
    validate_amount, validate_units, validate_mandate_id,
    validate_date_format
)
from .exceptions import (
    BSEIntegrationError, BSEOrderError, BSEValidationError,
    BSESoapFault, BSETransportError
)

# Configure logging
logger = logging.getLogger('bse_integration')
soap_handler = logging.FileHandler('bse_soap_calls.log')
soap_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(soap_handler)

# WSDL cache directory
cache_dir = os.path.join(os.path.dirname(__file__), '.wsdl_cache')
os.makedirs(cache_dir, exist_ok=True)

transport = Transport(
    cache=SqliteCache(path=os.path.join(cache_dir, 'zeep.db'), timeout=60*60*24),
    timeout=30,
    operation_timeout=60,
    session=Session()
)

SOAP_NS = {
    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
    'wsa': 'http://www.w3.org/2005/08/addressing',
    'star': 'http://bsestarmf.in/'
}

class SOAPMessageHandler:
    """
    Handles SOAP message formatting and parsing for BSE STAR MF API
    """
    
    
    def __init__(self):
        """Initialize the SOAP message handler"""
        self.wsdl_url = bse_settings.BSE_ORDER_ENTRY_WSDL
        self.service_url = bse_settings.BSE_ORDER_ENTRY_SECURE
        self.history = HistoryPlugin()  # Plugin to track SOAP requests

        try:
            print("DEBUG: About to create requests.Session instance within SOAPMessageHandler.__init__.")
            print(f"DEBUG: BSE_REQUEST_TIMEOUT (from bse_settings) = {bse_settings.BSE_REQUEST_TIMEOUT}")
            
            session = Session()
            print("DEBUG: requests.Session instance created within SOAPMessageHandler.__init__.")

            # Configure SSL
            session.verify = bse_settings.BSE_VERIFY_SSL
            if bse_settings.BSE_SSL_CERT_PATH:
                session.verify = bse_settings.BSE_SSL_CERT_PATH

            # Setup transport with cache
            transport = Transport(
                session=session,
                timeout=bse_settings.BSE_REQUEST_TIMEOUT,
                cache=SqliteCache(path=os.path.join(cache_dir, 'zeep.db'))
            )

            # Initialize SOAP client
            self._raw_client = Client(self.wsdl_url, transport=transport, plugins=[self.history])

            # Correct SOAP binding (must match WSDL)
            soap_binding = '{http://tempuri.org/}WSHttpBinding_MFOrderEntry1'
            self.client = self._raw_client.create_service(soap_binding, self.service_url)

            # Set HTTP headers
            self._raw_client.transport.session.headers.update({
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'Accept': 'application/soap+xml',
                'SOAPAction': 'http://bsestarmf.in/MFOrderEntry/orderEntryParam',
                'Connection': 'Keep-Alive'
            })

            logger.info("Initialized SOAP client for BSE Order service")

        except Exception as e:
            logger.error(f"Failed to initialize SOAP client: {e}", exc_info=True)
            raise BSETransportError(f"WSDL initialization failed: {str(e)}")

    def create_soap_envelope(self, method: str, params: Dict[str, Any]) -> str:
        """Create a SOAP envelope for the given method and parameters"""
        try:
            soap_envelope = self._raw_client.create_message(self.client, method, **params)

            return soap_envelope
        except Exception as e:
            logger.error(f"Failed to create SOAP envelope: {e}", exc_info=True)
            raise BSEValidationError(f"Failed to create SOAP envelope: {str(e)}")

    def create_purchase_request(self, params: Dict[str, Any]) -> str:
        """Create a purchase request SOAP envelope"""
        try:
            return self.create_soap_envelope("orderEntryParam", params)
        except Exception as e:
            logger.error(f"Failed to create purchase request: {e}", exc_info=True)
            raise BSEValidationError(f"Failed to create purchase request: {str(e)}")

    def parse_order_response(self, response_text: Union[str, 'OrderResponse']) -> 'OrderResponse':
        """Parse order response from BSE into OrderResponse format"""
        try:
            if isinstance(response_text, OrderResponse):
                return response_text  # already parsed
            return OrderResponse.from_pipe_separated(response_text)
        except Exception as e:
            logger.error(f"Failed to parse order response: {e}", exc_info=True)
            raise BSEValidationError(f"Failed to parse order response: {str(e)}")

    def parse_soap_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the SOAP response into a structured format"""
        try:
            parts = [part.strip() for part in response_text.split('|')]
            result = {
                "status_code": parts[0] if len(parts) > 0 else "",
                "message": parts[1] if len(parts) > 1 else "",
                "success": parts[0] == "100",
                "data": {}
            }
            if len(parts) > 2:
                result["data"]["order_id"] = parts[2]
            if len(parts) > 3:
                result["data"]["client_code"] = parts[3]
            if len(parts) > 4:
                result["data"]["bse_remarks"] = parts[4]
            return result
        except Exception as e:
            logger.error(f"Failed to parse SOAP response: {e}", exc_info=True)
            raise BSEValidationError(f"Failed to parse SOAP response: {str(e)}")

    async def send_soap_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a SOAP request to the BSE API"""
        try:
            def soap_call():
                return getattr(self.client.service, method)(**params)

            response = await asyncio.to_thread(soap_call)
            logger.debug(f"BSE Response: {response}")

            # Log full SOAP envelope if available
            print("DEBUG: Inside send_soap_request, checking SOAP history")

# Log the raw XML content of last sent SOAP request
            if self.history.last_sent:
                sent_envelope = etree.tostring(self.history.last_sent.envelope, pretty_print=True, encoding="unicode")
                print("----- SOAP Request -----")
                print(sent_envelope)
                logger.debug("SOAP Request Envelope:\n%s", sent_envelope)
            else:
                print("DEBUG: No SOAP request captured in history.")

# Log the raw XML content of last received SOAP response
            if self.history.last_received:
                received_envelope = etree.tostring(self.history.last_received.envelope, pretty_print=True, encoding ="unicode")
                print("----- SOAP Response -----")
                print(received_envelope)
                logger.debug("SOAP Response Envelope:\n%s", received_envelope)
            else:
                print("DEBUG: No SOAP response captured in history.")

            return self.parse_soap_response(str(response))

        except Fault as e:
            logger.error(f"SOAP fault: {e}", exc_info=True)
            raise BSESoapFault(f"SOAP fault: {str(e)}")
        except TransportError as e:
            logger.error(f"Transport error: {e}", exc_info=True)
            raise BSETransportError(f"Transport error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise BSEOrderError(f"Unexpected error: {str(e)}")


# Order Status Constants
class OrderStatus:
    RECEIVED = "RECEIVED"
    PENDING = "PENDING"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    SENT_TO_BSE = "SENT_TO_BSE"
    ACCEPTED_BY_BSE = "ACCEPTED_BY_BSE"
    REJECTED_BY_BSE = "REJECTED_BY_BSE"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Common BSE error codes mapping (add more as needed)
BSE_ERROR_CODES = {
    "101": "Invalid credentials or authentication failed",
    "102": "Order not found",
    "103": "Invalid order parameters",
    "104": "Order already processed",
    "105": "Insufficient balance",
    "106": "Scheme not available",
    "107": "Client code not found",
    "108": "Order cancelled",
    "109": "Order rejected by BSE",
    "110": "Duplicate order",
    # Add more error codes and messages as per BSE documentation
}

@dataclass
class OrderResponse:
    """Standard response format for all order types"""
    success: bool
    order_id: str
    message: str
    status_code: str
    details: Dict[str, Any]

    @property
    def success_flag(self) -> str:
        return self.details.get("success_flag", "N")
    @property
    def bse_remarks(self) -> str:
        return self.details.get("bse_remarks", "")
    @property
    def order_number(self) -> str:
        return self.order_id or ""


    @classmethod
    def from_pipe_separated(cls, response_text: str) -> 'OrderResponse':
        """Parse pipe-separated BSE response into standard format"""
        if not response_text or not response_text.strip():
            raise ValueError("Empty response text")
            
        parts = [part.strip() for part in response_text.split('|')]
        
        # Handle minimum required parts
        if len(parts) < 8:
            raise ValueError(f"Invalid response format - insufficient parts: {response_text}")
        
        trans_type = parts[0]
        unique_ref_no = parts[1]
        raw_order_id = parts[2]
        user_id = parts[3]
        member_id = parts[4]
        client_code = parts[5]
        message = parts[6]
        status_code = "Y" if "ORD CONF" in parts[6].upper() else "N"

        
        confirmation_time = None
        confirmation_match = re.search(r'CONFIRMATION TIME:\s+(.*?)\s+ENTRY BY', message)
        if confirmation_match:
            confirmation_time = confirmation_match.group(1).strip()

        
        extracted_order_id = raw_order_id or ""
        if not extracted_order_id:
            order_match = re.search(r'ORDER NO:\s*(\d+)', message)
            if order_match:
                extracted_order_id = order_match.group(1)
        success = status_code == "Y" and extracted_order_id not in ["", "0"]

        
        return cls(
            success=success,
            order_id=extracted_order_id,
            message=message,
            status_code=status_code,
            details={
                "trans_type": trans_type,
                "unique_ref_no": unique_ref_no,
                "user_id": user_id,
                "member_id": member_id,
                "client_code": client_code,
                "bse_remarks": message,
                "success_flag": "Y" if success else "N",
                "order_number": extracted_order_id,
                "confirmation_time": confirmation_time,
                "raw_response": response_text
            }
        )

    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failures += 1
        self.last_failure_time = time()
        
        if self.failures >= self.failure_threshold:
            self.state = 'OPEN'
            self.logger.warning(f"Circuit OPENED after {self.failures} failures")

    def record_success(self):
        """Record a success and potentially close the circuit"""
        self.failures = 0
        self.state = 'CLOSED'
        self.logger.info("Circuit CLOSED after successful call")

    def can_execute(self) -> bool:
        """Check if the circuit allows execution"""
        if self.state == 'CLOSED':
            return True
            
        if self.state == 'OPEN':
            # Check if enough time has passed to try again
            if time() - self.last_failure_time >= self.reset_timeout:
                self.state = 'HALF_OPEN'
                self.logger.info("Circuit entering HALF_OPEN state")
                return True
            return False
            
        # HALF_OPEN state
        return True

class BSEOrderPlacer:
    """
    Handles order placement with BSE STAR MF API.
    Supports various order types: lumpsum, SIP, XSIP, switch, spread.
    """

    def __init__(self) -> None: # Note: If your original __init__ took bse_settings as Depends, keep that.
                                # This snippet doesn't show it explicitly, but earlier thought did.
                                # Assuming bse_settings is imported globally here for this snippet's context.
        """Initialize BSE Order Placer."""
        logger.info("Initializing BSE Order Placer")
        self.user_id = bse_settings.BSE_USER_ID
        self.member_id = bse_settings.BSE_MEMBER_CODE
        # Use the secure HTTPS endpoint instead of WSDL
        self.service_url = bse_settings.BSE_ORDER_ENTRY_SECURE
        self.wsdl_url = bse_settings.BSE_ORDER_ENTRY_WSDL

        logger.debug(f"Using Service URL: {self.service_url}")
        logger.debug(f"Using WSDL URL: {self.wsdl_url}")
        logger.debug(f"User ID: {self.user_id}")
        logger.debug(f"Member ID: {self.member_id}")

        # Validate essential config with strict validation
        if not self.user_id:
            raise BSEValidationError("BSE_USER_ID is required")
        if not self.member_id:
            raise BSEValidationError("BSE_MEMBER_CODE is required")
        if not self.wsdl_url:
            raise BSEValidationError("BSE_ORDER_ENTRY_WSDL is required")

        # Initialize SOAP client
        try:
            logger.info("Initializing SOAP client...")
            
            # Set up cached transport
            cache = SqliteCache(path=os.path.join(cache_dir, 'zeep.db')) # Ensure cache_dir is defined and accessible
            
            # Configure SOAP client settings
            settings = Settings(
                strict=False,   # Less strict XML parsing
                xml_huge_tree=True,   # Handle large XML
                force_https=True    # Force HTTPS for security
            )
            
            # Add these debug prints around session initialization
            print("DEBUG: About to create requests.Session instance within BSEOrderPlacer.__init__.")
            # If bse_settings is passed as a parameter to __init__, you'd use self.bse_settings.BSE_REQUEST_TIMEOUT
            # Otherwise, ensure bse_settings is imported or accessible here.
            # Assuming bse_settings is accessible, as it's used for self.user_id etc.
            print(f"DEBUG: BSE_REQUEST_TIMEOUT (from bse_settings) = {bse_settings.BSE_REQUEST_TIMEOUT}")
            session = Session()
            print("DEBUG: requests.Session instance created within BSEOrderPlacer.__init__.")
            
            # Create transport with the session and cache
            transport = Transport(
                session=session,
                cache=cache,
                timeout=bse_settings.BSE_REQUEST_TIMEOUT,
                operation_timeout=bse_settings.BSE_REQUEST_TIMEOUT
            )
            
            # Create SOAP client with transport and settings, but use secure service URL
            self.client = Client(
                self.wsdl_url,
                transport=transport,
                settings=settings,
                wsse=None  # No WSSE security
            )
            
            # Override the service location to use the secure endpoint
            # Get the service binding and update the address
            # Create service with the secure binding
            binding_name = "{http://tempuri.org/}WSHttpBinding_MFOrderEntry1"
            self.service = self.client.create_service(
                binding_name=binding_name,
                address=self.service_url
            )
            logger.info(f"Created service with binding {binding_name} at {self.service_url}")
            
            # Add SOAP headers for secure endpoint
            self.client.transport.session.headers.update({
                'Content-Type': 'text/xml;charset=UTF-8',
                'Accept': 'text/xml',
                'SOAPAction': 'http://bsestarmf.in/MFOrderEntry/orderEntryParam',
                'X-SOAP-Action': 'http://bsestarmf.in/MFOrderEntry/orderEntryParam',
                'Connection': 'Keep-Alive'
            })
            
            # Configure transport for HTTPS
            self.client.transport.session.verify = bse_settings.BSE_VERIFY_SSL
            if bse_settings.BSE_SSL_CERT_PATH:
                self.client.transport.session.verify = bse_settings.BSE_SSL_CERT_PATH
            
            logger.info("SOAP client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SOAP client: {e}", exc_info=True)
            raise BSEOrderError(f"WSDL initialization failed: {str(e)}")

    def create_soap_envelope(self, method: str, params: Dict[str, Any]) -> str:
        """Create SOAP envelope for BSE STAR MF web service"""
        root = ET.Element(f"{{{SOAP_NS['soap']}}}Envelope")
        for prefix, uri in SOAP_NS.items():
            root.set(f'xmlns:{prefix}', uri)

        header = ET.SubElement(root, f"{{{SOAP_NS['soap']}}}Header")
        action = ET.SubElement(header, f"{{{SOAP_NS['wsa']}}}Action")
        action.text = f"http://bsestarmf.in/MFOrderEntry/{method}"

        body = ET.SubElement(root, f"{{{SOAP_NS['soap']}}}Body")
        request = ET.SubElement(body, f"{{{SOAP_NS['star']}}}{method}")

        for key, value in params.items():
            param = ET.SubElement(request, key)
            param.text = str(value)

        return ET.tostring(root, encoding='utf-8', method='xml').decode()

    def parse_soap_response(self, response_text: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Parse SOAP response from BSE STAR MF"""
        try:
            root = ET.fromstring(response_text)
            body = root.find(f".//{{{SOAP_NS['soap']}}}Body")
            if body is None:
                raise BSEOrderError("Invalid SOAP response: missing Body element")

            # Check for fault
            fault = body.find(f".//{{{SOAP_NS['soap']}}}Fault")
            if fault is not None:
                code = fault.find('.//faultcode')
                reason = fault.find('.//faultstring')
                raise BSESoapFault(
                    f"SOAP fault: {reason.text if reason is not None else 'Unknown error'}",
                    code.text if code is not None else 'Unknown'
                )

            # Parse response
            result = body.find(f".//{{{SOAP_NS['star']}}}Response")
            if result is None:
                raise BSEOrderError("Invalid SOAP response: missing Response element")

            return True, result.text, {}

        except ET.ParseError as e:
            logger.error(f"Failed to parse SOAP response: {e}", exc_info=True)
            raise BSEOrderError(f"Invalid SOAP response: {str(e)}")

    async def _send_soap_request(self, soap_method: str, params: Dict[str, Any]) -> OrderResponse:
        """Send SOAP request to BSE"""
        try:
            logger.info(f"Sending SOAP request: {soap_method}")
            logger.debug(f"Request parameters: {json.dumps(params, indent=2)}")

            if not hasattr(self.service, soap_method):
                raise BSEIntegrationError(f"SOAP method {soap_method} not found")

            # Add required BSE headers
            soap_action = f"http://bsestarmf.in/MFOrderEntry/{soap_method}"
            self.client.transport.session.headers.update({
                'SOAPAction': soap_action,
                'X-SOAP-Action': soap_action
            })

            def soap_call():
                try:
                    # Use the service object created with the secure binding
                    return getattr(self.service, soap_method)(**params)
                except Exception as e:
                    logger.error(f"SOAP call failed: {e}", exc_info=True)
                    raise

            # Send request with retry logic
            max_retries = bse_settings.BSE_MAX_RETRIES
            retry_delay = bse_settings.BSE_RETRY_DELAY
            
            last_error = None
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Attempt {attempt + 1}/{max_retries}")
                    response = await asyncio.to_thread(soap_call)
                    logger.debug(f"BSE Raw Response: {response}")
                    
                    # Handle different response formats
                    response_str = str(response).strip()
                    
                    # Check if response is empty or None
                    if not response_str or response_str.lower() in ['none', 'null', '']:
                        logger.error("Empty response from BSE")
                        raise BSEIntegrationError("Empty response from BSE")
                    
                    # Try to parse as pipe-separated format
                    # After parsing response:
                    try:
                        order_response = OrderResponse.from_pipe_separated(response_str)
                    except (ValueError, IndexError) as parse_error:
                        logger.error(f"Failed to parse BSE response as pipe-separated: {parse_error}")
                        logger.error(f"Raw response: {response_str}")
    
                        order_response = OrderResponse(
                            success=False,
                            order_id="",
                            message=f"BSE response parsing failed: {response_str}",
                            status_code="0",
                            details={"raw_response": response_str}
                        )

# ✅ Return if parsed successfully
                    if order_response.success:
                        return order_response

# ❌ Don’t raise error if message confirms order
                    if "confirmation time" in order_response.message.lower() and "order no" in order_response.message.lower():
                        logger.warning("Order appears confirmed but status code is not 'Y'. Proceeding.")
                        return order_response

# 🚨 Otherwise raise based on status_code
                    error_code = order_response.status_code
                    error_msg = BSE_ERROR_CODES.get(error_code, order_response.message or "Unknown error")
                    logger.error(f"BSE Error {error_code}: {error_msg}")

                    if error_code in ["101", "102", "103"]:
                        raise BSEValidationError(f"BSE Validation Error: {error_msg}")
                    elif error_code in ["104", "105", "106"]:
                        raise BSEOrderError(f"BSE Order Error: {error_msg}")
                    else:
                        raise BSEIntegrationError(f"BSE Error: {error_msg}")

                    
                    return order_response
                    
                except (TransportError, RequestException) as e:
                    last_error = e
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after error: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                except (BSEValidationError, BSEOrderError, BSEIntegrationError):
                    # Don't retry these errors
                    raise

            # If we got here, all retries failed
            raise last_error or BSETransportError("All retry attempts failed")

        except (TransportError, RequestException) as e:
            logger.error(f"Transport-level SOAP failure: {e}", exc_info=True)
            raise

        except (BSEValidationError, BSEOrderError, BSEIntegrationError) as be:
            logger.warning(f"BSE Business Error: {be}", exc_info=True)
            raise

        except Exception as e:
            logger.error(f"Unexpected error during SOAP request: {e}", exc_info=True)
            raise


    def _validate_response(self, response_text: str) -> Tuple[bool, str]:
        """Validate BSE response and extract status"""
        parts = response_text.split('|')
        if len(parts) < 2:
            raise BSEOrderError("Invalid response format")
            
        status_code = parts[0].strip().upper()
        message = parts[1].strip()
        
        if status_code in {"Y", "100"}:
            return True, message
        else:
            return False, message

    async def place_lumpsum_order(self, order_data: schemas.LumpsumOrderRequest, encrypted_password: str) -> OrderResponse:
        """Place lumpsum order (Purchase/Redemption)"""
        
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields using the correct field names from LumpsumOrderRequest
        validate_transaction_code(order_data.TransCode)
        validate_reference_number(order_data.TransNo)
        validate_member_code(self.member_id)
        validate_client_code(order_data.ClientCode)
        validate_scheme_code(order_data.SchemeCd)
        
        if order_data.Amount:
            validate_amount(str(order_data.Amount))
        if order_data.Qty:
            validate_units(str(order_data.Qty))

        # Prepare parameters using the exact BSE API signature
        params = {
            "TransCode": order_data.TransCode,
            "TransNo": order_data.TransNo,
            "OrderId": "",  # Not provided in LumpsumOrderRequest
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": order_data.ClientCode,
            "SchemeCd": order_data.SchemeCd,
            "BuySell": order_data.BuySell,
            "BuySellType": order_data.BuySellType or "FRESH",
            "DPTxn": order_data.DPTxn,
            "OrderVal": str(order_data.Amount or ""),
            "Qty": str(order_data.Qty or ""),
            "AllRedeem": order_data.AllRedeem or "N",
            "FolioNo": order_data.FolioNo or "",
            "Remarks": order_data.Remarks or "",
            "KYCStatus": order_data.KYCStatus or "Y",
            "RefNo": order_data.RefNo,  # Use dedicated RefNo field
            "SubBrCode": order_data.SubBrokerARN or "",
            "EUIN": order_data.EUIN or "",
            "EUINVal": "Y" if order_data.EUIN else "N",
            "MinRedeem": "N",  # Not provided in LumpsumOrderRequest
            "DPC": order_data.DPC or "N",
            "IPAdd": order_data.IPAdd or "",
            "Password": encrypted_password,
            "PassKey": order_data.PassKey,  # Use the same PassKey used for password encryption
            "Parma1": "",  # Note: BSE API has typo "Parma1" instead of "Param1"
            "Param2": "",
            "Param3": "",
            "MobileNo": order_data.MobileNo or "",
            "EmailID": order_data.EmailID or "",
            "MandateID": order_data.MandateID or "",
            "Filler1": "",
            "Filler2": "",
            "Filler3": "",
            "Filler4": "",
            "Filler5": "",
            "Filler6": ""
        }

        logger.info(f"Placing {order_data.BuySell} order for {order_data.TransNo}")
        logger.debug(f"SOAP Request Parameters: {json.dumps(params, indent=2)}")
        try:
            response = await self._send_soap_request("orderEntryParam", params)
            logger.debug(f"SOAP Response: {response}")
            return response
        except Exception as e:
            logger.error(f"SOAP Request failed with parameters: {json.dumps(params, indent=2)}")
            raise

    async def place_sip_order(self, sip_data: schemas.SIPOrderCreate, encrypted_password: str) -> OrderResponse:
        """Place new SIP registration order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields
        validate_transaction_code(sip_data.transaction_code)
        validate_reference_number(sip_data.unique_ref_no)
        validate_member_code(self.member_id)
        validate_client_code(sip_data.client_code)
        validate_scheme_code(sip_data.scheme_code)
        validate_amount(str(sip_data.installment_amount))
        validate_mandate_id(sip_data.mandate_id)
        validate_date_format(sip_data.start_date.strftime("%d/%m/%Y"))

        params = {
            "TransactionCode": sip_data.transaction_code,
            "UniqueRefNo": sip_data.unique_ref_no,
            "SchemeCode": sip_data.scheme_code,
            "MemberCode": self.member_id,
            "ClientCode": sip_data.client_code,
            "UserID": self.user_id,
            "InternalRefNo": sip_data.internal_ref_no or "",
            "TransMode": "P",  # Always Purchase for SIP
            "DpTxnMode": sip_data.dp_txn_mode.value,
            "StartDate": sip_data.start_date.strftime("%d/%m/%Y"),
            "FrequencyType": sip_data.frequency_type.value,
            "FrequencyAllowed": str(sip_data.frequency_allowed),
            "InstallmentAmount": str(sip_data.installment_amount),
            "NoOfInstallment": str(sip_data.no_of_installments),
            "Remarks": sip_data.remarks or "",
            "FolioNo": sip_data.folio_no or "",
            "FirstOrderFlag": "Y" if sip_data.first_order_today else "N",
            "SubberCode": sip_data.sub_broker_arn or "",
            "Euin": sip_data.euin or "",
            "EuinVal": "Y" if sip_data.euin_declaration else "N",
            "DPC": "Y" if sip_data.dpc_flag else "N",
            "RegId": "",
            "IPAdd": sip_data.ip_address or "",
            "Password": encrypted_password,
            "PassKey": "",
            "Param1": "",
            "Param2": "",
            "Param3": "",
            "Filler1": "",
            "Filler2": "",
            "Filler3": "",
            "Filler4": "",
            "Filler5": "",
            "Filler6": ""
        }

        logger.info(f"Registering SIP for {sip_data.unique_ref_no}")
        return await self._send_soap_request("sipOrderEntryParam", params)

    async def place_xsip_order(self, xsip_data: schemas.XSIPOrderCreate, encrypted_password: str) -> OrderResponse:
        """Place new XSIP registration order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields
        validate_transaction_code(xsip_data.transaction_code)
        validate_reference_number(xsip_data.unique_ref_no)
        validate_member_code(self.member_id)
        validate_client_code(xsip_data.client_code)
        validate_scheme_code(xsip_data.scheme_code)
        validate_amount(str(xsip_data.installment_amount))
        validate_mandate_id(xsip_data.mandate_id)
        validate_date_format(xsip_data.start_date.strftime("%d/%m/%Y"))

        params = {
            "TransCode": "XSIP",
            "TransNo": xsip_data.unique_ref_no,
            "SchemeCode": xsip_data.scheme_code,
            "MemberCode": self.member_id,
            "ClientCode": xsip_data.client_code,
            "UserID": self.user_id,
            "InternalRefNo": xsip_data.internal_ref_no or "",
            "TransMode": "P",  # Always Purchase for XSIP
            "DpTxnMode": xsip_data.dp_txn_mode.value,
            "StartDate": xsip_data.start_date.strftime("%d/%m/%Y"),
            "FrequencyType": xsip_data.frequency_type.value,
            "FrequencyAllowed": str(xsip_data.frequency_allowed),
            "InstallmentAmount": str(xsip_data.installment_amount),
            "NoOfInstallment": str(xsip_data.no_of_installments),
            "FolioNo": xsip_data.folio_no or "",
            "FirstOrderFlag": "Y" if xsip_data.first_order_today else "N",
            "SubBrCode": xsip_data.sub_broker_arn or "",
            "EUIN": xsip_data.euin or "",
            "EUINVal": "Y" if xsip_data.euin_declaration else "N",
            "DPC": "Y" if xsip_data.dpc_flag else "N",
            "RegDate": datetime.now().strftime("%d/%m/%Y"),
            "IPAdd": xsip_data.ip_address or "",
            "Password": encrypted_password,
            "PassKey": "",
            "MandateID": xsip_data.mandate_id,
            "Brokerage": str(xsip_data.brokerage or ""),
            "Remarks": xsip_data.remarks or "",
            "KYCStatus": xsip_data.kyc_status,
            "XsipRegID": xsip_data.xsip_reg_id or "",
            "Param1": "",
            "Param2": "",
            "Param3": ""
        }

        logger.info(f"Registering XSIP for {xsip_data.unique_ref_no}")
        return await self._send_soap_request("xsipOrderEntryParam", params)

    async def modify_sip_order(self, sip_data: schemas.SIPOrderModify, encrypted_password: str) -> OrderResponse:
        """Modify existing SIP registration"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields
        validate_transaction_code(sip_data.transaction_code)
        validate_reference_number(sip_data.unique_ref_no)
        validate_member_code(sip_data.member_id)
        validate_client_code(sip_data.client_code)
        
        if sip_data.new_amount:
            validate_amount(str(sip_data.new_amount))

        params = {
            "TransCode": sip_data.transaction_code,
            "TransNo": sip_data.unique_ref_no,
            "RegId": sip_data.sip_reg_id,
            "MemberCode": sip_data.member_id,
            "ClientCode": sip_data.client_code,
            "UserID": sip_data.user_id,
            "Amount": str(sip_data.new_amount or ""),
            "NoOfInstallment": str(sip_data.new_installments or ""),
            "Password": encrypted_password
        }

        logger.info(f"Modifying SIP {sip_data.sip_reg_id}")
        return await self._send_soap_request("modifySipOrderParam", params)

    async def modify_xsip_order(self, xsip_data: schemas.XSIPOrderModify, encrypted_password: str) -> OrderResponse:
        """Modify existing XSIP registration"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields
        validate_transaction_code(xsip_data.transaction_code)
        validate_reference_number(xsip_data.unique_ref_no)
        validate_member_code(xsip_data.member_id)
        validate_client_code(xsip_data.client_code)
        
        if xsip_data.new_amount:
            validate_amount(str(xsip_data.new_amount))

        params = {
            "TransCode": "MODXSIP",
            "TransNo": xsip_data.unique_ref_no,
            "XsipRegId": xsip_data.xsip_reg_id,
            "MemberCode": xsip_data.member_id,
            "ClientCode": xsip_data.client_code,
            "UserID": xsip_data.user_id,
            "Amount": str(xsip_data.new_amount or ""),
            "NoOfInstallment": str(xsip_data.new_installments or ""),
            "Password": encrypted_password
        }

        logger.info(f"Modifying XSIP {xsip_data.xsip_reg_id}")
        return await self._send_soap_request("modifyXsipOrderParam", params)

    async def place_switch_order(self, switch_data: schemas.SwitchOrderCreate, encrypted_password: str) -> OrderResponse:
        """Place switch order between schemes"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields
        validate_transaction_code(switch_data.transaction_code)
        validate_reference_number(switch_data.unique_ref_no)
        validate_member_code(self.member_id)
        validate_client_code(switch_data.client_code)
        validate_scheme_code(switch_data.from_scheme_code)
        validate_scheme_code(switch_data.to_scheme_code)
        
        if switch_data.switch_amount:
            validate_amount(str(switch_data.switch_amount))
        if switch_data.switch_units:
            validate_units(str(switch_data.switch_units))

        params = {
            "TransactionCode": "SWITCH",
            "UniqueRefNo": switch_data.unique_ref_no,
            "FromSchemeCode": switch_data.from_scheme_code,
            "ToSchemeCode": switch_data.to_scheme_code,
            "UserID": self.user_id,
            "MemberCode": self.member_id,
            "ClientCode": switch_data.client_code,
            "Amount": str(switch_data.switch_amount or ""),
            "Units": str(switch_data.switch_units or ""),
            "FolioNo": switch_data.folio_no or "",
            "BuySellType": "FRESH",
            "DpTxnMode": switch_data.dp_txn_mode.value,
            "SubberCode": switch_data.sub_broker_arn or "",
            "Euin": switch_data.euin or "",
            "EuinVal": "Y" if switch_data.euin_declaration else "N",
            "KYCStatus": switch_data.kyc_status or "Y",
            "Password": encrypted_password,
            "Remarks": switch_data.remarks or "",
            "IPAdd": switch_data.ip_address or "",
            "Param1": "",
            "Param2": "",
            "Param3": "",
            "Filler1": "",
            "Filler2": "",
            "Filler3": ""
        }

        logger.info(f"Placing switch order for {switch_data.unique_ref_no}")
        return await self._send_soap_request("switchOrderParam", params)

    async def place_spread_order(self, spread_data: schemas.SpreadOrderCreate, encrypted_password: str) -> OrderResponse:
        """Place spread order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields
        validate_transaction_code(spread_data.transaction_code)
        validate_reference_number(spread_data.unique_ref_no)
        validate_member_code(self.member_id)
        validate_client_code(spread_data.client_code)
        validate_scheme_code(spread_data.scheme_code)
        validate_date_format(spread_data.redeem_date.strftime("%d/%m/%Y"))
        
        if spread_data.purchase_amount:
            validate_amount(str(spread_data.purchase_amount))
        if spread_data.redemption_amount:
            validate_amount(str(spread_data.redemption_amount))

        params = {
            "TransCode": spread_data.transaction_code,
            "TransNo": spread_data.unique_ref_no,
            "OrderId": spread_data.order_id or "",
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": spread_data.client_code,
            "SchemeCd": spread_data.scheme_code,
            "BuySell": spread_data.buy_sell,
            "BuySellType": spread_data.buy_sell_type.value,
            "DPTxn": spread_data.dp_txn_mode.value,
            "PurchaseAmount": str(spread_data.purchase_amount or ""),
            "RedemptionAmount": str(spread_data.redemption_amount or ""),
            "AllUnitsFlag": "Y" if spread_data.all_units_flag else "N",
            "RedeemDate": spread_data.redeem_date.strftime("%d/%m/%Y"),
            "FolioNo": spread_data.folio_no or "",
            "Remarks": spread_data.remarks or "",
            "KYCStatus": spread_data.kyc_status,
            "SubBrCode": spread_data.sub_broker_arn or "",
            "EUIN": spread_data.euin or "",
            "EUINVal": "Y" if spread_data.euin_declaration else "N",
            "MinRedeem": "Y" if spread_data.min_redeem else "N",
            "DPC": "Y" if spread_data.dpc_flag else "N",
            "IPAdd": spread_data.ip_address or "",
            "Password": encrypted_password,
            "PassKey": "",
            "Param1": "",
            "Param2": "",
            "Param3": ""
        }

        logger.info(f"Placing spread order for {spread_data.unique_ref_no}")
        return await self._send_soap_request("spreadOrderEntryParam", params)

    async def cancel_order(self, order_id: str, client_code: str, encrypted_password: str) -> OrderResponse:
        """Cancel any type of order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields
        validate_client_code(client_code)

        params = {
            "TransCode": "CXL",
            "TransNo": f"CXL{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "OrderId": order_id,
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": client_code,
            "Password": encrypted_password
        }

        logger.info(f"Cancelling order {order_id}")
        return await self._send_soap_request("cancelOrderParam", params)

    async def cancel_sip_order(self, sip_reg_id: str, client_code: str, encrypted_password: str) -> OrderResponse:
        """Cancel existing SIP registration"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields
        validate_client_code(client_code)

        params = {
            "TransCode": "CXLSIP",
            "TransNo": f"CXLSIP{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "RegId": sip_reg_id,
            "MemberCode": self.member_id,
            "ClientCode": client_code,
            "UserID": self.user_id,
            "Password": encrypted_password
        }

        logger.info(f"Cancelling SIP registration {sip_reg_id}")
        return await self._send_soap_request("cancelSipOrderParam", params)

    async def cancel_xsip_order(self, order_id: str, client_code: str, encrypted_password: str) -> OrderResponse:
        """Cancel an XSIP order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate fields
        validate_client_code(client_code)

        params = {
            "TransCode": "XCXL",
            "TransNo": f"XCXL{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "OrderId": order_id,
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": client_code,
            "Password": encrypted_password
        }

        logger.info(f"Cancelling XSIP order {order_id}")
        return await self._send_soap_request("cancelXSIPOrderParam", params)

    async def get_order_status(self, order_id: str, encrypted_password: str) -> OrderResponse:
        """Get the status of any type of order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        params = {
            "TransCode": "ORDSTS",
            "TransNo": f"ORDSTS{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "OrderId": order_id,
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "Password": encrypted_password
        }

        logger.info(f"Getting status for order {order_id}")
        return await self._send_soap_request("orderStatusParam", params)

    async def get_orders_by_criteria(
        self,
        from_date: date,
        to_date: date,
        client_code: Optional[str],
        transaction_type: Optional[str],
        order_type: Optional[str],
        sub_order_type: Optional[str],
        settlement_type: Optional[str],
        encrypted_password: str
    ) -> OrderResponse:
        """
        Get orders by various criteria as per BSE specifications.
        
        Args:
            from_date: Start date for order search (DD/MM/YYYY)
            to_date: End date for order search (DD/MM/YYYY)
            client_code: Optional client code to filter orders
            transaction_type: Optional filter (P/R)
            order_type: Optional filter (ALL/MFD/SIP/XSIP/STP/SWITCH)
            sub_order_type: Optional filter (ALL/NFO/SPOR/SWITCH)
            settlement_type: Optional filter (ALL/L0/L1/OTHERS)
            encrypted_password: Encrypted password for authentication
        """
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate dates
        validate_date_format(from_date.strftime("%d/%m/%Y"))
        validate_date_format(to_date.strftime("%d/%m/%Y"))
        
        if from_date > to_date:
            raise BSEValidationError("From date cannot be later than to date")

        # Validate optional fields
        if client_code:
            validate_client_code(client_code)
        if transaction_type and transaction_type not in ['P', 'R']:
            raise BSEValidationError("Transaction type must be P or R")
        if order_type and order_type not in ['ALL', 'MFD', 'SIP', 'XSIP', 'STP', 'SWP']:
            raise BSEValidationError("Invalid order type")
        if sub_order_type and sub_order_type not in ['ALL', 'NFO', 'SPOR', 'SWITCH']:
            raise BSEValidationError("Invalid sub order type")
        if settlement_type and settlement_type not in ['ALL', 'L0', 'L1', 'OTHERS']:
            raise BSEValidationError("Invalid settlement type")

        params = {
            "FromDate": from_date.strftime("%d/%m/%Y"),
            "ToDate": to_date.strftime("%d/%m/%Y"),
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": client_code or "",
            "TransactionType": transaction_type or "",
            "OrderType": order_type or "ALL",
            "SubOrderType": sub_order_type or "ALL",
            "SettlementType": settlement_type or "ALL",
            "Password": encrypted_password,
            "OrderNo": "",  # Empty when searching by criteria
        }

        logger.info(f"Fetching orders from {from_date} to {to_date}")
        return await self._send_soap_request("getOrderStatus", params)

    def parse_order_status_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse BSE order status response into structured format.
        Handles all fields as per BSE manual.
        """
        try:
            parts = response_text.split('|')
            status_dict = {
                "status_code": parts[0] if len(parts) > 0 else None,
                "member_code": parts[1] if len(parts) > 1 else None,
                "client_code": parts[2] if len(parts) > 2 else None,
                "order_no": parts[3] if len(parts) > 3 else None,
                "bse_remarks": parts[4] if len(parts) > 4 else None,
                "order_status": parts[5] if len(parts) > 5 else None,
                "order_remarks": parts[6] if len(parts) > 6 else None,
                "scheme_code": parts[7] if len(parts) > 7 else None,
                "scheme_name": parts[8] if len(parts) > 8 else None,
                "isin": parts[9] if len(parts) > 9 else None,
                "buy_sell": parts[10] if len(parts) > 10 else None,
                "amount": float(parts[11]) if len(parts) > 11 and parts[11] else None,
                "quantity": float(parts[12]) if len(parts) > 12 and parts[12] else None,
                "allotted_nav": float(parts[13]) if len(parts) > 13 and parts[13] else None,
                "allotted_units": float(parts[14]) if len(parts) > 14 and parts[14] else None,
                "allotment_date": parts[15] if len(parts) > 15 else None,
                "valid_flag": parts[16] if len(parts) > 16 else None,
                "internal_ref_no": parts[17] if len(parts) > 17 else None,
                "dp_txn": parts[18] if len(parts) > 18 else None,
                "settlement_type": parts[19] if len(parts) > 19 else None,
                "order_type": parts[20] if len(parts) > 20 else None,
                "sub_order_type": parts[21] if len(parts) > 21 else None,
                "euin": parts[22] if len(parts) > 22 else None,
                "euin_flag": parts[23] if len(parts) > 23 else None,
                "sub_broker_arn": parts[24] if len(parts) > 24 else None,
                "payment_status": parts[25] if len(parts) > 25 else None,
                "settlement_status": parts[26] if len(parts) > 26 else None,
                "sip_reg_id": parts[27] if len(parts) > 27 else None,
                "sub_broker_code": parts[28] if len(parts) > 28 else None,
                "kyc_flag": parts[29] if len(parts) > 29 else None,
                "min_redeem_flag": parts[30] if len(parts) > 30 else None
            }

            # Convert to proper types
            if status_dict["allotment_date"]:
                try:
                    status_dict["allotment_date"] = datetime.strptime(
                        status_dict["allotment_date"], "%d/%m/%Y"
                    ).date()
                except ValueError:
                    logger.warning(f"Invalid allotment date format: {status_dict['allotment_date']}")

            # Validate status codes
            if status_dict["status_code"] not in ["100", "101"]:
                error_msg = BSE_ERROR_CODES.get(
                    status_dict["status_code"], 
                    f"Unknown error code: {status_dict['status_code']}"
                )
                logger.error(f"Order status error: {error_msg}")
                raise BSEOrderError(error_msg, status_dict["status_code"])

            return status_dict

        except Exception as e:
            logger.error(f"Failed to parse order status response: {e}", exc_info=True)
            raise BSEOrderError(f"Invalid order status response format: {str(e)}")

    async def get_allotment_statement(
        self,
        from_date: date,
        to_date: date,
        client_code: Optional[str],
        order_type: Optional[str],
        sub_order_type: Optional[str],
        settlement_type: Optional[str],
        encrypted_password: str
    ) -> OrderResponse:
        """
        Get allotment statement for orders as per BSE specifications.
        
        Args:
            from_date: Start date (DD/MM/YYYY)
            to_date: End date (DD/MM/YYYY)
            client_code: Optional client code
            order_type: Optional (ALL/MFD/SIP/XSIP/STP/SWP)
            sub_order_type: Optional (ALL/NFO/SPOR/SWITCH)
            settlement_type: Optional (ALL/L0/L1/OTHERS)
            encrypted_password: Encrypted password
        """
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate dates
        validate_date_format(from_date.strftime("%d/%m/%Y"))
        validate_date_format(to_date.strftime("%d/%m/%Y"))

        params = {
            "FromDate": from_date.strftime("%d/%m/%Y"),
            "ToDate": to_date.strftime("%d/%m/%Y"),
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": client_code or "",
            "OrderType": order_type or "ALL",
            "SubOrderType": sub_order_type or "ALL",
            "SettlementType": settlement_type or "ALL",
            "Password": encrypted_password,
            "OrderNo": ""
        }

        logger.info(f"Fetching allotment statement from {from_date} to {to_date}")
        return await self._send_soap_request("getAllotmentStatement", params)

    async def get_redemption_statement(
        self,
        from_date: date,
        to_date: date,
        client_code: Optional[str],
        order_type: Optional[str],
        sub_order_type: Optional[str],
        settlement_type: Optional[str],
        encrypted_password: str
    ) -> OrderResponse:
        """
        Get redemption statement for orders as per BSE specifications.
        
        Args:
            from_date: Start date (DD/MM/YYYY)
            to_date: End date (DD/MM/YYYY)
            client_code: Optional client code
            order_type: Optional (ALL/MFD/SIP/XSIP/STP/SWP)
            sub_order_type: Optional (ALL/NFO/SPOR/SWITCH)
            settlement_type: Optional (ALL/L0/L1/OTHERS)
            encrypted_password: Encrypted password
        """
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Validate dates
        validate_date_format(from_date.strftime("%d/%m/%Y"))
        validate_date_format(to_date.strftime("%d/%m/%Y"))

        params = {
            "FromDate": from_date.strftime("%d/%m/%Y"),
            "ToDate": to_date.strftime("%d/%m/%Y"),
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": client_code or "",
            "OrderType": order_type or "ALL",
            "SubOrderType": sub_order_type or "ALL",
            "SettlementType": settlement_type or "ALL",
            "Password": encrypted_password,
            "OrderNo": ""
        }

        logger.info(f"Fetching redemption statement from {from_date} to {to_date}")
        return await self._send_soap_request("getRedemptionStatement", params)

