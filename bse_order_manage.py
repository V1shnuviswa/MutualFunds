"""
BSE STAR MF System SOAP Message Handlers

This module handles SOAP message construction and parsing for BSE STAR MF System.
Following BSE's WSDL specifications for request/response formats.
"""

from typing import Dict, Any
from xml.etree import ElementTree as ET
from datetime import datetime
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

class SOAPMessageHandler:
    """Handles SOAP message construction and parsing for BSE STAR MF System"""
    
    # BSE STAR MF System demo endpoint URL
    BSE_ENDPOINT = "https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc"
    
    # SOAP namespaces
    NAMESPACES = {
        'soap': 'http://www.w3.org/2003/05/soap-envelope',
        'ns': 'http://www.bsestarmf.in/2016/01/OrderEntry',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    # Required fields for different order types
    PURCHASE_REQUIRED_FIELDS = [
        'TransactionCode', 'UniqueRefNo', 'OrderId', 'UserID', 'MemberId',
        'ClientCode', 'SchemeCode', 'BuySell', 'BuySellType', 'DPTxn',
        'OrderValue', 'KYCStatus', 'DPC', 'IPAdd', 'Password', 'PassKey'
    ]
    
    REDEMPTION_REQUIRED_FIELDS = [
        'TransactionCode', 'UniqueRefNo', 'OrderId', 'UserID', 'MemberId',
        'ClientCode', 'SchemeCode', 'BuySell', 'BuySellType', 'DPTxn',
        'OrderValue', 'KYCStatus', 'DPC', 'IPAdd', 'Password', 'PassKey',
        'FolioNo'
    ]
    
    CANCELLATION_REQUIRED_FIELDS = [
        'OrderNo', 'UserID', 'MemberId', 'ClientCode', 'Password', 'PassKey'
    ]
    
    @classmethod
    def validate_required_fields(cls, params: Dict[str, Any], required_fields: list) -> None:
        """Validate that all required fields are present in params."""
        missing_fields = [field for field in required_fields if field not in params]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    @classmethod
    def create_purchase_request(cls, params: Dict[str, Any]) -> str:
        """
        Create SOAP request for purchase order.
        
        Args:
            params: Order parameters including all required fields:
                - TransactionCode: NEW/MOD/CXL
                - UniqueRefNo: Unique reference number
                - OrderId: Order ID
                - UserID: User ID
                - MemberId: Member ID
                - ClientCode: Client code
                - SchemeCode: Scheme code
                - BuySell: P for Purchase
                - BuySellType: FRESH/SIP
                - DPTxn: P/D (Physical/Demat)
                - OrderValue: Amount
                - KYCStatus: Y/N
                - DPC: Y/N
                - IPAdd: IP Address
                - Password: Password
                - PassKey: PassKey
            
        Returns:
            Formatted SOAP XML request string
        """
        cls.validate_required_fields(params, cls.PURCHASE_REQUIRED_FIELDS)
        
        # Set default values for optional fields
        params.setdefault('AllRedeem', 'N')
        params.setdefault('EUINDecl', 'N')
        params.setdefault('MinRedeem', 'N')
        
        # Create SOAP envelope
        envelope = ET.Element(f"{{{cls.NAMESPACES['soap']}}}Envelope")
        for prefix, uri in cls.NAMESPACES.items():
            envelope.set(f'xmlns:{prefix}', uri)
            
        # Add header and body
        header = ET.SubElement(envelope, f"{{{cls.NAMESPACES['soap']}}}Header")
        body = ET.SubElement(envelope, f"{{{cls.NAMESPACES['soap']}}}Body")
        
        # Add orderEntryParam element
        order_entry = ET.SubElement(body, f"{{{cls.NAMESPACES['ns']}}}orderEntryParam")
        
        # Add parameters
        for key, value in params.items():
            param = ET.SubElement(order_entry, key)
            param.text = str(value)
            
        return ET.tostring(envelope, encoding='unicode', method='xml')
        
    @classmethod
    def create_redemption_request(cls, params: Dict[str, Any]) -> str:
        """
        Create SOAP request for redemption order.
        
        Args:
            params: Order parameters including all required fields:
                - All fields from purchase request plus:
                - FolioNo: Folio number
                - AllRedeem: Y/N for full redemption
            
        Returns:
            Formatted SOAP XML request string
        """
        cls.validate_required_fields(params, cls.REDEMPTION_REQUIRED_FIELDS)
        
        # Set default values for optional fields
        params.setdefault('AllRedeem', 'N')
        params.setdefault('EUINDecl', 'N')
        params.setdefault('MinRedeem', 'N')
        
        # Create SOAP envelope
        envelope = ET.Element(f"{{{cls.NAMESPACES['soap']}}}Envelope")
        for prefix, uri in cls.NAMESPACES.items():
            envelope.set(f'xmlns:{prefix}', uri)
            
        # Add header and body
        header = ET.SubElement(envelope, f"{{{cls.NAMESPACES['soap']}}}Header")
        body = ET.SubElement(envelope, f"{{{cls.NAMESPACES['soap']}}}Body")
        
        # Add orderEntryParam element
        order_entry = ET.SubElement(body, f"{{{cls.NAMESPACES['ns']}}}orderEntryParam")
        
        # Add parameters
        for key, value in params.items():
            param = ET.SubElement(order_entry, key)
            param.text = str(value)
            
        return ET.tostring(envelope, encoding='unicode', method='xml')
        
    @classmethod
    def create_cancellation_request(cls, params: Dict[str, Any]) -> str:
        """
        Create SOAP request for order cancellation.
        
        Args:
            params: Cancellation parameters including:
                - OrderNo: Original order number to cancel
                - UserID: User ID
                - MemberId: Member ID
                - ClientCode: Client code
                - Password: Password
                - PassKey: Passkey
                
        Returns:
            Formatted SOAP XML request string
        """
        cls.validate_required_fields(params, cls.CANCELLATION_REQUIRED_FIELDS)
        
        # Create SOAP envelope
        envelope = ET.Element(f"{{{cls.NAMESPACES['soap']}}}Envelope")
        for prefix, uri in cls.NAMESPACES.items():
            envelope.set(f'xmlns:{prefix}', uri)
            
        # Add header and body
        header = ET.SubElement(envelope, f"{{{cls.NAMESPACES['soap']}}}Header")
        body = ET.SubElement(envelope, f"{{{cls.NAMESPACES['soap']}}}Body")
        
        # Add cancelOrderParam element
        cancel_order = ET.SubElement(body, f"{{{cls.NAMESPACES['ns']}}}cancelOrderParam")
        
        # Add parameters
        for key, value in params.items():
            param = ET.SubElement(cancel_order, key)
            param.text = str(value)
            
        return ET.tostring(envelope, encoding='unicode', method='xml')

    @classmethod
    def parse_order_response(cls, soap_response: str) -> Dict[str, str]:
        """
        Parse SOAP response from BSE.
        
        Args:
            soap_response: SOAP XML response string
            
        Returns:
            Dictionary containing parsed response fields:
            - TransactionCode: Transaction code
            - UniqueRefNo: Unique reference number
            - OrderNumber: BSE order number
            - UserID: User ID
            - MemberId: Member ID
            - ClientCode: Client code
            - BSERemarks: Remarks from BSE
            - SuccessFlag: 1 for success, 0 for failure
        """
        # Parse XML
        root = ET.fromstring(soap_response)
        
        # Find response element in body
        body = root.find(f'.//{{{cls.NAMESPACES["soap"]}}}Body')
        response = body.find(f'.//{{{cls.NAMESPACES["ns"]}}}orderEntryParamResponse')
        
        # Extract fields
        result = {}
        if response is not None:
            for child in response:
                tag = child.tag.split('}')[-1]  # Remove namespace
                result[tag] = child.text
                
        return result
        
    @classmethod
    def parse_cancellation_response(cls, soap_response: str) -> Dict[str, str]:
        """
        Parse SOAP response for order cancellation.
        
        Args:
            soap_response: SOAP XML response string
            
        Returns:
            Dictionary containing parsed response fields:
            - OrderNo: Cancelled order number
            - BSERemarks: Remarks from BSE
            - SuccessFlag: 1 for success, 0 for failure
            - Message: Detailed message
        """
        # Parse XML
        root = ET.fromstring(soap_response)
        
        # Find response element in body
        body = root.find(f'.//{{{cls.NAMESPACES["soap"]}}}Body')
        response = body.find(f'.//{{{cls.NAMESPACES["ns"]}}}cancelOrderParamResponse')
        
        # Extract fields
        result = {}
        if response is not None:
            for child in response:
                tag = child.tag.split('}')[-1]  # Remove namespace
                result[tag] = child.text
                
        return result

    @classmethod
    def send_to_bse(cls, soap_request: str, operation: str) -> dict:
        """
        Send SOAP request to BSE endpoint.
        
        Args:
            soap_request: SOAP XML request
            operation: Operation type for SOAPAction header
            
        Returns:
            Parsed response dictionary
        """
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': f'http://www.bsestarmf.in/2016/01/OrderEntry/{operation}'
        }
        
        try:
            response = requests.post(cls.BSE_ENDPOINT, data=soap_request, headers=headers)
            response.raise_for_status()
            
            if operation == 'cancelOrder':
                return cls.parse_cancellation_response(response.text)
            else:
                return cls.parse_order_response(response.text)
                
        except requests.exceptions.RequestException as e:
            return {
                'SuccessFlag': '0',
                'BSERemarks': f'Error communicating with BSE: {str(e)}'
            }

    @classmethod
    def generate_transaction_number(cls, member_id: str) -> str:
        """Generate unique transaction number in BSE format."""
        date = datetime.now().strftime('%Y%m%d')
        sequence = '000001'  # Should be incremented and managed properly
        return f"{date}-{member_id}-{sequence}"

# Flask Routes
@app.route('/api/order/purchase', methods=['POST'])
def place_purchase_order():
    """Handle purchase order placement."""
    try:
        order_data = request.json
        
        # Add required fields
        order_data.update({
            'TransactionCode': 'NEW',
            'UniqueRefNo': SOAPMessageHandler.generate_transaction_number(order_data['MemberId']),
            'OrderId': '',
            'BuySell': 'P',
            'BuySellType': order_data.get('BuySellType', 'FRESH'),
            'DPTxn': order_data.get('DPTxn', 'P'),
            'DPC': order_data.get('DPC', 'Y'),
            'KYCStatus': order_data.get('KYCStatus', 'Y')
        })
        
        # Create and send SOAP request
        soap_request = SOAPMessageHandler.create_purchase_request(order_data)
        response = SOAPMessageHandler.send_to_bse(soap_request, 'orderEntry')
        
        if response['SuccessFlag'] == '1':
            return jsonify({
                'success': True,
                'order_number': response.get('OrderNumber', ''),
                'message': response.get('BSERemarks', 'Order placed successfully')
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': response.get('BSERemarks', 'Order placement failed')
            }), 400
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/order/redemption', methods=['POST'])
def place_redemption_order():
    """Handle redemption order placement."""
    try:
        order_data = request.json
        
        # Add required fields
        order_data.update({
            'TransactionCode': 'NEW',
            'UniqueRefNo': SOAPMessageHandler.generate_transaction_number(order_data['MemberId']),
            'OrderId': '',
            'BuySell': 'R',
            'BuySellType': order_data.get('BuySellType', 'FRESH'),
            'DPTxn': order_data.get('DPTxn', 'P'),
            'DPC': order_data.get('DPC', 'Y'),
            'KYCStatus': order_data.get('KYCStatus', 'Y'),
            'AllRedeem': order_data.get('AllRedeem', 'N')
        })
        
        # Create and send SOAP request
        soap_request = SOAPMessageHandler.create_redemption_request(order_data)
        response = SOAPMessageHandler.send_to_bse(soap_request, 'orderEntry')
        
        if response['SuccessFlag'] == '1':
            return jsonify({
                'success': True,
                'order_number': response.get('OrderNumber', ''),
                'message': response.get('BSERemarks', 'Order placed successfully')
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': response.get('BSERemarks', 'Order placement failed')
            }), 400
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/order/cancel', methods=['POST'])
def cancel_order():
    """Handle order cancellation."""
    try:
        cancel_data = request.json
        
        # Create and send cancellation request
        soap_request = SOAPMessageHandler.create_cancellation_request(cancel_data)
        response = SOAPMessageHandler.send_to_bse(soap_request, 'cancelOrder')
        
        if response['SuccessFlag'] == '1':
            return jsonify({
                'success': True,
                'order_number': response.get('OrderNo', ''),
                'message': response.get('Message', 'Order cancelled successfully')
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': response.get('Message', 'Order cancellation failed')
            }), 400
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/order/status', methods=['GET'])
def get_order_status():
    """Get order status by order number."""
    order_no = request.args.get('order_no')
    if not order_no:
        return jsonify({
            'success': False,
            'message': 'Order number is required'
        }), 400
        
    # Add implementation for order status check
    # This would typically involve another SOAP call to BSE
    
    return jsonify({
        'success': True,
        'order_number': order_no,
        'status': 'PENDING'  # Replace with actual status from BSE
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000) 