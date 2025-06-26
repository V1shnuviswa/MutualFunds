import asyncio
import json
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_place_sip_order():
    async with AsyncClient(base_url="http://testserver") as ac:
        sip_order_payload = {
            "transaction_code": "NEW",
            "unique_ref_no": "SIPREF123456",
            "scheme_code": "SCHEME001",
            "client_code": "CLIENT789",
            "installment_amount": 1000.00,
            "mandate_id": "MANDATE123",
            "start_date": "2024-07-01",
            "frequency_type": "M",  # Monthly
            "frequency_allowed": 12,
            "no_of_installments": 12,
            "folio_no": "",
            "first_order_today": True,
            "sub_broker_arn": "",
            "euin": "",
            "euin_declaration": False,
            "dpc_flag": False,
            "ip_address": "192.168.1.1",
            "brokerage": 0,
            "remarks": "Test SIP order",
            "kyc_status": "Y"
        }
        response = await ac.post("/api/v1/orders/sip", json=sip_order_payload)
        print("Response status code:", response.status_code)
        print("Response JSON:", response.json())
        assert response.status_code == 200
        assert "status" in response.json()
