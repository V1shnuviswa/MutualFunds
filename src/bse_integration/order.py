# /home/ubuntu/order_management_system/src/bse_integration/order.py

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

import requests
from requests.exceptions import RequestException
from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from requests import Session

from .config import bse_settings
from .exceptions import (
    BSEIntegrationError, BSEOrderError, BSETransportError, BSESoapFault,
    BSEValidationError
)
from .. import schemas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BSEOrderPlacer:
    """
    Handles order placement (Lumpsum, SIP) with BSE STAR MF using SOAP.
    Interacts with the MFOrderEntry service.
    Uses asyncio.to_thread for blocking SOAP calls.
    """

    def __init__(self) -> None:
        """
        Initialize BSE Order Placer.
        """
        self.wsdl_url = bse_settings.BSE_ORDER_ENTRY_WSDL
        self.user_id = bse_settings.BSE_USER_ID
        self.member_id = bse_settings.BSE_MEMBER_CODE

        if not self.wsdl_url:
            raise BSEIntegrationError("BSE_ORDER_ENTRY_WSDL is not configured.")
        if not self.user_id or not self.member_id:
             raise BSEIntegrationError("BSE User ID or Member ID not configured for order placement.")

        # Initialize SOAP client
        try:
            session = Session()
            transport = Transport(session=session)
            # Client initialization is typically not blocking I/O
            self.client = Client(self.wsdl_url, transport=transport)
            logger.info(f"Initialized SOAP client for BSE Order Entry service ({self.wsdl_url})")
        except Exception as e:
            logger.error(f"Failed to initialize SOAP client for {self.wsdl_url}: {e}", exc_info=True)
            raise BSEIntegrationError(f"WSDL initialization failed for order entry service: {str(e)}")

    def _parse_order_response(self, response: str) -> Dict[str, Any]:
        """
        Parses the response string from the order entry API.
        Synchronous method as it only parses strings.
        """
        try:
            parts = response.split("|")
            status_code = parts[0].strip()
            message = parts[1].strip() if len(parts) > 1 else ""
            unique_ref_no = parts[4].strip() if len(parts) > 4 else None
            bse_order_id = parts[3].strip() if len(parts) > 3 else None
            bse_remarks = parts[5].strip() if len(parts) > 5 else message
            success_flag = parts[6].strip() if len(parts) > 6 else ("Y" if status_code == "100" else "N")
            client_code = parts[2].strip() if len(parts) > 2 else None

            success = status_code == "100"

            return {
                "success": success,
                "status_code": status_code,
                "message": message,
                "unique_ref_no": unique_ref_no,
                "bse_order_id": bse_order_id,
                "bse_remarks": bse_remarks,
                "success_flag": success_flag,
                "client_code": client_code
            }
        except Exception as e:
            logger.error(f"Failed to parse BSE order response: {response}. Error: {e}", exc_info=True)
            raise BSEOrderError("Invalid response format received from BSE order API.")

    async def place_lumpsum_order(self, order_data: schemas.LumpsumOrderCreate, encrypted_password: str) -> Dict[str, Any]:
        """
        Places a lumpsum order using the BSE MFOrderEntry service.
        Runs the blocking SOAP call in a separate thread.
        """
        if not encrypted_password:
            raise BSEValidationError("Encrypted password is required for order placement.")

        soap_method_name = "orderEntryParam"  # Replace with actual method name from WSDL
        payload_dict = order_data.model_dump(by_alias=False)
        
        param_string_data = {
            "TransactionCode": payload_dict.get("transaction_code", "NEW"),
            "UniqueRefNo": payload_dict.get("unique_ref_no"),
            "SchemeCode": payload_dict.get("scheme_code"),
            "MemberCode": self.member_id,
            "ClientCode": payload_dict.get("client_code"),
            "UserId": self.user_id,
            "TransactionType": payload_dict.get("transaction_type"),
            "TransactionAmount": str(payload_dict.get("amount", "")), 
            "FolioNo": payload_dict.get("folio_no", ""),
            "BuySell": "P" if payload_dict.get("transaction_type") == "PURCHASE" else "R",
            "BuySellType": "FRESH" if payload_dict.get("transaction_type") == "PURCHASE" else "",
            "DPTxn": "C" if payload_dict.get("dp_txn_mode") == "CDSL" else "N",
            "OrderVal": str(payload_dict.get("amount", "")), 
            "Qty": str(payload_dict.get("quantity", "")), 
            "AllRedeem": "Y" if payload_dict.get("all_units_flag") else "N",
            "MandateID": payload_dict.get("mandate_id", ""),
            "Remarks": payload_dict.get("remarks", ""),
            "KYCStatus": payload_dict.get("kyc_status", "N"),
            "SubberCode": payload_dict.get("sub_broker_code", ""),
            "EUIN": payload_dict.get("euin", ""),
            "EUINVal": "Y" if payload_dict.get("euin_declared") == "Y" else "N",
            "MinRedeem": "Y" if payload_dict.get("min_redeem_flag") else "N",
            "DPC": "Y" if payload_dict.get("dpc_flag") else "N",
            "IPAdd": payload_dict.get("ip_address", ""),
            "Password": encrypted_password,
            "PassKey": payload_dict.get("passkey", ""),
            "Parma1": "", 
            "Parma2": "", 
            "Parma3": ""  
        }
        
        param_order = [
            "TransactionCode", "UniqueRefNo", "SchemeCode", "MemberCode", "ClientCode", "UserId",
            "TransactionType", "TransactionAmount", "BuySell", "BuySellType", "DPTxn", "OrderVal",
            "Qty", "AllRedeem", "FolioNo", "Remarks", "KYCStatus", "SubberCode", "EUIN",
            "EUINVal", "MinRedeem", "DPC", "IPAdd", "Password", "PassKey", 
            "Parma1", "Parma2", "Parma3"
        ]
        param_string = "|".join(str(param_string_data.get(k, "")) for k in param_order)

        request_payload = {
            "Flag": "N",
            "UserId": self.user_id,
            "Password": encrypted_password,
            "Data": param_string
        }

        logger.info(f"Attempting BSE lumpsum order placement for RefNo: {order_data.unique_ref_no}")
        logger.debug(f"BSE Lumpsum Order Payload (before SOAP): {request_payload}")

        try:
            if not hasattr(self.client.service, soap_method_name):
                raise BSEIntegrationError(f"SOAP method {soap_method_name} not found in WSDL {self.wsdl_url}.")

            # Define the blocking call
            def soap_call():
                return self.client.service[soap_method_name](**request_payload)

            # Run the blocking call in a separate thread
            response = await asyncio.to_thread(soap_call)
            logger.debug(f"Raw BSE lumpsum order response: {response}")

            parsed_response = self._parse_order_response(str(response))

            if not parsed_response["success"]:
                logger.warning(f"BSE Lumpsum Order failed: {parsed_response['message']}")
                raise BSEOrderError(f"BSE Lumpsum Order failed: {parsed_response['message']} (Code: {parsed_response['status_code']})")

            logger.info(f"BSE Lumpsum Order successful for RefNo: {order_data.unique_ref_no}. BSE Order ID: {parsed_response.get('bse_order_id')}")
            return parsed_response

        except Fault as e:
            logger.error(f"SOAP fault during lumpsum order: {e}", exc_info=True)
            raise BSESoapFault(f"SOAP fault during lumpsum order: {str(e)}")
        except TransportError as e:
            logger.error(f"Transport error during lumpsum order: {e}", exc_info=True)
            raise BSETransportError(f"Transport error during lumpsum order: {str(e)}")
        except RequestException as e:
            logger.error(f"Network error during lumpsum order: {e}", exc_info=True)
            raise BSETransportError(f"Network error during lumpsum order: {str(e)}")
        except BSEIntegrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during lumpsum order: {e}", exc_info=True)
            raise BSEOrderError(f"Unexpected error during lumpsum order: {str(e)}")

    async def place_sip_order(self, sip_data: schemas.SIPOrderCreate, encrypted_password: str) -> Dict[str, Any]:
        """
        Places an SIP registration order using the BSE MFOrderEntry service.
        Runs the blocking SOAP call in a separate thread.
        """
        if not encrypted_password:
            raise BSEValidationError("Encrypted password is required for SIP order placement.")

        soap_method_name = "sipEntryParam"  # Replace with actual method name from WSDL
        payload_dict = sip_data.model_dump(by_alias=False)

        param_string_data = {
            "TransactionCode": payload_dict.get("transaction_code", "NEWSIP"),
            "UniqueRefNo": payload_dict.get("unique_ref_no"),
            "SchemeCode": payload_dict.get("scheme_code"),
            "MemberCode": self.member_id,
            "ClientCode": payload_dict.get("client_code"),
            "UserId": self.user_id,
            "MandateID": payload_dict.get("mandate_id"),
            "FolioNo": payload_dict.get("folio_no", ""),
            "SIPAmount": str(payload_dict.get("installment_amount", "")), 
            "SIPFrequency": payload_dict.get("frequency", "MONTHLY"),
            "SIPStartDate": payload_dict.get("start_date").strftime("%d/%m/%Y"),
            "SIPInstallments": str(payload_dict.get("no_of_installments", "")), 
            "SIPRegistrationDate": datetime.now().strftime("%d/%m/%Y"),
            "DPTxn": "C" if payload_dict.get("dp_txn_mode") == "CDSL" else "N",
            "Remarks": payload_dict.get("remarks", ""),
            "KYCStatus": payload_dict.get("kyc_status", "N"),
            "SubberCode": payload_dict.get("sub_broker_code", ""),
            "EUIN": payload_dict.get("euin", ""),
            "EUINVal": "Y" if payload_dict.get("euin_declared") == "Y" else "N",
            "IPAdd": payload_dict.get("ip_address", ""),
            "Password": encrypted_password,
            "PassKey": payload_dict.get("passkey", ""),
            "Parma1": "", 
            "Parma2": "", 
            "Parma3": ""  
        }

        param_order = [
            "TransactionCode", "UniqueRefNo", "SchemeCode", "MemberCode", "ClientCode", "UserId",
            "MandateID", "FolioNo", "SIPAmount", "SIPFrequency", "SIPStartDate", "SIPInstallments",
            "SIPRegistrationDate", "DPTxn", "Remarks", "KYCStatus", "SubberCode", "EUIN",
            "EUINVal", "IPAdd", "Password", "PassKey",
            "Parma1", "Parma2", "Parma3"
        ]
        param_string = "|".join(str(param_string_data.get(k, "")) for k in param_order)

        request_payload = {
            "Flag": "N",
            "UserId": self.user_id,
            "Password": encrypted_password,
            "Data": param_string
        }

        logger.info(f"Attempting BSE SIP order placement for RefNo: {sip_data.unique_ref_no}")
        logger.debug(f"BSE SIP Order Payload (before SOAP): {request_payload}")

        try:
            if not hasattr(self.client.service, soap_method_name):
                raise BSEIntegrationError(f"SOAP method {soap_method_name} not found in WSDL {self.wsdl_url}.")

            # Define the blocking call
            def soap_call():
                return self.client.service[soap_method_name](**request_payload)

            # Run the blocking call in a separate thread
            response = await asyncio.to_thread(soap_call)
            logger.debug(f"Raw BSE SIP order response: {response}")

            parsed_response = self._parse_order_response(str(response))
            if "bse_order_id" in parsed_response:
                parsed_response["bse_sip_reg_id"] = parsed_response.pop("bse_order_id")

            if not parsed_response["success"]:
                logger.warning(f"BSE SIP Order failed: {parsed_response['message']}")
                raise BSEOrderError(f"BSE SIP Order failed: {parsed_response['message']} (Code: {parsed_response['status_code']})")

            logger.info(f"BSE SIP Order successful for RefNo: {sip_data.unique_ref_no}. BSE SIP Reg ID: {parsed_response.get('bse_sip_reg_id')}")
            return parsed_response

        except Fault as e:
            logger.error(f"SOAP fault during SIP order: {e}", exc_info=True)
            raise BSESoapFault(f"SOAP fault during SIP order: {str(e)}")
        except TransportError as e:
            logger.error(f"Transport error during SIP order: {e}", exc_info=True)
            raise BSETransportError(f"Transport error during SIP order: {str(e)}")
        except RequestException as e:
            logger.error(f"Network error during SIP order: {e}", exc_info=True)
            raise BSETransportError(f"Network error during SIP order: {str(e)}")
        except BSEIntegrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during SIP order: {e}", exc_info=True)
            raise BSEOrderError(f"Unexpected error during SIP order: {str(e)}")

