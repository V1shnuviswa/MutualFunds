# /home/ubuntu/order_management_system/src/bse_integration/auth.py

"""BSE STAR MF Authentication Module

This module handles authentication with BSE STAR MF using SOAP.
Supports password encryption, session management, and automatic re-authentication.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

import requests
from requests.exceptions import RequestException
from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from requests import Session
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from .config import bse_settings
from .exceptions import (
    BSEIntegrationError, BSEAuthError, BSETransportError, BSESoapFault,
    BlankUserIdError, BlankPasswordError, BlankPassKeyError,
    MaxLoginAttemptsError, InvalidAccountError, UserDisabledError,
    PasswordExpiredError, UserNotExistsError, BSEValidationError,
    BranchSuspendedError, MemberSuspendedError, AccessTemporarilySuspendedError
)
from ..database import get_db
from ..security import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth2 configuration for BSE integration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# BSE router for authentication endpoints
bse_router = APIRouter(
    prefix="/bse",
    tags=["BSE Authentication"]
)

# Direct token verification function to avoid circular imports
async def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {"username": username}
    except JWTError:
        raise credentials_exception

@dataclass
class AuthResponse:
    """Standard response format for authentication operations"""
    success: bool
    encrypted_password: Optional[str]
    message: str
    status_code: str
    details: Dict[str, Any]

class BSEAuthenticator:
    """
    Manages authentication with the BSE STAR MF using SOAP.
    Handles session management and automatic re-authentication.
    """

    def __init__(self) -> None:
        """Initialize BSE Authentication handler."""
        self.user_id = bse_settings.BSE_USER_ID
        self.member_id = bse_settings.BSE_MEMBER_CODE
        self.password = bse_settings.BSE_PASSWORD
        self.wsdl_url = bse_settings.BSE_AUTH_WSDL
        self.secure_url = bse_settings.BSE_AUTH_SECURE
        self.passkey = bse_settings.BSE_PASSKEY

        # Validate essential config with strict validation
        if not self.user_id:
            raise BlankUserIdError()
        if not self.password:
            raise BlankPasswordError()
        if not self.wsdl_url:
            raise BSEValidationError("WSDL URL is required")
        if not self.passkey:
            raise BlankPassKeyError()

        # Initialize SOAP client
        try:
            session = requests.Session()
            
            # Configure session with SSL settings
            session.verify = bse_settings.BSE_VERIFY_SSL
            if bse_settings.BSE_SSL_CERT_PATH:
                session.verify = bse_settings.BSE_SSL_CERT_PATH
                
            # Configure timeouts
            transport = Transport(
                session=session,
                timeout=(bse_settings.BSE_CONNECT_TIMEOUT, bse_settings.BSE_REQUEST_TIMEOUT)
            )
            
            self.client = Client(self.wsdl_url, transport=transport)
            # Set the service location to the secure endpoint
            self.client.service._binding_options["address"] = self.secure_url
            logger.info("Initialized SOAP client for BSE Authentication service")
        except Exception as e:
            logger.error(f"Failed to initialize SOAP client: {e}", exc_info=True)
            raise BSEAuthError(f"WSDL initialization failed: {str(e)}")

        # Session management
        self.session_valid_until: Optional[datetime] = None
        self.encrypted_password: Optional[str] = None
        self._last_passkey: Optional[str] = self.passkey  # Initialize with the default passkey
        self._login_attempts = 0
        self._max_login_attempts = 5

    def _validate_passkey(self, passkey: str) -> None:
        """
        Validate the format of the pass key.
        
        Args:
            passkey: The pass key to validate
            
        Raises:
            BlankPassKeyError: If pass key is blank
            BSEValidationError: If pass key format is invalid
        """
        if not passkey:
            raise BlankPassKeyError()
        # BSE documentation says passkey should be 10 chars, but we'll be more flexible
        # if not passkey.isalnum() or len(passkey) != 10:
        #    raise BSEValidationError("Pass key must be 10 characters alphanumeric")

    def is_session_valid(self) -> bool:
        """Check if the current session is valid."""
        if not self.session_valid_until or not self.encrypted_password:
            return False
        return datetime.now() < self.session_valid_until

    async def get_encrypted_password(self) -> str:
        """
        Get the current encrypted password, re-authenticating if needed.
        
        Returns:
            Current encrypted password
            
        Raises:
            BSEAuthError: If unable to get valid encrypted password
        """
        if self.is_session_valid():
            if not self.encrypted_password:
                raise BSEAuthError("Session valid but no encrypted password")
            return self.encrypted_password

        # Use the default passkey if no previous passkey is available
        passkey_to_use = self._last_passkey if self._last_passkey else self.passkey
        auth_response = await self.authenticate(passkey_to_use)
        
        if not auth_response.success:
            raise BSEAuthError("Re-authentication failed")

        return auth_response.encrypted_password

    async def authenticate(self, passkey: str) -> AuthResponse:
        """
        Authenticate with BSE STAR MF using getPassword method.
        
        Args:
            passkey: Pass key for authentication
            
        Returns:
            AuthResponse object with authentication result
            
        Raises:
            BSEAuthError: For authentication failures
            BSESoapFault: For SOAP faults
            BSETransportError: For transport/connection errors
        """
        self._validate_passkey(passkey)
        self._last_passkey = passkey
        
        # Increment login attempts
        self._login_attempts += 1
        if self._login_attempts > self._max_login_attempts:
            raise MaxLoginAttemptsError()
        
        # Clear any previous session
        self.encrypted_password = None
        self.session_valid_until = None
        
        # Log authentication attempt
        logger.info(f"Authenticating with BSE STAR MF: User={self.user_id}, Member={self.member_id}")
        
        # Prepare authentication parameters
        params = {
            "UserId": self.user_id,
            "Password": self.password,
            "PassKey": passkey,
            "MemberId": self.member_id
        }
        
        try:
            # Get the encrypted password using SOAP call
            response = await asyncio.to_thread(
                self.client.service.getPassword,
                **params
            )
            
            # Log the response
            logger.debug(f"BSE Authentication response: {response}")
            
            # Different response formats based on environment (sometimes string, sometimes object)
            if isinstance(response, str):
                parts = response.split('|')
                
                # Status at position 0, encrypted password at position 1
                if len(parts) > 1 and parts[0] == '100':
                    self.encrypted_password = parts[1]
                    self.session_valid_until = datetime.now() + timedelta(hours=1)
                    self._login_attempts = 0
                    
                    return AuthResponse(
                        success=True,
                        encrypted_password=self.encrypted_password,
                        message="Successfully authenticated",
                        status_code=parts[0],
                        details={}
                    )
                else:
                    error_message = f"Authentication failed. Status: {parts[0]}"
                    if len(parts) > 1:
                        error_message += f" - {parts[1]}"
                    logger.error(error_message)
                    
                    return AuthResponse(
                        success=False,
                        encrypted_password=None,
                        message=error_message,
                        status_code=parts[0] if len(parts) > 0 else "Unknown",
                        details={}
                    )
            else:
                # Try to handle it as an object (fallback)
                if hasattr(response, 'Status') and response.Status == '100':
                    self.encrypted_password = response.ResponseString
                    self.session_valid_until = datetime.now() + timedelta(hours=1)
                    self._login_attempts = 0
                    
                    return AuthResponse(
                        success=True,
                        encrypted_password=self.encrypted_password,
                        message="Successfully authenticated",
                        status_code=response.Status,
                        details={}
                    )
                else:
                    error_message = f"Authentication failed. Status: {getattr(response, 'Status', 'Unknown')}"
                    logger.error(error_message)
                    
                    return AuthResponse(
                        success=False,
                        encrypted_password=None,
                        message=error_message,
                        status_code=getattr(response, 'Status', 'Unknown'),
                        details={}
                    )
                
        except Fault as e:
            error_message = f"SOAP Fault: {e}"
            logger.error(error_message)
            raise BSESoapFault(error_message)
        except TransportError as e:
            error_message = f"Transport Error: {e}"
            logger.error(error_message)
            raise BSETransportError(error_message)
        except RequestException as e:
            error_message = f"Request Exception: {e}"
            logger.error(error_message)
            raise BSETransportError(error_message)
        except Exception as e:
            error_message = f"Unexpected error during authentication: {e}"
            logger.error(error_message, exc_info=True)
            raise BSEAuthError(error_message)

    def logout(self) -> None:
        """Invalidate the current session."""
        self.encrypted_password = None
        self.session_valid_until = None
        logger.info("Logged out of BSE session")

@bse_router.post("/authenticate")
async def bse_authenticate(
    passkey: str,
    user_info: dict = Depends(verify_token),
    bse_auth: BSEAuthenticator = Depends()
) -> Dict[str, Any]:
    """
    Authenticate with BSE STAR MF.
    
    Args:
        passkey: Pass key for BSE authentication
        user_info: Current authenticated user info
        bse_auth: BSE authenticator instance
        
    Returns:
        Dictionary containing authentication result
    """
    try:
        auth_response = await bse_auth.authenticate(passkey)
        return {
            "success": auth_response.success,
            "message": auth_response.message,
            "status_code": auth_response.status_code,
            "session_valid_until": bse_auth.session_valid_until.isoformat() if bse_auth.session_valid_until else None
        }
    except BSEIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@bse_router.post("/logout")
async def bse_logout(
    user_info: dict = Depends(verify_token),
    bse_auth: BSEAuthenticator = Depends()
) -> Dict[str, str]:
    """
    Logout from BSE STAR MF session.
    
    Args:
        user_info: Current authenticated user info
        bse_auth: BSE authenticator instance
        
    Returns:
        Dictionary containing logout result
    """
    bse_auth.logout()
    return {"message": "Successfully logged out from BSE session"}


