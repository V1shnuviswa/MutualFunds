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
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth2 configuration
SECRET_KEY = "your-secret-key-here"  # In production, use secure environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Router configuration
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

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
        self.wsdl_url = bse_settings.order_wsdl

        # Validate essential config
        if not self.user_id or len(self.user_id) != 5:
            raise BlankUserIdError()
        if not self.password or len(self.password) > 20:
            raise BlankPasswordError()
        if not self.wsdl_url:
            raise BSEAuthError("BSE_ORDER_WSDL is not configured.")

        # Initialize SOAP client
        try:
            session = Session()
            transport = Transport(session=session, timeout=bse_settings.REQUEST_TIMEOUT)
            self.client = Client(self.wsdl_url, transport=transport)
            logger.info("Initialized SOAP client for BSE Authentication service")
        except Exception as e:
            logger.error(f"Failed to initialize SOAP client: {e}", exc_info=True)
            raise BSEAuthError(f"WSDL initialization failed: {str(e)}")

        # Session management
        self.session_valid_until: Optional[datetime] = None
        self.encrypted_password: Optional[str] = None
        self._last_passkey: Optional[str] = None
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
        if not passkey.isalnum() or len(passkey) != 10:
            raise BSEValidationError("Pass key must be 10 characters alphanumeric")

    def _handle_auth_response(self, response: str) -> AuthResponse:
        """
        Handle authentication response string and raise appropriate exceptions.
        
        Args:
            response: Raw response string from BSE
            
        Returns:
            AuthResponse object containing parsed response
            
        Raises:
            Various BSEAuthError subclasses based on error type
        """
        try:
            parts = [part.strip() for part in response.split("|")]
            
            if len(parts) < 2:
                raise BSEAuthError("Invalid response format from BSE")

            status_code = parts[0]
            message = parts[1]
            encrypted_pass = parts[2] if len(parts) > 2 else None

            if status_code == bse_settings.SUCCESS_CODE:
                self._login_attempts = 0
                if not encrypted_pass:
                    raise BSEAuthError("No encrypted password received")
                return AuthResponse(
                    success=True,
                    encrypted_password=encrypted_pass,
                    message=message,
                    status_code=status_code,
                    details={}
                )

            # Handle error cases
            self._login_attempts += 1
            error_details = {"attempts": self._login_attempts}

            if "USER_DISABLED" in message:
                raise UserDisabledError()
            elif "MAX_LOGIN_ATTEMPTS" in message or self._login_attempts >= self._max_login_attempts:
                raise MaxLoginAttemptsError()
            elif "INVALID_ACCOUNT" in message:
                raise InvalidAccountError()
            elif "PASSWORD_EXPIRED" in message:
                raise PasswordExpiredError()
            elif "USER_NOT_EXISTS" in message:
                raise UserNotExistsError()
            elif "BRANCH_SUSPENDED" in message:
                raise BranchSuspendedError()
            elif "MEMBER_SUSPENDED" in message:
                raise MemberSuspendedError()
            elif "ACCESS_SUSPENDED" in message:
                raise AccessTemporarilySuspendedError()
            else:
                raise BSEAuthError(f"Authentication failed: {message}")

        except (IndexError, ValueError) as e:
            logger.error(f"Failed to parse BSE auth response: {e}", exc_info=True)
            raise BSEAuthError("Invalid response format from BSE")

    async def authenticate(self, passkey: str) -> AuthResponse:
        """
        Authenticate with BSE STAR MF using getPassword method.
        
        Args:
            passkey: Pass key for authentication
            
        Returns:
            AuthResponse object containing authentication result
            
        Raises:
            Various BSE exceptions based on error type
        """
        self._validate_passkey(passkey)
        logger.info(f"Authenticating with BSE STAR MF")

        try:
            params = {
                "UserId": self.user_id,
                "MemberId": self.member_id,
                "Password": self.password,
                "PassKey": passkey
            }

            def soap_call():
                return self.client.service.getPassword(**params)

            response = await asyncio.to_thread(soap_call)
            logger.debug(f"BSE Response: {response}")

            auth_response = self._handle_auth_response(str(response))

            if auth_response.success:
                self.session_valid_until = datetime.now() + timedelta(seconds=bse_settings.SESSION_TIMEOUT)
                self.encrypted_password = auth_response.encrypted_password
                self._last_passkey = passkey
                logger.info(f"Successfully authenticated with BSE")

            return auth_response

        except Fault as e:
            logger.error(f"SOAP fault: {e}", exc_info=True)
            raise BSESoapFault(f"SOAP fault: {str(e)}")
        except TransportError as e:
            logger.error(f"Transport error: {e}", exc_info=True)
            raise BSETransportError(f"Transport error: {str(e)}")
        except RequestException as e:
            logger.error(f"Network error: {e}", exc_info=True)
            raise BSETransportError(f"Network error: {str(e)}")
        except BSEIntegrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise BSEAuthError(f"Unexpected error: {str(e)}")

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

        if not self._last_passkey:
            raise BSEAuthError("No previous pass key available for re-authentication")

        auth_response = await self.authenticate(self._last_passkey)
        if not auth_response.success:
            raise BSEAuthError("Re-authentication failed")

        return auth_response.encrypted_password

    def logout(self) -> None:
        """Clear current session."""
        self.session_valid_until = None
        self.encrypted_password = None
        self._last_passkey = None
        self._login_attempts = 0
        logger.info("Logged out of BSE session")

# FastAPI route handlers
@router.post("/login", response_model=Dict[str, str])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    bse_auth: BSEAuthenticator = Depends()
) -> Dict[str, str]:
    """Handle user login and return access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/bse/authenticate")
async def bse_authenticate(
    passkey: str,
    current_user = Depends(get_current_user),
    bse_auth: BSEAuthenticator = Depends()
) -> Dict[str, Any]:
    """
    Authenticate with BSE STAR MF.
    
    Args:
        passkey: Pass key for BSE authentication
        current_user: Current authenticated user
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

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
    bse_auth: BSEAuthenticator = Depends()
) -> Dict[str, str]:
    """
    Logout from BSE session.
    
    Args:
        current_user: Current authenticated user
        bse_auth: BSE authenticator instance
        
    Returns:
        Dictionary containing logout result
    """
    bse_auth.logout()
    return {"message": "Successfully logged out"}

# Helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token."""
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
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user


