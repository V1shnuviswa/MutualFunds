# /home/ubuntu/bse_test_connectivity.py

import logging
import sys

# Add project src to path to import config (adjust path if needed)
sys.path.append("/home/ubuntu/order_management_system")

from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from requests import Session
from requests.exceptions import RequestException

# Try importing settings, handle if it fails
try:
    from src.bse_integration.config import bse_settings
    USER_ID = bse_settings.BSE_USER_ID
    PASSWORD = bse_settings.BSE_PASSWORD
    WSDL_URL = bse_settings.BSE_AUTH_WSDL
except ImportError:
    print("Could not import settings, using hardcoded defaults.")
    USER_ID = "1809801" # Default from reference
    PASSWORD = "0123456" # Default from reference
    WSDL_URL = "https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl"

# Hardcoded passkey for testing
PASSKEY = "PassKey123" 

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_bse_authentication():
    logger.info(f"Attempting to connect to BSE Auth WSDL: {WSDL_URL}")
    
    try:
        # Initialize SOAP client
        session = Session()
        transport = Transport(session=session)
        client = Client(WSDL_URL, transport=transport)
        logger.info("Zeep client initialized successfully.")

        # Prepare request data
        request_data = {
            "UserId": USER_ID,
            "Password": PASSWORD,
            "PassKey": PASSKEY
        }
        logger.info(f"Attempting to call getPassword with UserID: {USER_ID}")
        
        # Make the SOAP call (synchronous)
        response = client.service.getPassword(**request_data)
        logger.info(f"Raw BSE getPassword response received:")
        print(f"""--- RESPONSE START ---
{response}
--- RESPONSE END ---""")

        # Basic response parsing (similar to authenticator)
        parts = str(response).split("|")
        response_code = parts[0].strip()
        if response_code == "100":
            logger.info("Authentication successful (Code 100).")
            encrypted_pass = parts[1].strip() if len(parts) > 1 else None
            if encrypted_pass:
                 logger.info(f"Received encrypted password: {encrypted_pass[:5]}...{encrypted_pass[-5:]}") # Log partial password
            else:
                 logger.warning("Authentication successful but no encrypted password received.")
        else:
            error_message = parts[1].strip() if len(parts) > 1 else "Unknown error"
            logger.error(f"Authentication failed. Code: {response_code}, Message: {error_message}")

    except Fault as e:
        logger.error(f"SOAP Fault occurred: {e}", exc_info=True)
    except TransportError as e:
        logger.error(f"Transport Error occurred: {e}", exc_info=True)
    except RequestException as e:
        logger.error(f"Network Error occurred: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    test_bse_authentication()

