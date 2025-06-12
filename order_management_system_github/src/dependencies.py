# /home/ubuntu/order_management_system/src/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional, Any, Annotated
from jose import JWTError, jwt
from pydantic import ValidationError
from datetime import datetime, timedelta

from . import crud, security, models, schemas
from .database import get_db, SessionLocal
from .security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Type dependencies
DbDependency = Annotated[Session, Depends(get_db)]
TokenDependency = Annotated[str, Depends(oauth2_scheme)]

async def get_current_user(token: TokenDependency, db: Session = Depends(get_db)) -> models.User:
    """Get the current authenticated user from token"""
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

    user = crud.get_user_by_userid(db, user_id=username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_id(token: TokenDependency, db: Session = Depends(get_db)) -> str:
    """Get the current user ID from the JWT token"""
    user = await get_current_user(token, db)
    return user.user_id

# Type annotations for common dependencies
CurrentUserDependency = Annotated[models.User, Depends(get_current_user)]

# Import BSE-related classes here to avoid circular imports
# These functions will be called when needed, not during import
def get_bse_authenticator():
    """Get BSE authenticator instance"""
    # Import here to avoid circular import
    from .bse_integration.auth import BSEAuthenticator
    return BSEAuthenticator()

def get_bse_order_placer():
    """Get BSE order placer instance"""
    # Import here to avoid circular import
    from .bse_integration.order import BSEOrderPlacer
    return BSEOrderPlacer()

def get_bse_client_registrar():
    """Get BSE client registrar instance"""
    # Import here to avoid circular import
    from .bse_integration.client_registration import BSEClientRegistrar
    return BSEClientRegistrar()

def get_bse_soap_handler():
    """Get BSE SOAP message handler instance"""
    # Import here to avoid circular import
    from .bse_integration.order import SOAPMessageHandler
    return SOAPMessageHandler()

def get_bse_price_discovery():
    """Get BSE price discovery instance"""
    # Import here to avoid circular import
    from .bse_integration.price import BSEPriceDiscovery
    return BSEPriceDiscovery()

# BSE integration dependencies
BSEAuthenticatorDependency = Annotated[Any, Depends(get_bse_authenticator)]
BSEOrderPlacerDependency = Annotated[Any, Depends(get_bse_order_placer)]
BSEClientRegistrarDependency = Annotated[Any, Depends(get_bse_client_registrar)]
BSEPriceDiscoveryDependency = Annotated[Any, Depends(get_bse_price_discovery)]

