from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import date

from .. import schemas, crud
from ..dependencies import (
    get_db,
    get_current_active_user,
    get_bse_authenticator,
    BSEAuthenticatorDependency,
)
from ..bse_integration.price import BSEPriceDiscovery
from ..bse_integration.exceptions import (
    BSEIntegrationError,
    BSEAuthError,
    BSEValidationError,
    BSESoapFault,
    BSETransportError
)

router = APIRouter(
    prefix="/price",
    tags=["price"],
    responses={404: {"description": "Not found"}},
)

# Initialize BSE Price Discovery service
bse_price_discovery = BSEPriceDiscovery()

@router.get("/nav/{scheme_code}", response_model=schemas.NAVResponse)
async def get_scheme_nav(
    scheme_code: str,
    date: date | None = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
    bse_authenticator: BSEAuthenticatorDependency = Depends(get_bse_authenticator),
):
    """
    Get the NAV for a specific scheme code.
    Optionally specify a date (defaults to current date).
    """
    # Validate scheme exists in our database
    db_scheme = crud.get_scheme(db, scheme_code=scheme_code)
    if not db_scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found"
        )

    try:
        # Get encrypted password for BSE authentication
        placeholder_passkey = "PassKey123"  # Replace with actual passkey source
        if not bse_authenticator.is_session_valid():
            await bse_authenticator.authenticate(placeholder_passkey)
        encrypted_password = await bse_authenticator.get_encrypted_password()

        # Create NAV request
        nav_request = schemas.NAVRequest(
            scheme_code=scheme_code,
            date=date,
            user_id=current_user.user_id
        )

        # Get NAV from BSE
        nav_response = await bse_price_discovery.get_nav(nav_request, encrypted_password)

        # Map to response schema
        return schemas.NAVResponse(
            schemeCode=nav_response["scheme_code"],
            schemeName=nav_response["scheme_name"],
            nav=nav_response["nav"],
            navDate=nav_response["nav_date"],
            status="Success",
            statusCode=nav_response["status_code"],
            message=nav_response["message"]
        )

    except (BSEAuthError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        if isinstance(e, BSEValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(e, BSEAuthError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch NAV: {str(e)}"
        ) 