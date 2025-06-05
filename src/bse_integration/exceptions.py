# /home/ubuntu/order_management_system/src/bse_integration/exceptions.py

"""BSE STAR MF Integration Exceptions

This module contains all custom exceptions for BSE-related errors.
"""

class BSEBaseException(Exception):
    """Base exception for all BSE-related errors"""
    def __init__(self, message: str, code: str = None) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)

class BSEIntegrationError(BSEBaseException):
    """Raised when there is a configuration or initialization error"""
    pass

class BSEAuthenticationError(BSEBaseException):
    """Raised when authentication with BSE fails"""
    ERROR_CODES = {
        "101": "Invalid user ID or member code",
        "102": "Invalid password",
        "103": "Password expired",
        "104": "Account locked",
        "105": "Invalid passkey",
        "106": "Session expired",
        "107": "IP not whitelisted",
        "108": "Access denied",
        "109": "User disabled",
        "110": "Member disabled"
    }

    def __init__(self, message: str, code: str) -> None:
        if code in self.ERROR_CODES:
            message = f"{message} - {self.ERROR_CODES[code]}"
        super().__init__(message, code)

class BSEValidationError(BSEBaseException):
    """Raised when request validation fails"""
    pass

class BSEOrderError(BSEBaseException):
    """Raised when order processing fails"""
    ERROR_CODES = {
        # Authentication Errors
        "FAILED: USER ID MANDATORY": "User ID is required",
        "FAILED: MEMBER CODE MANDATORY": "Member code is required",
        "FAILED: PASSWORD MANDATORY": "Password is required",
        "FAILED: YOU HAVE EXCEEDED MAXIMUM LOGIN": "Maximum login attempts exceeded",
        "FAILED: CONTACT ADMIN": "Contact BSE admin",
        "FAILED: THE MEMBER IS SUSPENDED, CONTACT ADMIN": "Member is suspended",
        "FAILED: ACCESS TEMPORARILY SUSPENDED, KINDLY WAIT": "Access temporarily suspended",
        "FAILED: LOGIN PASSWORD EXPIRED, KINDLY RESET LOGIN": "Password expired",

        # Date Validation Errors
        "FAILED: INVALID FROM DATE": "Invalid from date format",
        "FAILED: INVALID TO DATE": "Invalid to date format",
        "FAILED: INVALID CLIENT CODE FOR GIVEN MEMBER CODE": "Invalid client code",
        "FAILED: INVALID TRANSACTION TYPE": "Invalid transaction type",
        "FAILED: INVALID ORDER TYPE": "Invalid order type",
        "FAILED: INVALID SETTLEMENT TYPE": "Invalid settlement type",
        "FAILED: USER NOT EXISTS": "User does not exist",

        # Order Status Errors
        "201": "Invalid transaction code",
        "202": "Invalid scheme code",
        "203": "Invalid amount/quantity",
        "204": "Invalid folio number",
        "205": "Invalid mandate ID",
        "206": "Invalid SIP registration ID",
        "207": "Invalid order ID",
        "208": "Duplicate order",
        "209": "Order not found",
        "210": "Order already cancelled",
        "211": "Order modification not allowed",
        "212": "Invalid order status",
        "213": "Invalid frequency type",
        "214": "Invalid start date",
        "215": "Invalid number of installments",
        "216": "Invalid switch scheme",
        "217": "Invalid redemption date",
        "218": "Invalid client code",
        "219": "Client not registered",
        "220": "KYC not compliant",
        "221": "PAN not verified",
        "222": "FATCA not compliant",
        "223": "Minimum investment criteria not met",
        "224": "Maximum investment limit exceeded",
        "225": "Cut-off time elapsed",
        "226": "Holiday/non-business day",
        "227": "Invalid bank details",
        "228": "Insufficient balance",
        "229": "Units not available",
        "230": "Mandate registration pending",
        "231": "Mandate amount insufficient",
        "232": "Mandate expired",
        "233": "Invalid EUIN",
        "234": "Invalid sub-broker ARN",
        "235": "Invalid DP transaction mode"
    }

    def __init__(self, message: str, code: str = None) -> None:
        if code in self.ERROR_CODES:
            message = f"{message} - {self.ERROR_CODES[code]}"
        super().__init__(message, code)

class BSETransportError(BSEBaseException):
    """Raised when there is a network/transport error"""
    pass

class BSESoapFault(BSEBaseException):
    """Raised when BSE SOAP service returns a fault"""
    pass

class BSEPaymentError(BSEBaseException):
    """Raised when payment processing fails"""
    ERROR_CODES = {
        "301": "Payment gateway error",
        "302": "Payment timeout",
        "303": "Payment declined",
        "304": "Invalid payment amount",
        "305": "Payment already processed",
        "306": "Payment cancelled",
        "307": "Invalid payment mode",
        "308": "Payment verification failed"
    }

    def __init__(self, message: str, code: str = None) -> None:
        if code in self.ERROR_CODES:
            message = f"{message} - {self.ERROR_CODES[code]}"
        super().__init__(message, code)

class BSEUploadError(BSEBaseException):
    """Raised when file upload fails"""
    ERROR_CODES = {
        "401": "Invalid file format",
        "402": "File size exceeded",
        "403": "File corrupted",
        "404": "Upload failed",
        "405": "Processing failed",
        "406": "Invalid record format",
        "407": "Duplicate records found",
        "408": "Mandatory fields missing"
    }

    def __init__(self, message: str, code: str) -> None:
        if code in self.ERROR_CODES:
            message = f"{message} - {self.ERROR_CODES[code]}"
        super().__init__(message, code)

class BSEClientRegError(BSEIntegrationError):
    """Raised for errors during client registration."""
    pass

class BlankUserIdError(BSEAuthenticationError):
    """Raised when User ID is blank."""
    def __init__(self, message="User ID cannot be blank."):
        super().__init__(message, "101")

class BlankPasswordError(BSEAuthenticationError):
    """Raised when Password is blank."""
    def __init__(self, message="Password cannot be blank."):
        super().__init__(message, "102")

class BlankPassKeyError(BSEAuthenticationError):
    """Raised when Pass Key is blank."""
    def __init__(self, message="Pass Key cannot be blank."):
        super().__init__(message, "105")

class MaxLoginAttemptsError(BSEAuthenticationError):
    """Raised when maximum login attempts are exceeded."""
    def __init__(self, message="Maximum login attempts exceeded."):
        super().__init__(message, "106")

class InvalidAccountError(BSEAuthenticationError):
    """Raised for invalid account information during authentication."""
    def __init__(self, message="Invalid account information."):
        super().__init__(message, "101")

class UserDisabledError(BSEAuthenticationError):
    """Raised when the user account is disabled."""
    def __init__(self, message="User account is disabled."):
        super().__init__(message, "109")

class PasswordExpiredError(BSEAuthenticationError):
    """Raised when the user password has expired."""
    def __init__(self, message="Password has expired."):
        super().__init__(message, "103")

class UserNotExistsError(BSEAuthenticationError):
    """Raised when the user does not exist."""
    def __init__(self, message="User does not exist."):
        super().__init__(message)

class BSEOrderError(BSEIntegrationError):
    """Raised for errors during order placement."""
    pass

class BSEClientRegError(BSEIntegrationError):
    """Raised for errors during client registration."""
    pass

class BSEValidationError(BSEIntegrationError):
    """Raised for validation errors related to BSE data or requests."""
    pass

