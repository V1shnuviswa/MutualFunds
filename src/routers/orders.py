# /home/ubuntu/order_management_system/src/routers/orders.py

import logging
from typing import List, Any, Dict

from fastapi import APIRouter, HTTPException, status, Body
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..dependencies import (
    DbDependency, CurrentUserDependency,
    BSEAuthenticatorDependency, BSEOrderPlacerDependency # Import BSE dependencies
)
from ..utils import preprocess_payload # Keep the preprocessor for incoming requests
from ..bse_integration.exceptions import (
    BSEIntegrationError, BSEAuthError, BSEOrderError, 
    BSESoapFault, BSETransportError, BSEValidationError
) # Import BSE exceptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["orders"],
    # dependencies=[Depends(get_current_active_user)] # Apply auth dependency globally if needed
)

@router.post("/lumpsum", response_model=schemas.LumpsumOrderResponse)
async def place_lumpsum_order(
    payload: Dict[str, Any] = Body(...),
    db: DbDependency = None, # Keep DB dependency if needed for logging/pre-checks
    current_user: CurrentUserDependency = None, # Keep user dependency
    bse_authenticator: BSEAuthenticatorDependency = None, # Inject BSE Authenticator
    bse_order_placer: BSEOrderPlacerDependency = None # Inject BSE Order Placer
):
    """
    Places a new Lumpsum (Purchase/Redemption) order.
    Integrates with BSE STAR MF SOAP API for order placement.
    Handles camelCase request payload.
    """
    processed_payload = preprocess_payload(payload)
    
    try:
        order_data = schemas.LumpsumOrderCreate(**processed_payload)
    except Exception as e:
        logger.error(f"Lumpsum order validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid lumpsum order payload: {e}"
        )

    # Add user_id to order data if needed for logging or internal use
    order_data.user_id = current_user.user_id
    
    # --- BSE Integration --- 
    try:
        # 1. Get encrypted password (handles auth/re-auth)
        # Passkey might need to come from user profile or config? Using a placeholder for now.
        # TODO: Determine the source of the passkey required by BSEAuthenticator.authenticate
        # Hardcoding a placeholder passkey for now - THIS MUST BE REPLACED
        placeholder_passkey = "PassKey123" 
        if not bse_authenticator.is_session_valid():
             logger.info("BSE session invalid, attempting initial authentication.")
             await bse_authenticator.authenticate(placeholder_passkey)
             
        encrypted_password = await bse_authenticator.get_encrypted_password()

        # 2. Place the order via BSE SOAP API
        bse_response = await bse_order_placer.place_lumpsum_order(order_data, encrypted_password)
        
        # 3. Log the successful BSE interaction (optional)
        logger.info(f"Successfully placed lumpsum order via BSE for RefNo: {order_data.unique_ref_no}")

        # 4. Update internal database record (optional, depending on workflow)
        # If you still want to store the order locally:
        # db_order = crud.create_lumpsum_order(db=db, order=order_data)
        # crud.update_order_status(
        #     db=db, 
        #     order_id=db_order.id, 
        #     status=bse_response.get("message", "PLACED_VIA_BSE"), 
        #     bse_order_id=bse_response.get("bse_order_id"),
        #     bse_remarks=bse_response.get("bse_remarks")
        # )

        # 5. Map BSE response to API response schema
        api_response = schemas.LumpsumOrderResponse(
            message=f'Order successfully placed via BSE: {bse_response.get("message")}',
            order_id=None, # Or db_order.id if storing locally
            unique_ref_no=bse_response.get("unique_ref_no", order_data.unique_ref_no),
            bse_order_id=bse_response.get("bse_order_id"),
            status=bse_response.get("message", "SUCCESS"), # Map BSE status appropriately
            bse_status_code=bse_response.get("status_code"),
            bse_remarks=bse_response.get("bse_remarks")
        )
        return api_response

    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error placing lumpsum order for RefNo {order_data.unique_ref_no}: {e}", exc_info=True)
        # Map specific BSE errors to HTTP status codes
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE # Default for BSE errors
        if isinstance(e, BSEValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(e, BSEAuthError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR # Or 503, as auth failure is critical
        elif isinstance(e, BSEOrderError):
             status_code = status.HTTP_400_BAD_REQUEST # Often order errors are due to bad data
             
        raise HTTPException(status_code=status_code, detail=f"BSE Interaction Failed: {str(e)}")
    except HTTPException as e: # Re-raise HTTP exceptions from dependencies
        raise e
    except Exception as e:
        logger.error(f"Unexpected error placing lumpsum order for RefNo {order_data.unique_ref_no}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")

@router.post("/sip", response_model=schemas.SIPOrderResponse)
async def register_sip_order(
    payload: Dict[str, Any] = Body(...),
    db: DbDependency = None, # Keep DB dependency
    current_user: CurrentUserDependency = None, # Keep user dependency
    bse_authenticator: BSEAuthenticatorDependency = None, # Inject BSE Authenticator
    bse_order_placer: BSEOrderPlacerDependency = None # Inject BSE Order Placer
):
    """
    Registers a new SIP order.
    Integrates with BSE STAR MF SOAP API for SIP registration.
    Handles camelCase request payload.
    """
    processed_payload = preprocess_payload(payload)
    
    try:
        sip_data = schemas.SIPOrderCreate(**processed_payload)
    except Exception as e:
        logger.error(f"SIP order validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid SIP order payload: {e}"
        )

    # Add user_id if needed
    sip_data.user_id = current_user.user_id

    # --- BSE Integration --- 
    try:
        # 1. Get encrypted password
        # TODO: Determine the source of the passkey required by BSEAuthenticator.authenticate
        placeholder_passkey = "PassKey123" # Replace this!
        if not bse_authenticator.is_session_valid():
             logger.info("BSE session invalid, attempting initial authentication.")
             await bse_authenticator.authenticate(placeholder_passkey)
             
        encrypted_password = await bse_authenticator.get_encrypted_password()

        # 2. Place the SIP order via BSE SOAP API
        bse_response = await bse_order_placer.place_sip_order(sip_data, encrypted_password)
        
        # 3. Log success
        logger.info(f"Successfully placed SIP order via BSE for RefNo: {sip_data.unique_ref_no}")

        # 4. Update internal database record (optional)
        # db_sip = crud.create_sip_order(db=db, sip_order=sip_data)
        # crud.update_sip_status(
        #     db=db, 
        #     sip_id=db_sip.id, 
        #     status=bse_response.get("message", "REGISTERED_VIA_BSE"), 
        #     bse_sip_reg_id=bse_response.get("bse_sip_reg_id"),
        #     bse_remarks=bse_response.get("bse_remarks")
        # )

        # 5. Map BSE response to API response schema
        api_response = schemas.SIPOrderResponse(
            message=f'SIP successfully registered via BSE: {bse_response.get("message")}',
            sip_id=None, # Or db_sip.id if storing locally
            unique_ref_no=bse_response.get("unique_ref_no", sip_data.unique_ref_no),
            bse_sip_reg_id=bse_response.get("bse_sip_reg_id"),
            status=bse_response.get("message", "SUCCESS"), # Map BSE status
            bse_status_code=bse_response.get("status_code"),
            bse_remarks=bse_response.get("bse_remarks")
        )
        return api_response

    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error placing SIP order for RefNo {sip_data.unique_ref_no}: {e}", exc_info=True)
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE # Default
        if isinstance(e, BSEValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(e, BSEAuthError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        elif isinstance(e, BSEOrderError):
             status_code = status.HTTP_400_BAD_REQUEST
             
        raise HTTPException(status_code=status_code, detail=f"BSE Interaction Failed: {str(e)}")
    except HTTPException as e: # Re-raise HTTP exceptions from dependencies
        raise e
    except Exception as e:
        logger.error(f"Unexpected error placing SIP order for RefNo {sip_data.unique_ref_no}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")

# TODO: Add endpoints for fetching order status, potentially querying BSE or local DB
# TODO: Add endpoint for client registration if needed, using BSEClientRegistrarDependency

