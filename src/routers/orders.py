# /home/ubuntu/order_management_system/src/routers/orders.py

import logging
from typing import List, Any, Dict

from fastapi import APIRouter, HTTPException, status, Body, Depends
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..dependencies import (
    DbDependency, CurrentUserDependency,
    get_bse_authenticator, get_bse_order_placer, get_bse_soap_handler
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
    db: Session = Depends(DbDependency),
    current_user: models.User = Depends(CurrentUserDependency),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer),
    bse_soap_handler = Depends(get_bse_soap_handler)
):
    """Place a lumpsum order"""
    try:
        # Preprocess and validate payload
        order_data = schemas.LumpsumOrderCreate(**preprocess_payload(payload))
        
        # Get encrypted password
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Create SOAP request using handler
        soap_request = bse_soap_handler.create_purchase_request({
            "TransCode": "NEW",
            "TransNo": order_data.unique_ref_no,
            "OrderId": "",
            "UserID": bse_order_placer.user_id,
            "MemberId": bse_order_placer.member_id,
            "ClientCode": order_data.client_code,
            "SchemeCd": order_data.scheme_code,
            "BuySell": "P" if order_data.transaction_type == "PURCHASE" else "R",
            "BuySellType": "FRESH",
            "DPTxn": order_data.dp_txn_mode,
            "OrderVal": str(order_data.amount or ""),
            "Qty": str(order_data.quantity or ""),
            "AllRedeem": "Y" if order_data.all_units_flag else "N",
            "FolioNo": order_data.folio_no or "",
            "KYCStatus": order_data.kyc_status or "N",
            "Password": encrypted_password
        })
        
        # Place order
        bse_response = await bse_order_placer.place_lumpsum_order(order_data, encrypted_password)
        
        # Parse response
        parsed_response = bse_soap_handler.parse_order_response(bse_response)
        
        return schemas.LumpsumOrderResponse(
            message=parsed_response.bse_remarks,
            order_id=parsed_response.order_number,
            unique_ref_no=order_data.unique_ref_no,
            bse_order_id=parsed_response.order_number,
            status="SUCCESS" if parsed_response.success_flag == "1" else "FAILED",
            bse_status_code=parsed_response.success_flag,
            bse_remarks=parsed_response.bse_remarks
        )
        
    except BSEAuthError as e:
        logger.error(f"BSE Authentication error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except BSEValidationError as e:
        logger.error(f"BSE Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except (BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Communication error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except BSEOrderError as e:
        logger.error(f"BSE Order error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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

@router.post("/switch", response_model=schemas.SwitchOrderResponse)
async def place_switch_order(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(DbDependency),
    current_user: models.User = Depends(CurrentUserDependency),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer),
    bse_soap_handler = Depends(get_bse_soap_handler)
):
    """Place a switch order between schemes"""
    try:
        # Preprocess and validate payload
        order_data = schemas.SwitchOrderCreate(**preprocess_payload(payload))
        
        # Get encrypted password
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Place switch order
        bse_response = await bse_order_placer.place_switch_order(order_data, encrypted_password)
        
        return schemas.SwitchOrderResponse(
            message=bse_response.message,
            order_id=bse_response.order_id,
            unique_ref_no=order_data.unique_ref_no,
            bse_order_id=bse_response.order_id,
            status="SUCCESS" if bse_response.success else "FAILED",
            bse_status_code=bse_response.status_code,
            bse_remarks=bse_response.details.get("bse_remarks", "")
        )
        
    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error placing switch order: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.post("/spread", response_model=schemas.SpreadOrderResponse)
async def place_spread_order(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(DbDependency),
    current_user: models.User = Depends(CurrentUserDependency),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer),
    bse_soap_handler = Depends(get_bse_soap_handler)
):
    """Place a spread order"""
    try:
        # Preprocess and validate payload
        order_data = schemas.SpreadOrderCreate(**preprocess_payload(payload))
        
        # Get encrypted password
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Place spread order
        bse_response = await bse_order_placer.place_spread_order(order_data, encrypted_password)
        
        return schemas.SpreadOrderResponse(
            message=bse_response.message,
            order_id=bse_response.order_id,
            unique_ref_no=order_data.unique_ref_no,
            bse_order_id=bse_response.order_id,
            status="SUCCESS" if bse_response.success else "FAILED",
            bse_status_code=bse_response.status_code,
            bse_remarks=bse_response.details.get("bse_remarks", "")
        )
        
    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error placing spread order: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.post("/sip/{sip_reg_id}/modify", response_model=schemas.SIPOrderResponse)
async def modify_sip_order(
    sip_reg_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(DbDependency),
    current_user: models.User = Depends(CurrentUserDependency),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    """Modify an existing SIP registration"""
    try:
        # Preprocess and validate payload
        modify_data = schemas.SIPOrderModify(
            sip_reg_id=sip_reg_id,
            **preprocess_payload(payload)
        )
        
        # Get encrypted password
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Modify SIP
        bse_response = await bse_order_placer.modify_sip_order(modify_data, encrypted_password)
        
        return schemas.SIPOrderResponse(
            message=f"SIP modification successful: {bse_response.message}",
            sip_id=sip_reg_id,
            unique_ref_no=modify_data.unique_ref_no,
            bse_sip_reg_id=bse_response.order_id,
            status="SUCCESS" if bse_response.success else "FAILED",
            bse_status_code=bse_response.status_code,
            bse_remarks=bse_response.details.get("bse_remarks", "")
        )
        
    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error modifying SIP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.delete("/sip/{sip_reg_id}", response_model=schemas.SIPOrderResponse)
async def cancel_sip_order(
    sip_reg_id: str,
    client_code: str = Query(..., description="Client code for validation"),
    db: Session = Depends(DbDependency),
    current_user: models.User = Depends(CurrentUserDependency),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    """Cancel a SIP registration"""
    try:
        # Get encrypted password
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Cancel SIP
        bse_response = await bse_order_placer.cancel_sip_order(sip_reg_id, client_code, encrypted_password)
        
        return schemas.SIPOrderResponse(
            message=f"SIP cancellation successful: {bse_response.message}",
            sip_id=sip_reg_id,
            status="SUCCESS" if bse_response.success else "FAILED",
            bse_status_code=bse_response.status_code,
            bse_remarks=bse_response.details.get("bse_remarks", "")
        )
        
    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error cancelling SIP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.delete("/{order_id}", response_model=schemas.OrderCancellationResponse)
async def cancel_order(
    order_id: str,
    client_code: str = Query(..., description="Client code for validation"),
    db: Session = Depends(DbDependency),
    current_user: models.User = Depends(CurrentUserDependency),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    """Cancel any type of order"""
    try:
        # Verify order exists and belongs to client
        db_order = crud.get_order(db, order_id=order_id)
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if db_order.client_code != client_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Order does not belong to the specified client"
            )
        
        # Get encrypted password
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Cancel order
        bse_response = await bse_order_placer.cancel_order(order_id, client_code, encrypted_password)
        
        # Update order status in DB
        crud.update_order_status(
            db=db,
            order_id=db_order.id,
            status="CANCELLED",
            user_id=current_user.id,
            remarks=f"Order cancelled via BSE: {bse_response.message}"
        )
        
        return schemas.OrderCancellationResponse(
            message=f"Order cancellation successful: {bse_response.message}",
            order_id=order_id,
            status="SUCCESS" if bse_response.success else "FAILED",
            bse_status_code=bse_response.status_code,
            bse_remarks=bse_response.details.get("bse_remarks", "")
        )
        
    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error cancelling order: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

# TODO: Add endpoints for fetching order status, potentially querying BSE or local DB
# TODO: Add endpoint for client registration if needed, using BSEClientRegistrarDependency

