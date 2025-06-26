import logging
from zeep import Client
from zeep.exceptions import Fault

# === CONFIG ===
BSE_USER_ID = "6385101"
BSE_PASSWORD = "Abc@1234"
BSE_MEMBER_ID = "63851"
BSE_PASSKEY = "Passkey123"
CLIENT_CODE = "0000000002"
ORDER_NO = "1911336232"
SEGMENT = "M"  # Use 'M' for Mutual Fund, 'SGB' for Sovereign Gold Bonds

# === WSDL URL ===
WSDL_URL = "https://bsestarmfdemo.bseindia.com/MFUploadService/MFUploadService.svc?wsdl"

# === Logging setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Custom error class ===
class BSEIntegrationError(Exception):
    pass

# === Function to get encrypted password ===
def get_encrypted_password(auth_client: Client, password: str, passkey: str) -> str:
    """Authenticates with BSE to get an encrypted password."""
    logger.info("Authenticating with BSE STAR MF to get encrypted password.")
    try:
        logger.debug(f"Sending password encryption request with:")
        logger.debug(f"UserId: {BSE_USER_ID}")
        logger.debug(f"Password: {'*' * len(password)}")
        logger.debug(f"PassKey: {passkey}")

        encrypted_response = auth_client.service.getPassword(
            UserId=BSE_USER_ID,
            Password=password,
            PassKey=passkey
        )

        logger.debug(f"Raw encrypted password response: {encrypted_response}")

        if '|' in str(encrypted_response):
            status, encrypted_pwd = str(encrypted_response).split('|', 1)
            logger.debug(f"Split response - Status: {status}, Password length: {len(encrypted_pwd)}")

            if status == '100':
                logger.info("Password encryption successful")
                return encrypted_pwd.strip()
            else:
                raise BSEIntegrationError(f"Password encryption failed with status: {status}")

        logger.warning("Response did not contain expected '|' separator")
        return str(encrypted_response).strip()

    except Fault as e:
        logger.error(f"SOAP Fault during getPassword: {e}", exc_info=True)
        raise BSEIntegrationError(f"Authentication failed: {str(e.message)}")
    except Exception as e:
        logger.error(f"Error getting encrypted password: {e}", exc_info=True)
        raise BSEIntegrationError(f"Authentication failed: {str(e)}")

# === Main script logic ===
if __name__ == "__main__":
    try:
        # Step 1: Create SOAP client
        client = Client(WSDL_URL)

        # Step 2: Get encrypted password
        encrypted_password = get_encrypted_password(client, BSE_PASSWORD, BSE_PASSKEY)

        # Step 3: Call MFAPI with Flag 11 (Client Order Payment Status)
        response = client.service.MFAPI(
            Flag="11",
            UserId=BSE_USER_ID,
            EncryptedPassword=encrypted_password,
            Param=f"{CLIENT_CODE}|{ORDER_NO}|{SEGMENT}"
        )

        # Step 4: Print raw response from BSE
        print(response)

    except Exception as e:
        logger.error(f"Failed to fetch payment status: {e}", exc_info=True)
