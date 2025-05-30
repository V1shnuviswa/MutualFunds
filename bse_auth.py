import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import requests
from requests.exceptions import RequestException
from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from requests import Session

from .bse_exceptions import (
    BSEError, BSEAuthError, raise_bse_error,
    BlankUserIdError, BlankPasswordError, BlankPassKeyError,
    MaxLoginAttemptsError, InvalidAccountError, UserDisabledError,
    PasswordExpiredError, UserNotExistsError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BSEMFAuth:
    """
    BSE Mutual Fund Order Web Service Authentication Handler
    
    This class manages authentication for the BSE MF Order Web Service using SOAP protocol.
    The authentication is done using the getPassword method which requires:
    - User ID (Login ID for Web Service)
    - Password (Password for the Login ID)
    - Pass Key (Random Alphanumeric value for Entropy)
    
    The service uses WSHttpBinding_MFOrderEntry1 binding and requires HTTPS for all communications.
    
    Attributes:
        user_id (str): BSE web service login ID
        password (str): BSE web service password
        wsdl_url (str): URL to the MFOrder WSDL definition
        session_valid_until (datetime): Timestamp when current session expires
        encrypted_password (str): Current encrypted password for order placement
    """
    
    # Response codes
    SUCCESS_CODE = "100"
    FAILURE_CODE = "101"
    
    # Error codes mapping
    ERROR_CODES = {
        "USER_ID_BLANK": "User ID field is blank",
        "PASSWORD_BLANK": "Password field is blank",
        "PASSKEY_BLANK": "Passkey field is blank",
        "USER_DISABLED": "User account is disabled",
        "MAX_ATTEMPTS": "Maximum login attempts exceeded",
        "INVALID_ACCOUNT": "Invalid account information",
        "PASSWORD_EXPIRED": "Password has expired",
        "USER_NOT_EXISTS": "User does not exist"
    }
    
    # Session validity in seconds
    MF_ORDER_SESSION_VALIDITY = 3600  # 1 hour
    DEFAULT_SESSION_VALIDITY = 300    # 5 minutes
    
    def __init__(
        self,
        user_id: str,
        password: str,
        wsdl_url: str,
        service_name: str = "MFOrder",
        auto_reauth: bool = True
    ) -> None:
        """
        Initialize BSE MF authentication handler.
        
        Args:
            user_id: BSE web service login ID
            password: BSE web service password
            wsdl_url: URL to the WSDL definition
            service_name: Name of the service (MFOrder or others)
            auto_reauth: Whether to automatically re-authenticate when session expires
            
        Raises:
            BlankUserIdError: If user_id is blank
            BlankPasswordError: If password is blank
        """
        # Validate input parameters
        if not user_id:
            raise BlankUserIdError()
        if not password:
            raise BlankPasswordError()
            
        self.user_id = user_id
        self.password = password
        self.wsdl_url = wsdl_url
        self.service_name = service_name
        self.auto_reauth = auto_reauth
        
        # Set session validity based on service type
        self.session_validity = (
            self.MF_ORDER_SESSION_VALIDITY 
            if service_name == "MFOrder" 
            else self.DEFAULT_SESSION_VALIDITY
        )
        
        # Initialize SOAP client with secure transport
        try:
            session = Session()
            session.verify = True
            transport = Transport(session=session)
            
            self.client = Client(
                wsdl_url,
                transport=transport
            )
            logger.info(f"Initialized SOAP client for BSE {service_name} service")
        except Exception as e:
            logger.error(f"Failed to initialize SOAP client: {e}")
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
            passkey: Pass key to validate (must be alphanumeric)
            
        Raises:
            BlankPassKeyError: If passkey is blank
            BSEValidationError: If passkey format is invalid
        """
        if not passkey:
            raise BlankPassKeyError()
        if not passkey.isalnum():
            raise BSEAuthError("Pass key must be alphanumeric with no special characters")

    def _handle_auth_response(self, response: str) -> Tuple[str, Optional[str]]:
        """
        Handle authentication response and raise appropriate exceptions.
        
        Args:
            response: Response string from BSE auth endpoint
            
        Returns:
            Tuple of (response_code, encrypted_password)
            
        Raises:
            Various BSE exceptions based on error code
        """
        try:
            parts = response.split("|")
            response_code = parts[0].strip()
            
            if response_code == self.SUCCESS_CODE:
                self._login_attempts = 0  # Reset login attempts on success
                return response_code, parts[1].strip() if len(parts) > 1 else None
                
            # Handle specific error cases
            error_message = parts[1].strip() if len(parts) > 1 else "Unknown error"
            
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
                raise BSEAuthError(f"Authentication failed: {error_message}")
                
        except (IndexError, ValueError) as e:
            logger.error(f"Failed to parse auth response: {e}")
            raise BSEAuthError(f"Invalid authentication response format: {response}")

    def authenticate(self, passkey: str) -> bool:
        """
        Authenticate with BSE MF Order Web Service using getPassword method.
        
        Args:
            passkey: Alphanumeric pass key
            
        Returns:
            bool: True if authentication successful
            
        Raises:
            Various BSE exceptions based on error code
        """
        self._validate_passkey(passkey)
        
        try:
            # Create and send SOAP request
            request_data = {
                "UserId": self.user_id,
                "Password": self.password,
                "PassKey": passkey
            }
            
            response = self.client.service.getPassword(**request_data)
            response_code, encrypted_password = self._handle_auth_response(response)
            
            if response_code == self.SUCCESS_CODE and encrypted_password:
                self.session_valid_until = datetime.now() + timedelta(seconds=self.session_validity)
                self.encrypted_password = encrypted_password
                self._last_passkey = passkey
                logger.info(f"Successfully authenticated with BSE {self.service_name} service")
                return True
                
            return False
                
        except Fault as e:
            logger.error(f"SOAP fault during authentication: {e}")
            raise BSEAuthError(f"SOAP fault: {str(e)}")
        except TransportError as e:
            logger.error(f"Transport error during authentication: {e}")
            raise BSEAuthError(f"Transport error: {str(e)}")
        except BSEError:
            raise  # Re-raise BSE-specific exceptions
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise BSEAuthError(f"Authentication failed: {str(e)}")

    def is_session_valid(self) -> bool:
        """Check if the current session is valid."""
        if not self.session_valid_until or not self.encrypted_password:
            return False
        return datetime.now() < self.session_valid_until

    def get_encrypted_password(self) -> str:
        """
        Get the current encrypted password for order placement.
        
        Returns:
            str: Current encrypted password
            
        Raises:
            BSEAuthError: If session is invalid or expired
        """
        if not self.is_session_valid():
            if self.auto_reauth and self._last_passkey:
                logger.info("Session expired, attempting automatic re-authentication")
                if not self.authenticate(self._last_passkey):
                    raise BSEAuthError("Failed to re-authenticate expired session")
            else:
                raise BSEAuthError("Invalid or expired session")
        
        return self.encrypted_password

    def logout(self) -> None:
        """Clear current session data."""
        self.session_valid_until = None
        self.encrypted_password = None
        self._last_passkey = None
        self._login_attempts = 0
        logger.info(f"Logged out of BSE {self.service_name} service") 