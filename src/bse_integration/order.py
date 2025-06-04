# /home/ubuntu/order_management_system/src/bse_integration/order.py

"""
BSE STAR MF Order Management System

This module handles all types of orders (Lumpsum, SIP, Switch, Spread) with BSE STAR MF using SOAP.
Supports order operations: Buy, Sell, Modify, Cancel and Status tracking.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass
from xml.etree import ElementTree as ET

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

@dataclass
class OrderResponse:
    """Standard response format for all order types"""
    success: bool
    order_id: str
    message: str
    status_code: str
    details: Dict[str, Any]

    @classmethod
    def from_pipe_separated(cls, response_text: str) -> 'OrderResponse':
        """Parse pipe-separated BSE response into standard format"""
        parts = [part.strip() for part in response_text.split('|')]
        if len(parts) < 4:
            raise ValueError(f"Invalid response format: {response_text}")
            
        return cls(
            success=parts[0] == "100",
            order_id=parts[2] if len(parts) > 2 else "",
            message=parts[1],
            status_code=parts[0],
            details={
                "client_code": parts[3] if len(parts) > 3 else "",
                "bse_remarks": parts[4] if len(parts) > 4 else "",
                "success_flag": parts[5] if len(parts) > 5 else "Y" if parts[0] == "100" else "N"
            }
        )

class BSEOrderPlacer:
    """
    Handles all types of orders with BSE STAR MF using SOAP.
    Supports: Lumpsum, SIP, Switch, Spread orders with all operations.
    """

    def __init__(self) -> None:
        """Initialize BSE Order Placer with SOAP client"""
        self.wsdl_url = bse_settings.BSE_ORDER_ENTRY_WSDL
        self.user_id = bse_settings.BSE_USER_ID
        self.member_id = bse_settings.BSE_MEMBER_CODE

        if not self.wsdl_url:
            raise BSEIntegrationError("BSE_ORDER_ENTRY_WSDL is not configured.")
        if not self.user_id or not self.member_id:
             raise BSEIntegrationError("BSE User ID or Member ID not configured.")

        # Initialize SOAP client
        try:
            session = Session()
            transport = Transport(session=session)
            self.client = Client(self.wsdl_url, transport=transport)
            logger.info(f"Initialized SOAP client for BSE Order Entry service")
        except Exception as e:
            logger.error(f"Failed to initialize SOAP client: {e}", exc_info=True)
            raise BSEIntegrationError(f"WSDL initialization failed: {str(e)}")

    def _create_soap_envelope(self, action: str, method: str) -> ET.Element:
        """Create SOAP envelope with proper headers"""
        envelope = ET.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope")
        envelope.set("xmlns:soap", "http://www.w3.org/2003/05/soap-envelope")
        envelope.set("xmlns:bses", "http://bsestarmf.in/")
        
        header = ET.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Header")
        header.set("xmlns:wsa", "http://www.w3.org/2005/08/addressing")
        
        action_elem = ET.SubElement(header, "{http://www.w3.org/2005/08/addressing}Action")
        action_elem.text = f"http://bsestarmf.in/MFOrderEntry/{action}"
        
        to = ET.SubElement(header, "{http://www.w3.org/2005/08/addressing}To")
        to.text = "https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc/Secure"
        
        return envelope

    async def _send_soap_request(self, soap_method: str, params: Dict[str, Any]) -> OrderResponse:
        """Send SOAP request to BSE and parse response"""
        try:
            if not hasattr(self.client.service, soap_method):
                raise BSEIntegrationError(f"SOAP method {soap_method} not found")

            def soap_call():
                return getattr(self.client.service, soap_method)(**params)

            response = await asyncio.to_thread(soap_call)
            logger.debug(f"BSE Response: {response}")
            
            return OrderResponse.from_pipe_separated(str(response))

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
            raise BSEOrderError(f"Unexpected error: {str(e)}")

    async def place_lumpsum_order(self, order_data: schemas.LumpsumOrderCreate, encrypted_password: str) -> OrderResponse:
        """Place lumpsum order (Purchase/Redemption)"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        # Prepare parameters
        params = {
            "TransCode": "NEW",
            "TransNo": order_data.unique_ref_no,
            "OrderId": "",
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": order_data.client_code,
            "SchemeCd": order_data.scheme_code,
            "BuySell": "P" if order_data.transaction_type == "PURCHASE" else "R",
            "BuySellType": "FRESH" if order_data.transaction_type == "PURCHASE" else "",
            "DPTxn": "C" if order_data.dp_txn_mode == "CDSL" else "N",
            "OrderVal": str(order_data.amount or ""),
            "Qty": str(order_data.quantity or ""),
            "AllRedeem": "Y" if order_data.all_units_flag else "N",
            "FolioNo": order_data.folio_no or "",
            "KYCStatus": order_data.kyc_status or "N",
            "MinRedeem": "Y" if order_data.min_redeem_flag else "N",
            "DPC": "Y" if order_data.dpc_flag else "N",
            "Password": encrypted_password
        }

        logger.info(f"Placing {order_data.transaction_type} order for {order_data.unique_ref_no}")
        return await self._send_soap_request("orderEntryParam", params)

    async def place_sip_order(self, sip_data: schemas.SIPOrderCreate, encrypted_password: str) -> OrderResponse:
        """Place new SIP registration order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        params = {
            "TransCode": "NEWSIP",
            "TransNo": sip_data.unique_ref_no,
            "SchemeCode": sip_data.scheme_code,
            "MemberCode": self.member_id,
            "ClientCode": sip_data.client_code,
            "UserID": self.user_id,
            "TransMode": sip_data.transaction_mode,
            "DpTxnMode": "C" if sip_data.dp_txn_mode == "CDSL" else "N",
            "StartDate": sip_data.start_date.strftime("%d/%m/%Y"),
            "FrequencyType": sip_data.frequency,
            "FrequencyAllowed": "1",
            "InstallmentAmount": str(sip_data.amount),
            "NoOfInstallment": str(sip_data.installments or ""),
            "FolioNo": sip_data.folio_no or "",
            "FirstOrderFlag": sip_data.first_order_today,
            "MandateID": sip_data.mandate_id or "",
            "Password": encrypted_password
        }

        logger.info(f"Registering SIP for {sip_data.unique_ref_no}")
        return await self._send_soap_request("sipOrderEntryParam", params)

    async def modify_sip_order(self, sip_data: schemas.SIPOrderModify, encrypted_password: str) -> OrderResponse:
        """Modify existing SIP registration"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        params = {
            "TransCode": "MODSIP",
            "TransNo": sip_data.unique_ref_no,
            "RegId": sip_data.sip_reg_id,
            "MemberCode": self.member_id,
            "ClientCode": sip_data.client_code,
            "UserID": self.user_id,
            "Amount": str(sip_data.new_amount),
            "NoOfInstallment": str(sip_data.new_installments or ""),
            "Password": encrypted_password
        }

        logger.info(f"Modifying SIP {sip_data.sip_reg_id}")
        return await self._send_soap_request("modifySipOrderParam", params)

    async def cancel_sip_order(self, sip_reg_id: str, client_code: str, encrypted_password: str) -> OrderResponse:
        """Cancel SIP registration"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        params = {
            "TransCode": "CXLSIP",
            "TransNo": f"CXL{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "RegId": sip_reg_id,
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

        logger.info(f"Cancelling SIP {sip_reg_id}")
        return await self._send_soap_request("cancelSipOrderParam", params)

    async def place_switch_order(self, switch_data: schemas.SwitchOrderCreate, encrypted_password: str) -> OrderResponse:
        """Place switch order between schemes"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        params = {
            "TransCode": "NEW",
            "TransNo": switch_data.unique_ref_no,
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": switch_data.client_code,
            "FromSchemeCd": switch_data.from_scheme_code,
            "ToSchemeCd": switch_data.to_scheme_code,
            "BuySell": "SO",  # Switch Out
            "DPTxn": "C" if switch_data.dp_txn_mode == "CDSL" else "N",
            "SwitchAmount": str(switch_data.amount or ""),
            "SwitchUnits": str(switch_data.units or ""),
            "AllUnitsFlag": "Y" if switch_data.all_units_flag else "N",
            "FolioNo": switch_data.folio_no or "",
            "Password": encrypted_password
        }

        logger.info(f"Placing switch order for {switch_data.unique_ref_no}")
        return await self._send_soap_request("switchOrderEntryParam", params)

    async def place_spread_order(self, spread_data: schemas.SpreadOrderCreate, encrypted_password: str) -> OrderResponse:
        """Place spread order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        params = {
            "TransCode": "NEW",
            "TransNo": spread_data.unique_ref_no,
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": spread_data.client_code,
            "SchemeCd": spread_data.scheme_code,
            "BuySell": spread_data.buy_sell,
            "DPTxn": "C" if spread_data.dp_txn_mode == "CDSL" else "N",
            "PurchaseAmount": str(spread_data.purchase_amount or ""),
            "RedemptionAmount": str(spread_data.redemption_amount or ""),
            "AllUnitsFlag": "Y" if spread_data.all_units_flag else "N",
            "RedeemDate": spread_data.redeem_date.strftime("%d/%m/%Y"),
            "FolioNo": spread_data.folio_no or "",
            "Password": encrypted_password
        }

        logger.info(f"Placing spread order for {spread_data.unique_ref_no}")
        return await self._send_soap_request("spreadOrderEntryParam", params)

    async def cancel_order(self, order_id: str, client_code: str, encrypted_password: str) -> OrderResponse:
        """Cancel any type of order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

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

    async def get_order_status(self, order_id: str, client_code: str, encrypted_password: str) -> OrderResponse:
        """Get status of any order"""
        if not encrypted_password:
            raise BSEValidationError("Encrypted password required")

        params = {
            "OrderNo": order_id,
            "UserID": self.user_id,
            "MemberId": self.member_id,
            "ClientCode": client_code,
            "Password": encrypted_password
        }

        logger.info(f"Checking status for order {order_id}")
        return await self._send_soap_request("getOrderStatus", params)

