# /home/ubuntu/order_management_system/src/bse_integration/auth.py

import logging
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

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
    PasswordExpiredError, UserNotExistsError, BSEValidationError
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

class BSEAuthenticator:
    """
    Manages authentication with the BSE MF Order Web Service using SOAP.
    Handles session management and automatic re-authentication.
    Uses asyncio.to_thread for blocking SOAP calls.
    """
    # Response codes
    SUCCESS_CODE = "100"
    FAILURE_CODE = "101"

    def __init__(self, auto_reauth: bool = True) -> None:
        """
        Initialize BSE MF authentication handler.

        Args:
            auto_reauth: Whether to automatically re-authenticate when session expires.
        """
        self.user_id = bse_settings.BSE_USER_ID
        self.password = bse_settings.BSE_PASSWORD
        self.wsdl_url = bse_settings.BSE_AUTH_WSDL # Use AUTH WSDL from config
        self.auto_reauth = auto_reauth
        self.session_validity = bse_settings.BSE_SESSION_TIMEOUT

        # Validate essential config
        if not self.user_id:
            raise BlankUserIdError()
        if not self.password:
            raise BlankPasswordError()
        if not self.wsdl_url:
             raise BSEAuthError("BSE_AUTH_WSDL is not configured.")

        # Initialize SOAP client with secure transport
        try:
            session = Session()
            # In production, consider stricter SSL verification
            transport = Transport(session=session)
            # Client initialization itself is usually not blocking I/O
            self.client = Client(self.wsdl_url, transport=transport)
            logger.info(f"Initialized SOAP client for BSE Authentication service ({self.wsdl_url})")
        except Exception as e:
            logger.error(f"Failed to initialize SOAP client for {self.wsdl_url}: {e}", exc_info=True)
            raise BSEAuthError(f"WSDL initialization failed: {str(e)}")

        # Session management attributes
        self.session_valid_until: Optional[datetime] = None
        self.encrypted_password: Optional[str] = None
        self._last_passkey: Optional[str] = None
        self._login_attempts = 0
        self._max_login_attempts = 5 # Consider making this configurable

    def _validate_passkey(self, passkey: str) -> None:
        """Validate the format of the pass key."""
        if not passkey:
            raise BlankPassKeyError()
        if not passkey.isalnum():
            raise BSEValidationError("Pass key must be alphanumeric with no special characters")

    def _handle_auth_response(self, response: str) -> Tuple[str, Optional[str]]:
        """Handle authentication response string and raise appropriate exceptions."""
        # This method is synchronous as it only parses strings
        try:
            parts = response.split("|")
            response_code = parts[0].strip()

            if response_code == self.SUCCESS_CODE:
                self._login_attempts = 0 # Reset login attempts on success
                encrypted_pass = parts[1].strip() if len(parts) > 1 else None
                if not encrypted_pass:
                     raise BSEAuthError("Authentication successful but no encrypted password received.")
                return response_code, encrypted_pass
            else:
                error_message = parts[1].strip() if len(parts) > 1 else "Unknown authentication error"
                logger.warning(f"BSE Authentication failed. Code: {response_code}, Message: {error_message}")
                if "USER_DISABLED" in error_message:
                    raise UserDisabledError()
                elif "MAX_LOGIN_ATTEMPTS" in error_message:
                    raise MaxLoginAttemptsError()
                elif "INVALID_ACCOUNT" in error_message:
                    self._login_attempts += 1
                    if self._login_attempts >= self._max_login_attempts:
                        raise MaxLoginAttemptsError()
                    raise InvalidAccountError()
                elif "PASSWORD_EXPIRED" in error_message:
                    raise PasswordExpiredError()
                elif "USER_NOT_EXISTS" in error_message:
                    raise UserNotExistsError()
                else:
                    raise BSEAuthError(f"Authentication failed: {error_message} (Code: {response_code})")

        except (IndexError, ValueError) as e:
            logger.error(f"Failed to parse BSE auth response: {response}\nError: {e}", exc_info=True)
            raise BSEAuthError(f"Invalid authentication response format received from BSE.")

    async def authenticate(self, passkey: str) -> bool:
        """
        Authenticate with BSE MF Order Web Service using getPassword method.
        Runs the blocking SOAP call in a separate thread.
        """
        self._validate_passkey(passkey)
        logger.info(f"Attempting BSE authentication for user: {self.user_id}")
        try:
            request_data = {
                "UserId": self.user_id,
                "Password": self.password,
                "PassKey": passkey
            }
            
            # Define the blocking call
            def soap_call():
                return self.client.service.getPassword(**request_data)

            # Run the blocking call in a separate thread
            response = await asyncio.to_thread(soap_call)
            logger.debug(f"Raw BSE getPassword response: {response}")

            response_code, encrypted_password = self._handle_auth_response(response)

            if response_code == self.SUCCESS_CODE and encrypted_password:
                self.session_valid_until = datetime.now() + timedelta(seconds=self.session_validity)
                self.encrypted_password = encrypted_password
                self._last_passkey = passkey
                logger.info(f"Successfully authenticated with BSE. Session valid until {self.session_valid_until}")
                return True
            else:
                 logger.error("Authentication failed after response handling.")
                 return False

        except Fault as e:
            logger.error(f"SOAP fault during authentication: {e}", exc_info=True)
            raise BSESoapFault(f"SOAP fault: {str(e)}")
        except TransportError as e:
            logger.error(f"Transport error during authentication: {e}", exc_info=True)
            raise BSETransportError(f"Transport error: {str(e)}")
        except RequestException as e:
            logger.error(f"Network error during authentication: {e}", exc_info=True)
            raise BSETransportError(f"Network error: {str(e)}")
        except BSEIntegrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}", exc_info=True)
            raise BSEAuthError(f"Unexpected authentication error: {str(e)}")

    def is_session_valid(self) -> bool:
        """Check if the current session is valid."""
        if not self.session_valid_until or not self.encrypted_password:
            return False
        return datetime.now() < self.session_valid_until

    async def get_encrypted_password(self) -> str:
        """
        Get the current encrypted password, handling re-authentication.
        """
        if self.is_session_valid():
            logger.debug("BSE session is valid. Returning existing encrypted password.")
            # Type hint satisfaction
            if self.encrypted_password is None:
                 raise BSEAuthError("Session valid but encrypted password is None, internal state error.")
            return self.encrypted_password
        else:
            logger.warning("BSE session is invalid or expired.")
            if self.auto_reauth and self._last_passkey:
                logger.info("Attempting automatic re-authentication...")
                try:
                    # authenticate is now async
                    if await self.authenticate(self._last_passkey):
                        logger.info("Automatic re-authentication successful.")
                        if self.encrypted_password is None:
                             raise BSEAuthError("Re-authentication successful but encrypted password is None.")
                        return self.encrypted_password
                    else:
                        raise BSEAuthError("Automatic re-authentication attempt failed.")
                except Exception as e:
                    logger.error(f"Automatic re-authentication failed: {e}", exc_info=True)
                    raise BSEAuthError(f"Failed to re-authenticate expired session: {str(e)}")
            else:
                if not self.auto_reauth:
                     raise BSEAuthError("BSE session invalid/expired. Auto re-authentication disabled.")
                else: # No last passkey available
                     raise BSEAuthError("BSE session invalid/expired. Cannot re-authenticate without a previous passkey.")

    def logout(self) -> None:
        """Clear current session data."""
        # This method is synchronous
        self.session_valid_until = None
        self.encrypted_password = None
        self._last_passkey = None
        self._login_attempts = 0
        logger.info("Cleared BSE authentication session data.")

# API Authentication endpoints
@router.post("/login", response_model=Dict[str, str])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    bse_auth: BSEAuthenticator = Depends()
):
    """
    Authenticate user and create access token.
    Also performs BSE authentication if required.
    """
    # First authenticate with local system
    user = crud.get_user_by_userid(db, user_id=form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If local auth successful, try BSE auth if passkey provided
    if form_data.scopes and "bse_auth" in form_data.scopes and user.pass_key:
        try:
            bse_auth_success = await bse_auth.authenticate(user.pass_key)
            if not bse_auth_success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="BSE authentication failed",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except BSEIntegrationError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"BSE service error: {str(e)}"
            )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.user_id,
            "member_id": user.member_id,
            "bse_authenticated": bool(form_data.scopes and "bse_auth" in form_data.scopes)
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "bse_authenticated": bool(form_data.scopes and "bse_auth" in form_data.scopes)
    }

@router.post("/register", response_model=Dict[str, str])
async def register_user(user_data: Dict[str, str], db: Session = Depends(get_db)):
    """Register a new user in the system."""
    if crud.get_user_by_userid(db, user_id=user_data["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID already registered"
        )
    
    user = crud.create_user(db=db, user_data=user_data)
    return {"message": "User registered successfully", "user_id": user.user_id}

@router.post("/bse/authenticate")
async def bse_authenticate(
    passkey: str,
    current_user = Depends(get_current_user),
    bse_auth: BSEAuthenticator = Depends()
):
    """
    Authenticate with BSE using provided passkey.
    Requires user to be already authenticated with the system.
    """
    try:
        auth_success = await bse_auth.authenticate(passkey)
        if auth_success:
            return {"message": "BSE authentication successful"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="BSE authentication failed"
        )
    except BSEIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"BSE service error: {str(e)}"
        )

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
    bse_auth: BSEAuthenticator = Depends()
):
    """
    Logout user from both system and BSE.
    Clears BSE session if exists.
    """
    bse_auth.logout()
    return {"message": "Logged out successfully"}

# Helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
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
    """Validate JWT token and return current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_userid(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user


