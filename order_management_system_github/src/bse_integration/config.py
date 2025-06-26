# /home/ubuntu/order_management_system/src/bse_integration/config.py

"""BSE STAR MF Integration Configuration

This module contains all configuration settings for BSE STAR MF integration.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skipping .env load
    pass

class BSESettings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"
    )

    # Authentication settings
    BSE_USER_ID: str = "6385101"  # Updated with actual credentials
    BSE_PASSWORD: str = "Abc@1234"  # Updated with actual credentials
    BSE_MEMBER_CODE: str = "63851"  # Updated with actual credentials
    BSE_PASSKEY: str = "PassKey123"  # Default passkey

    # Base URLs and Paths
    BSE_BASE_URL: str = "https://bsestarmfdemo.bseindia.com/StarMFCommonAPI"
    BSE_REGISTRATION_PATH: str = "/ClientMaster/Registration"
    
    # Common API settings
    common_api: str = Field(
        default="https://bsestarmfdemo.bseindia.com/StarMFCommonAPI",
        description="Base URL for BSE STAR MF Common API"
    )
    BSE_UCC_BASE_URL: str = Field(
        default="https://bsestarmfdemo.bseindia.com/BSEMFWEBAPI",
        description="Base URL for UCC Registration"
    )
    BSE_UCC_REGISTER_URL: str = Field(
        default="https://bsestarmfdemo.bseindia.com/BSEMFWEBAPI/UCCAPI/UCCRegistrationV183",
        description="Full URL for UCC Registration API"
    )
    CLIENT_REGISTRATION: str = Field(
        default="/UCCAPI/UCCRegistrationV183",
        description="Client registration endpoint path"
    )

    # WSDL URLs - Updated with correct format based on working tests
    BSE_ORDER_ENTRY_BASE: str = Field(
        default="https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc",
        description="Base URL for order entry service"
    )
    BSE_ORDER_ENTRY_WSDL: str = Field(
        default="https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl",
        description="WSDL URL for order entry service"
    )
    BSE_ORDER_ENTRY_SECURE: str = Field(
        default="https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc/Secure",
        description="Secure endpoint for order entry service"
    )
    
    BSE_UPLOAD_BASE: str = Field(
        default="https://bsestarmfdemo.bseindia.com/MFUploadService/MFUploadService.svc",
        description="Base URL for file upload service"
    )
    BSE_UPLOAD_WSDL: str = Field(
        default="https://bsestarmfdemo.bseindia.com/MFUploadService/MFUploadService.svc?wsdl",
        description="WSDL URL for file upload service"
    )
    BSE_UPLOAD_SECURE: str = Field(
        default="https://bsestarmfdemo.bseindia.com/MFUploadService/MFUploadService.svc/Secure",
        description="Secure endpoint for file upload service"
    )
    
    BSE_PRICE_BASE: str = Field(
        default="https://bsestarmfdemo.bseindia.com/StarMFWebService/StarMFWebService.svc",
        description="Base URL for price service"
    )
    BSE_PRICE_WSDL: str = Field(
        default="https://bsestarmfdemo.bseindia.com/StarMFWebService/StarMFWebService.svc?wsdl",
        description="WSDL URL for price service"
    )
    BSE_PRICE_SECURE: str = Field(
        default="https://bsestarmfdemo.bseindia.com/StarMFWebService/StarMFWebService.svc/Secure",
        description="Secure endpoint for price service"
    )
    
    # Auth WSDL - same as order entry
    BSE_AUTH_WSDL: str = Field(
        default="https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl",
        description="WSDL URL for authentication service (same as order entry)"
    )
    BSE_AUTH_SECURE: str = Field(
        default="https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc/Secure",
        description="Secure endpoint for authentication service (same as order entry)"
    )

    # API Endpoints
    BSE_API_BASE_URL: str = Field(
        default="https://bsestarmfdemo.bseindia.com",
        description="Base URL for BSE STAR MF API"
    )
    
    # File Upload Settings
    BSE_UPLOAD_LOCATION: str = Field(
        default="./uploads",
        description="Location for file uploads"
    )
    BSE_MAX_FILE_SIZE: int = Field(
        default=10485760,  # 10MB
        description="Maximum file size for uploads in bytes"
    )
    
    # Timeouts (in seconds)
    BSE_REQUEST_TIMEOUT: int = Field(
        default=60,
        description="Request timeout in seconds"
    )
    BSE_CONNECT_TIMEOUT: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )
    
    # Rate Limiting
    BSE_MAX_RETRIES: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    BSE_RETRY_DELAY: int = Field(
        default=1,
        description="Delay between retries in seconds"
    )
    BSE_MAX_REQUESTS_PER_MINUTE: int = Field(
        default=60,
        description="Maximum requests allowed per minute"
    )

    # Response Settings
    BSE_SUCCESS_CODE: str = Field(
        default="100",
        description="Success response code"
    )
    BSE_ERROR_PREFIX: str = Field(
        default="BSE-",
        description="Error code prefix"
    )

    # Order Settings
    BSE_MIN_SIP_AMOUNT: float = Field(
        default=500.0,
        description="Minimum SIP amount allowed"
    )
    BSE_MIN_LUMPSUM_AMOUNT: float = Field(
        default=5000.0,
        description="Minimum lumpsum amount allowed"
    )
    BSE_MAX_SIP_INSTALLMENTS: int = Field(
        default=999,
        description="Maximum number of SIP installments allowed"
    )
    
    # Mandate Settings
    BSE_MIN_MANDATE_AMOUNT: float = Field(
        default=500.0,
        description="Minimum mandate amount allowed"
    )
    BSE_MAX_MANDATE_AMOUNT: float = Field(
        default=9999999999.0,
        description="Maximum mandate amount allowed"
    )

    # Client Settings
    BSE_DEFAULT_DP_TXN: str = Field(
        default="P",
        description="Default DP transaction mode (P=Physical)"
    )
    BSE_DEFAULT_CLIENT_TYPE: str = Field(
        default="P",
        description="Default client type (P=Physical)"
    )

    # Security Settings
    BSE_USE_HTTPS: bool = Field(
        default=True,
        description="Whether to use HTTPS"
    )
    BSE_VERIFY_SSL: bool = Field(
        default=True,
        description="Whether to verify SSL certificates"
    )
    BSE_SSL_CERT_PATH: Optional[str] = Field(
        default=None,
        description="Path to SSL certificate"
    )

    # Testing/Development Settings
    USE_MOCK_BSE: bool = Field(
        default=False,  # Set to False to use real BSE services
        description="Whether to use mock BSE services instead of real ones"
    )

    # Session timeout in seconds (1 hour for order entry, 5 minutes for others)
    SESSION_TIMEOUT: int = Field(
        default=3600,  # 1 hour
        description="Session timeout in seconds"
    )

# Create settings instance
bse_settings = BSESettings()

