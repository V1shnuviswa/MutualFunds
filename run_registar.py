# run_registrar.py
import asyncio
from registrar import BSEClientRegistrar, _convert_to_bse_format
from database import SessionLocal
from crud import get_client_and_state

async def test_registration():
    db = SessionLocal()
    client_code = "CL123456"

    client, state = get_client_and_state(db, client_code)
    if not client or not state:
        print("Client not found.")
        return

    registrar = BSEClientRegistrar()
    payload = _convert_to_bse_format(client, state)
    print("Payload:", payload)

    response = await registrar.register_client(payload)
    print("Response:", response)

asyncio.run(test_registration())
