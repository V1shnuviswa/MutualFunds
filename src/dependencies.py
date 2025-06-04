# /home/ubuntu/order_management_system/src/dependencies.py

from typing import Generator, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from . import crud, models, schemas, security
from .database import SessionLocal
from .security import ALGORITHM, SECRET_KEY

# Import BSE integration components
from .bse_integration.auth import BSEAuthenticator
from .bse_integration.client_registration import BSEClientRegistrar
from .bse_integration.order import BSEOrderPlacer, SOAPMessageHandler
from .bse_integration.exceptions import BSEIntegrationError

# --- Database Dependency ---
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbDependency = Annotated[Session, Depends(get_db)]

# --- Authentication Dependencies ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

TokenDependency = Annotated[str, Depends(oauth2_scheme)]

async def get_current_user(token: TokenDependency, db: DbDependency) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    user = crud.get_user(db, user_id=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    # Add logic here if users can be deactivated
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

CurrentUserDependency = Annotated[models.User, Depends(get_current_active_user)]

# --- BSE Integration Dependencies ---

# Create singleton instances (consider lifespan management if needed)
try:
    bse_authenticator_instance = BSEAuthenticator()
except BSEIntegrationError as e:
    print(f"CRITICAL: Failed to initialize BSEAuthenticator: {e}")
    raise

try:
    bse_client_registrar_instance = BSEClientRegistrar()
except BSEIntegrationError as e:
    print(f"WARNING: Failed to initialize BSEClientRegistrar: {e}")
    bse_client_registrar_instance = None

try:
    bse_order_placer_instance = BSEOrderPlacer()
    bse_soap_handler_instance = SOAPMessageHandler()
except BSEIntegrationError as e:
    print(f"CRITICAL: Failed to initialize BSE Order components: {e}")
    raise

def get_bse_authenticator() -> BSEAuthenticator:
    if bse_authenticator_instance is None:
        raise HTTPException(status_code=503, detail="BSE Authentication service is unavailable")
    return bse_authenticator_instance

def get_bse_client_registrar() -> BSEClientRegistrar:
    if bse_client_registrar_instance is None:
        raise HTTPException(status_code=503, detail="BSE Client Registration service is unavailable")
    return bse_client_registrar_instance

def get_bse_order_placer() -> BSEOrderPlacer:
    if bse_order_placer_instance is None:
        raise HTTPException(status_code=503, detail="BSE Order service is unavailable")
    return bse_order_placer_instance

def get_bse_soap_handler() -> SOAPMessageHandler:
    if bse_soap_handler_instance is None:
        raise HTTPException(status_code=503, detail="BSE SOAP handler is unavailable")
    return bse_soap_handler_instance

BSEAuthenticatorDependency = Annotated[BSEAuthenticator, Depends(get_bse_authenticator)]
BSEClientRegistrarDependency = Annotated[BSEClientRegistrar, Depends(get_bse_client_registrar)]
BSEOrderPlacerDependency = Annotated[BSEOrderPlacer, Depends(get_bse_order_placer)]
BSESoapHandlerDependency = Annotated[SOAPMessageHandler, Depends(get_bse_soap_handler)]

