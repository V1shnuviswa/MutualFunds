# /home/ubuntu/order_management_system/src/bse_integration/config.py

from pydantic_settings import BaseSettings
import os

# Load .env file if it exists (for local development)
# from dotenv import load_dotenv
# load_dotenv()

class BSESettings(BaseSettings):
    # Authentication settings
    BSE_USER_ID: str = "1809801"  # Default from reference
    BSE_PASSWORD: str = "0123456"  # Default from reference
    BSE_MEMBER_CODE: str = "10000"  # Default from reference
    BSE_PASSKEY: str = "PassKey123"  # Default passkey

    # Base URLs and Paths
    BSE_BASE_URL: str = "https://bsestarmfdemo.bseindia.com/StarMFCommonAPI"
    BSE_REGISTRATION_PATH: str = "/ClientMaster/Registration"

    # WSDL URLs
    BSE_ORDER_ENTRY_WSDL: str = "https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl"
    BSE_AUTH_WSDL: str = "https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl"

    # SOAP Namespaces
    BSE_SOAP_NS: str = "http://www.w3.org/2003/05/soap-envelope"
    BSE_STAR_MF_NS: str = "http://bsestarmf.in/"
    BSE_ADDRESSING_NS: str = "http://www.w3.org/2005/08/addressing"

    # Timeouts and Limits
    BSE_SESSION_TIMEOUT: int = 3600  # 1 hour
    BSE_REQUEST_TIMEOUT: int = 30  # 30 seconds
    BSE_MAX_RETRIES: int = 3

    # Order Settings
    BSE_DEFAULT_DPC: str = "Y"
    BSE_DEFAULT_EUIN_FLAG: str = "N"
    BSE_DEFAULT_MIN_REDEEM: str = "N"
    BSE_DEFAULT_ALL_UNITS: str = "N"
    BSE_DEFAULT_FIRST_ORDER: str = "N"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Instantiate settings
bse_settings = BSESettings()

