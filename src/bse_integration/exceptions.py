# /home/ubuntu/order_management_system/src/bse_integration/exceptions.py

class BSEIntegrationError(Exception):
    """Base exception class for BSE integration errors."""
    pass

class BSETransportError(BSEIntegrationError):
    """Raised for network or transport level errors during SOAP communication."""
    pass

class BSESoapFault(BSEIntegrationError):
    """Raised when a SOAP fault occurs during communication."""
    pass

class BSEAuthError(BSEIntegrationError):
    """Base class for authentication specific errors."""
    pass

class BlankUserIdError(BSEAuthError):
    """Raised when User ID is blank."""
    def __init__(self, message="User ID cannot be blank."):
        super().__init__(message)

class BlankPasswordError(BSEAuthError):
    """Raised when Password is blank."""
    def __init__(self, message="Password cannot be blank."):
        super().__init__(message)

class BlankPassKeyError(BSEAuthError):
    """Raised when Pass Key is blank."""
    def __init__(self, message="Pass Key cannot be blank."):
        super().__init__(message)

class MaxLoginAttemptsError(BSEAuthError):
    """Raised when maximum login attempts are exceeded."""
    def __init__(self, message="Maximum login attempts exceeded."):
        super().__init__(message)

class InvalidAccountError(BSEAuthError):
    """Raised for invalid account information during authentication."""
    def __init__(self, message="Invalid account information."):
        super().__init__(message)

class UserDisabledError(BSEAuthError):
    """Raised when the user account is disabled."""
    def __init__(self, message="User account is disabled."):
        super().__init__(message)

class PasswordExpiredError(BSEAuthError):
    """Raised when the user password has expired."""
    def __init__(self, message="Password has expired."):
        super().__init__(message)

class UserNotExistsError(BSEAuthError):
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

