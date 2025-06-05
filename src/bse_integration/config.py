# /home/ubuntu/order_management_system/src/bse_integration/config.py

"""BSE STAR MF Integration Configuration

This module contains all configuration settings for BSE STAR MF integration.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skipping .env load
    pass

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
    BSE_ORDER_ENTRY_WSDL: str = Field(
        default="http://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl",
        description="WSDL URL for order entry service"
    )
    BSE_UPLOAD_WSDL: str = Field(
        default="http://bsestarmfdemo.bseindia.com/MFUploadService/MFUploadService.svc?wsdl",
        description="WSDL URL for file upload service"
    )
    BSE_PRICE_WSDL: str = Field(
        default="http://bsestarmfdemo.bseindia.com/StarMFWebService/StarMFWebService.svc?wsdl",
        description="WSDL URL for price service"
    )

    # Authentication
    BSE_USER_ID: str = Field(
        default="",
        description="BSE STAR MF user ID"
    )
    BSE_MEMBER_CODE: str = Field(
        default="",
        description="BSE STAR MF member code"
    )
    BSE_PASSWORD: str = Field(
        default="",
        description="BSE STAR MF password"
    )
    BSE_PASSKEY: str = Field(
        default="",
        description="BSE STAR MF passkey"
    )

    # API Endpoints
    BSE_API_BASE_URL: str = Field(
        default="http://bsestarmfdemo.bseindia.com",
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
        default=30,
        description="Request timeout in seconds"
    )
    BSE_CONNECT_TIMEOUT: int = Field(
        default=10,
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

    @validator("BSE_USER_ID", "BSE_MEMBER_CODE", "BSE_PASSWORD", "BSE_PASSKEY", "BSE_ORDER_ENTRY_WSDL")
    def validate_required_fields(cls, v, field):
        if not v:
            raise ValueError(f"{field.name} is required")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
bse_settings = BSESettings()

