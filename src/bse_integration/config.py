# /home/ubuntu/order_management_system/src/bse_integration/config.py

from pydantic_settings import BaseSettings
import os

# Load .env file if it exists (for local development)
# from dotenv import load_dotenv
# load_dotenv()

class BSESettings(BaseSettings):
    BSE_USER_ID: str = "1809801" # Default from reference, should be overridden by env
    BSE_PASSWORD: str = "0123456" # Default from reference, should be overridden by env
    BSE_MEMBER_CODE: str = "10000" # Default from reference, should be overridden by env

    # Base URL and Paths (matching reference config.py)
    BSE_BASE_URL: str = "https://bsestarmfdemo.bseindia.com/StarMFCommonAPI"
    BSE_REGISTRATION_PATH: str = "/ClientMaster/Registration"

    # WSDL URLs (Order Entry and Auth still use WSDL)
    BSE_ORDER_ENTRY_WSDL: str = "https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl"
    BSE_AUTH_WSDL: str = "https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl" # Auth seems to use Order Entry WSDL

    BSE_SESSION_TIMEOUT: int = 3600 # Default 1 hour

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # Ignore extra environment variables

# Instantiate settings
bse_settings = BSESettings()

