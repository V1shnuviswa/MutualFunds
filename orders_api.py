from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET



app = Flask(__name__)

# Endpoints
BSE_BASE_URL = "https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc"
AUTH_URL = "https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc/Secure"

# Temporary data storage
orders = {}
sips = {}
holdings = []
instruments = []

# Helper functions for SOAP Requests
def authenticate(user_id, password, passkey):
    auth_request = f"""
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
        <soap:Body>
            <bses:getPassword xmlns:bses="http://bsestarmf.in/">
                <bses:UserId>{user_id}</bses:UserId>
                <bses:Password>{password}</bses:Password>
                <bses:PassKey>{passkey}</bses:PassKey>
            </bses:getPassword>
        </soap:Body>
    </soap:Envelope>
    """
    try:
        response = requests.post(AUTH_URL, data=auth_request, headers={'Content-Type': 'application/soap+xml'})
        response.raise_for_status()
        tree = ET.fromstring(response.content)
        result = tree.find('.//{http://bsestarmf.in/}getPasswordResult').text
        if result.startswith("100|"):
            return result.split("|")[1]  # Extract and return the session token
        else:
            return None, "Authentication failed"
    except requests.RequestException as e:
        return None, f"Authentication request failed: {str(e)}"

def send_soap_request(xml_request):
    try:
        response = requests.post(BSE_BASE_URL, data=xml_request, headers={'Content-Type': 'application/soap+xml'})
        response.raise_for_status()
        return response.content, None
    except requests.RequestException as e:
        return None, str(e)

# SOAP request for placing buy/sell orders
def create_order_soap_request(order_type, member_id, client_code, scheme_code, amount, session_token, passkey):
    buy_sell = "P" if order_type == "buy" else "R"
    return f"""
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
        <soap:Body>
            <bses:orderEntryParam xmlns:bses="http://bsestarmf.in/">
                <bses:TransCode>NEW</bses:TransCode>
                <bses:MemberId>{member_id}</bses:MemberId>
                <bses:ClientCode>{client_code}</bses:ClientCode>
                <bses:SchemeCd>{scheme_code}</bses:SchemeCd>
                <bses:BuySell>{buy_sell}</bses:BuySell>
                <bses:OrderVal>{amount}</bses:OrderVal>
                <bses:Password>{session_token}</bses:Password>
                <bses:PassKey>{passkey}</bses:PassKey>
            </bses:orderEntryParam>
        </soap:Body>
    </soap:Envelope>
    """

# SOAP request for canceling an order
def create_cancel_order_soap_request(order_id, member_id, session_token, passkey):
    return f"""
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
        <soap:Body>
            <bses:orderCancelParam xmlns:bses="http://bsestarmf.in/">
                <bses:OrderId>{order_id}</bses:OrderId>
                <bses:MemberId>{member_id}</bses:MemberId>
                <bses:Password>{session_token}</bses:Password>
                <bses:PassKey>{passkey}</bses:PassKey>
            </bses:orderCancelParam>
        </soap:Body>
    </soap:Envelope>
    """

# SOAP request for placing a SIP order
def create_sip_soap_request(member_id, client_code, scheme_code, amount, frequency, session_token, passkey):
    return f"""
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
        <soap:Body>
            <bses:sipOrderEntryParam xmlns:bses="http://bsestarmf.in/">
                <bses:TransCode>NEW</bses:TransCode>
                <bses:MemberId>{member_id}</bses:MemberId>
                <bses:ClientCode>{client_code}</bses:ClientCode>
                <bses:SchemeCd>{scheme_code}</bses:SchemeCd>
                <bses:InstallmentAmount>{amount}</bses:InstallmentAmount>
                <bses:FrequencyType>{frequency}</bses:FrequencyType>
                <bses:Password>{session_token}</bses:Password>
                <bses:PassKey>{passkey}</bses:PassKey>
            </bses:sipOrderEntryParam>
        </soap:Body>
    </soap:Envelope>
    """

# SOAP request for modifying a SIP order
def create_modify_sip_soap_request(sip_id, amount, frequency, session_token, passkey):
    return f"""
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
        <soap:Body>
            <bses:sipOrderModifyParam xmlns:bses="http://bsestarmf.in/">
                <bses:SIPId>{sip_id}</bses:SIPId>
                <bses:InstallmentAmount>{amount}</bses:InstallmentAmount>
                <bses:FrequencyType>{frequency}</bses:FrequencyType>
                <bses:Password>{session_token}</bses:Password>
                <bses:PassKey>{passkey}</bses:PassKey>
            </bses:sipOrderModifyParam>
        </soap:Body>
    </soap:Envelope>
    """

# SOAP request for canceling a SIP order
def create_cancel_sip_soap_request(sip_id, session_token, passkey):
    return f"""
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
        <soap:Body>
            <bses:sipOrderCancelParam xmlns:bses="http://bsestarmf.in/">
                <bses:SIPId>{sip_id}</bses:SIPId>
                <bses:Password>{session_token}</bses:Password>
                <bses:PassKey>{passkey}</bses:PassKey>
            </bses:sipOrderCancelParam>
        </soap:Body>
    </soap:Envelope>
    """

# 1. POST /mf/orders - Place a buy or sell order
@app.route('/mf/orders', methods=['POST'])
def place_order():
    data = request.json
    required_fields = ['user_id', 'password', 'passkey', 'member_id', 'client_code', 'scheme_code', 'amount', 'type']

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    session_token, auth_error = authenticate(data['user_id'], data['password'], data['passkey'])
    if auth_error:
        return jsonify({'error': auth_error}), 401

    order_type = data['type']  # buy or sell
    soap_request = create_order_soap_request(order_type, data['member_id'], data['client_code'], data['scheme_code'], data['amount'], session_token, data['passkey'])

    response_content, error = send_soap_request(soap_request)
    if error:
        return jsonify({'error': error}), 500

    tree = ET.fromstring(response_content)
    result = tree.find('.//{http://bsestarmf.in/}orderEntryParamResult').text
    if "ORD CONF" in result:
        return jsonify({'message': 'Order placed successfully', 'details': result}), 201
    else:
        return jsonify({'error': 'Order placement failed', 'details': result}), 500

# 2. DELETE /mf/orders/:order_id - Cancel an open or pending order
@app.route('/mf/orders/<order_id>', methods=['DELETE'])
def cancel_order(order_id):
    data = request.json
    session_token, auth_error = authenticate(data['user_id'], data['password'], data['passkey'])
    if auth_error:
        return jsonify({'error': auth_error}), 401

    soap_request = create_cancel_order_soap_request(order_id, data['member_id'], session_token, data['passkey'])

    response_content, error = send_soap_request(soap_request)
    if error:
        return jsonify({'error': error}), 500

    tree = ET.fromstring(response_content)
    result = tree.find('.//{http://bsestarmf.in/}orderCancelParamResult').text
    if "CANCEL CONF" in result:
        return jsonify({'message': 'Order cancelled successfully', 'details': result}), 200
    else:
        return jsonify({'error': 'Order cancellation failed', 'details': result}), 500

# 3. GET /mf/orders - Retrieve all orders (open and executed) over the last 7 days
@app.route('/mf/orders', methods=['GET'])
def list_orders():
    last_week = datetime.now() - timedelta(days=7)
    recent_orders = [order for order in orders.values() if order['created_at'] >= last_week]
    return jsonify(recent_orders), 200

# 4. GET /mf/orders/:order_id - Retrieve an individual order
@app.route('/mf/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    order = orders.get(order_id)
    if order:
        return jsonify(order), 200
    return jsonify({'error': 'Order not found'}), 404

# 5. POST /mf/sips - Place a SIP order
@app.route('/mf/sips', methods=['POST'])
def place_sip():
    data = request.json
    required_fields = ['user_id', 'password', 'passkey', 'member_id', 'client_code', 'scheme_code', 'amount', 'frequency']

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    session_token, auth_error = authenticate(data['user_id'], data['password'], data['passkey'])
    if auth_error:
        return jsonify({'error': auth_error}), 401

    soap_request = create_sip_soap_request(data['member_id'], data['client_code'], data['scheme_code'], data['amount'], data['frequency'], session_token, data['passkey'])

    response_content, error = send_soap_request(soap_request)
    if error:
        return jsonify({'error': error}), 500

    tree = ET.fromstring(response_content)
    result = tree.find('.//{http://bsestarmf.in/}sipOrderEntryParamResult').text
    if "ORD CONF" in result:
        return jsonify({'message': 'SIP placed successfully', 'details': result}), 201
    else:
        return jsonify({'error': 'SIP placement failed', 'details': result}), 500

# 6. PUT /mf/sips/:order_id - Modify an open SIP order
@app.route('/mf/sips/<sip_id>', methods=['PUT'])
def modify_sip(sip_id):
    data = request.json
    session_token, auth_error = authenticate(data['user_id'], data['password'], data['passkey'])
    if auth_error:
        return jsonify({'error': auth_error}), 401

    soap_request = create_modify_sip_soap_request(sip_id, data['amount'], data['frequency'], session_token, data['passkey'])

    response_content, error = send_soap_request(soap_request)
    if error:
        return jsonify({'error': error}), 500

    tree = ET.fromstring(response_content)
    result = tree.find('.//{http://bsestarmf.in/}sipOrderModifyParamResult').text
    if "MODIFY CONF" in result:
        return jsonify({'message': 'SIP modified successfully', 'details': result}), 200
    else:
        return jsonify({'error': 'SIP modification failed', 'details': result}), 500

# 7. DELETE /mf/sips/:order_id - Cancel an open SIP order
@app.route('/mf/sips/<sip_id>', methods=['DELETE'])
def cancel_sip(sip_id):
    data = request.json
    session_token, auth_error = authenticate(data['user_id'], data['password'], data['passkey'])
    if auth_error:
        return jsonify({'error': auth_error}), 401

    soap_request = create_cancel_sip_soap_request(sip_id, session_token, data['passkey'])

    response_content, error = send_soap_request(soap_request)
    if error:
        return jsonify({'error': error}), 500

    tree = ET.fromstring(response_content)
    result = tree.find('.//{http://bsestarmf.in/}sipOrderCancelParamResult').text
    if "CANCEL CONF" in result:
        return jsonify({'message': 'SIP cancelled successfully', 'details': result}), 200
    else:
        return jsonify({'error': 'SIP cancellation failed', 'details': result}), 500

# 8. GET /mf/sips - Retrieve the list of all open SIP orders
@app.route('/mf/sips', methods=['GET'])
def list_sips():
    open_sips = [sip for sip in sips.values() if sip['status'] == 'open']
    return jsonify(open_sips), 200

# 9. GET /mf/sips/:order_id - Retrieve an individual SIP order
@app.route('/mf/sips/<sip_id>', methods=['GET'])
def get_sip(sip_id):
    sip = sips.get(sip_id)
    if sip:
        return jsonify(sip), 200
    return jsonify({'error': 'SIP not found'}), 404

# 10. GET /mf/holdings - Retrieve the list of mutual fund holdings available in DEMAT
@app.route('/mf/holdings', methods=['GET'])
def get_holdings():
    return jsonify(holdings), 200

# 11. GET /mf/instruments - Retrieve the master list of all mutual funds available on the platform
@app.route('/mf/instruments', methods=['GET'])
def get_instruments():
    return jsonify(instruments), 200

# Initialize some dummy data for holdings and instruments
@app.before_first_request
def setup_dummy_data():
    global holdings, instruments
    holdings = [
        {'scheme_code': '01-AB', 'units': 100.50, 'value': 1500},
        {'scheme_code': '02-CD', 'units': 50.75, 'value': 1200}
    ]
    instruments = [
        {'scheme_code': '01-AB', 'scheme_name': 'Fund ABC', 'type': 'Equity'},
        {'scheme_code': '02-CD', 'scheme_name': 'Fund DEF', 'type': 'Debt'},
        {'scheme_code': '03-EF', 'scheme_name': 'Fund XYZ', 'type': 'Balanced'},
    ]

if __name__ == '__main__':
    app.run(debug=True)
