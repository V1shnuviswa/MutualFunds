# /home/ubuntu/order_management_system/src/routers/orders.py

import logging
from typing import List, Any, Dict, Optional
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, status, Body, Depends, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, model_validator, ConfigDict
import logging

logger = logging.getLogger(__name__)

from .. import crud, models, schemas
from ..database import get_db
from ..dependencies import (
    get_current_user,
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
    generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}"
)

from fastapi import Body

@router.post("/lumpsum", response_model=schemas.LumpsumOrderResponse)
async def place_lumpsum_order(
    order: schemas.LumpsumOrderRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer),
    bse_soap_handler = Depends(get_bse_soap_handler)
):
    """Place a lumpsum order"""
    print("DEBUG: Inside place_lumpsum_order endpoint. All dependencies should be resolved.")
    
    try:
        # Step 1: Convert to dict
        payload = order.model_dump()
        processed_payload = payload

        logger.info(f"Processing lumpsum order request: {processed_payload}")

        # Step 2: Add required contextual fields
        processed_payload["transaction_code"] = "NEW"
        processed_payload["user_id"] = current_user.user_id
        processed_payload["member_id"] = current_user.member_id

        # Step 3: Validate all mandatory fields
        required_fields = [
            "TransCode", "TransNo", "UserID", "MemberId", "ClientCode", 
            "SchemeCd", "BuySell", "BuySellType", "DPTxn", "AllRedeem",
            "KYCStatus", "EUINFlag", "MinRedeem", "DPC",
            "Password", "PassKey", "Amount"
        ]
        
        # Check all mandatory fields are present
        for field in required_fields:
            if field not in processed_payload or not processed_payload[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
                
        # Validate Amount/Qty requirement (either one must be present)
        if not processed_payload.get("Amount") and not processed_payload.get("Qty"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either Amount or Qty must be provided"
            )

        # Step 4: Save order to DB
        db_order = crud.create_lumpsum_order(
            db=db,
            order_data=processed_payload,
            user_id=current_user.id
        )
        logger.info(f"Created lumpsum order in database with ID: {db_order.id}")

        # Step 5: Try BSE integration (gracefully handle failures)
        try:
            # Get encrypted password
            encrypted_password = await bse_authenticator.get_encrypted_password()
            
            # Create SOAP request with all mandatory fields
            soap_request = bse_soap_handler.create_purchase_request({
                # Mandatory fields
                "TransCode": order.TransCode,
                "TransNo": order.TransNo,
                "OrderId": "",  # Optional for new orders
                "UserID": order.UserID,
                "MemberId": order.MemberId,
                "ClientCode": order.ClientCode,
                "SchemeCd": order.SchemeCd,
                "BuySell": order.BuySell,
                "BuySellType": order.BuySellType,
                "DPTxn": order.DPTxn,
                "OrderVal": str(order.Amount if order.Amount is not None else ""),  # Amount maps to OrderVal in BSE API
                "Qty": str(order.Qty if order.Qty is not None else ""),
                "AllRedeem": order.AllRedeem,
                "KYCStatus": order.KYCStatus,
                "EUINVal": order.EUINFlag,
                "MinRedeem": order.MinRedeem,
                "DPC": order.DPC,
                "IPAdd": order.IPAdd,
                "Password": encrypted_password,
                "PassKey": order.PassKey,
                
                # Optional fields
                "FolioNo": order.FolioNo or "",
                "Remarks": order.Remarks or "",
                "RefNo": order.RefNo,  # Use RefNo from order request
                "SubBrCode": order.SubBrokerARN or "",
                "EUIN": order.EUIN or "",
                "MobileNo": order.MobileNo or "",
                "EmailID": order.EmailID or "",
                "MandateID": order.MandateID or "",
                
                # Required by WSDL but can be empty
                "Parma1": "",
                "Param2": "",
                "Param3": "",
                "Filler1": "",
                "Filler2": "",
                "Filler3": "",
                "Filler4": "",
                "Filler5": "",
                "Filler6": ""
            })

            # Update DB status
            crud.update_order_status(
                db=db,
                order_id=db_order.id,
                status="SENT_TO_BSE",
                user_id=current_user.id,
                remarks="Order sent to BSE"
            )

            # Send to BSE
            bse_response = await bse_order_placer.place_lumpsum_order(order, encrypted_password)
            parsed_response = bse_soap_handler.parse_order_response(bse_response)

            # Update final status
            new_status = "ACCEPTED_BY_BSE" if parsed_response.success else "REJECTED_BY_BSE"

            
            update_kwargs = {
                "db": db,
                "order_id": db_order.id,
                "status": new_status,
                "user_id": current_user.id,
                "status_code": parsed_response.success_flag,
                "remarks": parsed_response.bse_remarks
            }

            # Conditionally add order_id_bse only if valid (not "0" or empty)
            if parsed_response.order_number and parsed_response.order_number != "0":
                update_kwargs["order_id_bse"] = parsed_response.order_number

            crud.update_order_status(**update_kwargs)

            return schemas.LumpsumOrderResponse(
                message=parsed_response.bse_remarks,
                order_id=str(db_order.id),
                unique_ref_no=order.TransNo,
                bse_order_id=parsed_response.order_number,
                status="SUCCESS" if parsed_response.success_flag == "Y" else "FAILED",
                bse_status_code=parsed_response.success_flag,
                bse_remarks=parsed_response.bse_remarks
            )

        except Exception as bse_error:
            logger.warning(f"BSE integration failed: {str(bse_error)}")
            
            # Update order status to indicate BSE failure
            crud.update_order_status(
                db=db,
                order_id=db_order.id,
                status="BSE_ERROR",
                user_id=current_user.id,
                remarks=f"BSE integration failed: {str(bse_error)}"
            )

            # Return success response indicating order was saved but BSE failed
            return schemas.LumpsumOrderResponse(
                message="Order saved successfully but BSE integration failed",
                order_id=str(db_order.id),
                unique_ref_no=order.TransNo,
                bse_order_id="",
                status="PENDING",
                bse_status_code="0",
                bse_remarks=f"BSE integration error: {str(bse_error)}"
            )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/sip", response_model=schemas.SIPOrderResponse)
async def register_sip_order(
    order: schemas.SIPOrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    print("DEBUG: Inside register_sip_order endpoint. All dependencies should be resolved.")
    """
    Registers a new SIP order.
    Integrates with BSE STAR MF SOAP API for SIP registration.
    """
    try:
        # Use order directly - BSEOrderPlacer will use its own user_id
        sip_data = order

        logger.info(f"Processing SIP order request: {sip_data.unique_ref_no}")

        # Step 1: Save order to DB first
        db_order = crud.create_sip_registration_order(db=db, sip_data=sip_data, user_id=current_user.id)
        logger.info(f"Created SIP order in database with ID: {db_order.id}")

        # Step 2: Try BSE integration (gracefully handle failures)
        try:
            # Get encrypted password
            encrypted_password = await bse_authenticator.get_encrypted_password()

            # Place the SIP order via BSE SOAP API
            bse_response = await bse_order_placer.place_sip_order(sip_data, encrypted_password)
            
            logger.info(f"Successfully placed SIP order via BSE for RefNo: {sip_data.unique_ref_no}")
            
            if bse_response.success:
                # Update with BSE registration ID
                crud.update_sip_status(
                    db=db, 
                    sip_reg_id=db_order.sip_registration.id, 
                    bse_sip_reg_id=bse_response.order_id, 
                    status="REGISTERED_WITH_BSE"
                )
                
                # Update order status
                crud.update_order_status(
                    db=db,
                    order_id=db_order.id,
                    status="ACCEPTED_BY_BSE",
                    user_id=current_user.id,
                    status_code=bse_response.status_code,
                    remarks=bse_response.message
                )
            else:
                # Update with failure information
                crud.update_order_status(
                    db=db,
                    order_id=db_order.id,
                    status="REJECTED_BY_BSE",
                    user_id=current_user.id,
                    status_code=bse_response.status_code,
                    remarks=bse_response.message
                )

            # Return successful response
            return schemas.SIPOrderResponse(
                message=f'SIP successfully registered via BSE: {bse_response.message}',
                sip_id=str(db_order.sip_registration.id),
                unique_ref_no=sip_data.unique_ref_no,
                bse_sip_reg_id=bse_response.order_id,
                status="SUCCESS" if bse_response.success else "FAILED",
                bse_status_code=bse_response.status_code,
                bse_remarks=bse_response.details.get("bse_remarks", "")
            )

        except Exception as bse_error:
            logger.warning(f"BSE integration failed for SIP order: {str(bse_error)}")
            
            # Update order status to indicate BSE failure
            crud.update_order_status(
                db=db,
                order_id=db_order.id,
                status="BSE_ERROR",
                user_id=current_user.id,
                remarks=f"BSE integration failed: {str(bse_error)}"
            )

            # Return success response indicating order was saved but BSE failed
            return schemas.SIPOrderResponse(
                message="SIP order saved successfully but BSE integration failed",
                sip_id=str(db_order.sip_registration.id),
                unique_ref_no=sip_data.unique_ref_no,
                bse_sip_reg_id="",
                status="PENDING",
                bse_status_code="0",
                bse_remarks=f"BSE integration error: {str(bse_error)}"
            )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error placing SIP order for RefNo {sip_data.unique_ref_no}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")

@router.post("/switch", response_model=schemas.SwitchOrderResponse)
async def place_switch_order(
    order: schemas.SwitchOrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer),
    bse_soap_handler = Depends(get_bse_soap_handler)
):
    """Place a switch order between schemes"""
    try:
        # BSEOrderPlacer will use its own user_id
        
        # Get encrypted password
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Place switch order
        bse_response = await bse_order_placer.place_switch_order(order, encrypted_password)
        
        return schemas.SwitchOrderResponse(
            message=bse_response.message,
            order_id=bse_response.order_id,
            unique_ref_no=order.unique_ref_no,
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
    order: schemas.SpreadOrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer),
    bse_soap_handler = Depends(get_bse_soap_handler)
):
    """Place a spread order"""
    try:
        # BSEOrderPlacer will use its own user_id
        
        # Get encrypted password
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Place spread order
        bse_response = await bse_order_placer.place_spread_order(order, encrypted_password)
        
        return schemas.SpreadOrderResponse(
            message=bse_response.message,
            order_id=bse_response.order_id,
            unique_ref_no=order.unique_ref_no,
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
    order: schemas.SIPOrderModify,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    """Modify an existing SIP registration"""
    try:
        # Create a new order with the sip_reg_id - we need to handle this differently
        # since we can't mutate Pydantic models
        order_dict = order.model_dump()
        order_dict['sip_reg_id'] = sip_reg_id
        order_dict['user_id'] = current_user.user_id
        modified_order = schemas.SIPOrderModify(**order_dict)
        
        # Get encrypted password
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Modify SIP
        bse_response = await bse_order_placer.modify_sip_order(modified_order, encrypted_password)
        
        return schemas.SIPOrderResponse(
            message=f"SIP modification successful: {bse_response.message}",
            sip_id=sip_reg_id,
            unique_ref_no=modified_order.unique_ref_no,
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
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

@router.get("", response_model=List[schemas.OrderStatusResponse])
async def get_orders(
    client_code: Optional[str] = None,
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve a list of all orders for a user (open, executed, canceled).
    Supports filtering by client code, status, order type, and date range.
    """
    try:
        # Set default date range if not provided (last 30 days)
        if not from_date:
            from_date = date.today() - timedelta(days=30)
        if not to_date:
            to_date = date.today()
            
        # Get orders from database
        orders = crud.get_filtered_orders(
            db=db,
            client_code=client_code,
            status=status,
            order_type=order_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
            user_id=current_user.id
        )
        
        # Map to response schema
        response_data = []
        for order in orders:
            # Get status history for the order
            status_history = crud.get_order_status_history(db=db, order_id=order.id)
            
            # Map status history to response schema
            status_history_data = [
                schemas.OrderStatusHistoryResponse(
                    status=hist.status,
                    remarks=hist.remarks,
                    createdAt=hist.created_at,
                    createdBy=hist.user.user_id if hist.user else "system"
                )
                for hist in status_history
            ]
            
            order_detail = schemas.OrderStatusResponse(
                internalOrderId=order.id,
                orderId=order.order_id_bse,
                uniqueRefNo=order.unique_ref_no,
                orderDate=order.order_timestamp.date(),
                orderTime=order.order_timestamp.strftime("%H:%M:%S"),
                clientCode=order.client_code,
                clientName=order.client.client_name if order.client else None,
                schemeCode=order.scheme_code,
                schemeName=order.scheme.scheme_name if order.scheme else None,
                orderType=order.order_type,
                transactionType=order.transaction_type,
                amount=order.amount,
                quantity=order.quantity,
                folioNo=order.folio_no,
                orderStatus=order.status,
                paymentStatus=order.payment_status,
                paymentReference=order.payment_reference,
                paymentDate=order.payment_date,
                allotmentDate=order.allotment_date,
                allotmentNav=order.allotment_nav,
                unitsAllotted=order.units_allotted,
                settlementDate=order.settlement_date,
                settlementAmount=order.settlement_amount,
                statusHistory=status_history_data,
                remarks=order.bse_remarks
            )
            response_data.append(order_detail)
            
        return response_data
        
    except Exception as e:
        logger.error(f"Error retrieving orders: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve orders: {str(e)}"
        )

@router.get("/history", response_model=List[schemas.OrderStatusResponse])
async def get_order_history(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    client_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    """
    Fetch order history for the specified date range (defaults to last 30 days).
    This endpoint combines local database records with BSE order status.
    """
    try:
        # Set default date range if not provided (last 30 days)
        if not from_date:
            from_date = date.today() - timedelta(days=30)
        if not to_date:
            to_date = date.today()
            
        # Get encrypted password for BSE authentication
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Get order history from BSE
        bse_response = await bse_order_placer.get_orders_by_criteria(
            from_date=from_date,
            to_date=to_date,
            client_code=client_code,
            transaction_type=None,
            order_type=None,
            sub_order_type=None,
            settlement_type=None,
            encrypted_password=encrypted_password
        )
        
        # Get orders from local database
        orders = crud.get_filtered_orders(
            db=db,
            client_code=client_code,
            from_date=from_date,
            to_date=to_date,
            user_id=current_user.id
        )
        
        # Map to response schema (same as get_orders)
        response_data = []
        for order in orders:
            # Get status history for the order
            status_history = crud.get_order_status_history(db=db, order_id=order.id)
            
            # Map status history to response schema
            status_history_data = [
                schemas.OrderStatusHistoryResponse(
                    status=hist.status,
                    remarks=hist.remarks,
                    createdAt=hist.created_at,
                    createdBy=hist.user.user_id if hist.user else "system"
                )
                for hist in status_history
            ]
            
            order_detail = schemas.OrderStatusResponse(
                internalOrderId=order.id,
                orderId=order.order_id_bse,
                uniqueRefNo=order.unique_ref_no,
                orderDate=order.order_timestamp.date(),
                orderTime=order.order_timestamp.strftime("%H:%M:%S"),
                clientCode=order.client_code,
                clientName=order.client.client_name if order.client else None,
                schemeCode=order.scheme_code,
                schemeName=order.scheme.scheme_name if order.scheme else None,
                orderType=order.order_type,
                transactionType=order.transaction_type,
                amount=order.amount,
                quantity=order.quantity,
                folioNo=order.folio_no,
                orderStatus=order.status,
                paymentStatus=order.payment_status,
                paymentReference=order.payment_reference,
                paymentDate=order.payment_date,
                allotmentDate=order.allotment_date,
                allotmentNav=order.allotment_nav,
                unitsAllotted=order.units_allotted,
                settlementDate=order.settlement_date,
                settlementAmount=order.settlement_amount,
                statusHistory=status_history_data,
                remarks=order.bse_remarks
            )
            response_data.append(order_detail)
            
        return response_data
        
    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error retrieving order history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving order history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order history: {str(e)}"
        )

@router.get("/{order_id}", response_model=schemas.OrderStatusResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    """
    Retrieve order details by order ID.
    """
    try:
        # Get order from database
        db_order = crud.get_order(db, order_id=order_id)
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
            
        # Get encrypted password for BSE authentication
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Get latest order status from BSE if order_id_bse exists
        bse_status = None
        if db_order.order_id_bse:
            try:
                bse_response = await bse_order_placer.get_order_status(
                    order_id=db_order.order_id_bse,
                    client_code=db_order.client_code,
                    encrypted_password=encrypted_password
                )
                bse_status = bse_response.details
            except Exception as e:
                logger.warning(f"Could not fetch BSE status for order {order_id}: {e}")
        
        # Get status history for the order
        status_history = crud.get_order_status_history(db=db, order_id=db_order.id)
        
        # Map status history to response schema
        status_history_data = [
            schemas.OrderStatusHistoryResponse(
                status=hist.status,
                remarks=hist.remarks,
                createdAt=hist.created_at,
                createdBy=hist.user.user_id if hist.user else "system"
            )
            for hist in status_history
        ]
        
        # Map to response schema
        return schemas.OrderStatusResponse(
            internalOrderId=db_order.id,
            orderId=db_order.order_id_bse,
            uniqueRefNo=db_order.unique_ref_no,
            orderDate=db_order.order_timestamp.date(),
            orderTime=db_order.order_timestamp.strftime("%H:%M:%S"),
            clientCode=db_order.client_code,
            clientName=db_order.client.client_name if db_order.client else None,
            schemeCode=db_order.scheme_code,
            schemeName=db_order.scheme.scheme_name if db_order.scheme else None,
            orderType=db_order.order_type,
            transactionType=db_order.transaction_type,
            amount=db_order.amount,
            quantity=db_order.quantity,
            folioNo=db_order.folio_no,
            orderStatus=db_order.status,
            paymentStatus=db_order.payment_status,
            paymentReference=db_order.payment_reference,
            paymentDate=db_order.payment_date,
            allotmentDate=db_order.allotment_date,
            allotmentNav=db_order.allotment_nav,
            unitsAllotted=db_order.units_allotted,
            settlementDate=db_order.settlement_date,
            settlementAmount=db_order.settlement_amount,
            statusHistory=status_history_data,
            remarks=db_order.bse_remarks
        )
        
    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error retrieving order details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving order details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order details: {str(e)}"
        )

@router.put("/{order_id}", response_model=schemas.OrderStatusResponse)
async def update_order(
    order_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Modify an existing order.
    Note: Only certain fields can be modified depending on the order status.
    """
    try:
        # Get order from database
        db_order = crud.get_order(db, order_id=order_id)
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
            
        # Check if order can be modified
        if db_order.status not in ["RECEIVED", "PENDING"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order with status '{db_order.status}' cannot be modified"
            )
            
        # Process payload
        processed_payload = preprocess_payload(payload)
        
        # Update order
        updated_order = crud.update_order(
            db=db,
            order_id=order_id,
            order_data=processed_payload,
            user_id=current_user.id
        )
        
        # Get status history for the updated order
        status_history = crud.get_order_status_history(db=db, order_id=updated_order.id)
        
        # Map status history to response schema
        status_history_data = [
            schemas.OrderStatusHistoryResponse(
                status=hist.status,
                remarks=hist.remarks,
                createdAt=hist.created_at,
                createdBy=hist.user.user_id if hist.user else "system"
            )
            for hist in status_history
        ]
        
        # Map to response schema
        return schemas.OrderStatusResponse(
            internalOrderId=updated_order.id,
            orderId=updated_order.order_id_bse,
            uniqueRefNo=updated_order.unique_ref_no,
            orderDate=updated_order.order_timestamp.date(),
            orderTime=updated_order.order_timestamp.strftime("%H:%M:%S"),
            clientCode=updated_order.client_code,
            clientName=updated_order.client.client_name if updated_order.client else None,
            schemeCode=updated_order.scheme_code,
            schemeName=updated_order.scheme.scheme_name if updated_order.scheme else None,
            orderType=updated_order.order_type,
            transactionType=updated_order.transaction_type,
            amount=updated_order.amount,
            quantity=updated_order.quantity,
            folioNo=updated_order.folio_no,
            orderStatus=updated_order.status,
            paymentStatus=updated_order.payment_status,
            paymentReference=updated_order.payment_reference,
            paymentDate=updated_order.payment_date,
            allotmentDate=updated_order.allotment_date,
            allotmentNav=updated_order.allotment_nav,
            unitsAllotted=updated_order.units_allotted,
            settlementDate=updated_order.settlement_date,
            settlementAmount=updated_order.settlement_amount,
            statusHistory=status_history_data,
            remarks=updated_order.bse_remarks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order: {str(e)}"
        )

@router.get("/sips", response_model=List[schemas.SIPOrderResponse])
async def get_sip_orders(
    client_code: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve all active SIP orders.
    Supports filtering by client code and status.
    """
    try:
        # Get SIP registrations from database
        sip_registrations = crud.get_sip_registrations(
            db=db,
            client_code=client_code,
            status=status,
            limit=limit,
            offset=offset,
            user_id=current_user.id
        )
        
        # Map to response schema
        response_data = []
        for sip in sip_registrations:
            sip_response = schemas.SIPOrderResponse(
                message="SIP registration details",
                sip_id=str(sip.id),
                unique_ref_no=sip.order.unique_ref_no if sip.order else None,
                bse_sip_reg_id=sip.sip_reg_id_bse,
                status=sip.status,
                bse_status_code=None,  # Not available in local DB
                bse_remarks=None       # Not available in local DB
            )
            response_data.append(sip_response)
            
        return response_data
        
    except Exception as e:
        logger.error(f"Error retrieving SIP orders: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve SIP orders: {str(e)}"
        )

@router.get("/sips/{sip_id}", response_model=schemas.SIPDetailResponse)
async def get_sip_details(
    sip_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    """
    Retrieve details of a specific SIP registration.
    """
    try:
        # Get SIP registration from database
        sip = crud.get_sip_registration(db=db, sip_id=sip_id)
        if not sip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIP registration not found"
            )
            
        # Get encrypted password for BSE authentication
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Get latest SIP status from BSE if sip_reg_id_bse exists
        bse_status = None
        if sip.sip_reg_id_bse:
            try:
                # This is a placeholder - you would need to implement the actual BSE API call
                # bse_response = await bse_order_placer.get_sip_status(
                #     sip_reg_id=sip.sip_reg_id_bse,
                #     client_code=sip.client_code,
                #     encrypted_password=encrypted_password
                # )
                # bse_status = bse_response.details
                pass
            except Exception as e:
                logger.warning(f"Could not fetch BSE status for SIP {sip_id}: {e}")
        
        # Map to response schema
        return schemas.SIPDetailResponse(
            sipId=str(sip.id),
            bseSipRegId=sip.sip_reg_id_bse,
            clientCode=sip.client_code,
            clientName=sip.client.client_name if sip.client else None,
            schemeCode=sip.scheme_code,
            schemeName=sip.scheme.scheme_name if sip.scheme else None,
            frequency=sip.frequency,
            amount=sip.amount,
            installments=sip.installments,
            startDate=sip.start_date,
            endDate=sip.end_date,
            mandateId=sip.mandate_id,
            firstOrderToday=sip.first_order_today == "Y" if sip.first_order_today else False,
            status=sip.status,
            createdAt=sip.created_at,
            updatedAt=sip.updated_at,
            orderId=str(sip.order.id) if sip.order else None,
            orderStatus=sip.order.status if sip.order else None
        )
        
    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error retrieving SIP details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving SIP details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve SIP details: {str(e)}"
        )

@router.get("/client/{client_code}/status", response_model=List[schemas.OrderStatusResponse])
async def get_client_order_status(
    client_code: str,
    from_date: Optional[date] = Query(None, description="Start date for order search (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date for order search (YYYY-MM-DD)"),
    order_type: Optional[str] = Query(None, description="Filter by order type (ALL/MFD/SIP/XSIP/STP/SWP)"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    """
    Retrieve order status for a specific client code.
    This endpoint combines local database records with BSE order status.
    """
    try:
        # Set default date range if not provided (last 30 days)
        if not from_date:
            from_date = date.today() - timedelta(days=30)
        if not to_date:
            to_date = date.today()
            
        logger.info(f"Fetching order status for client {client_code} from {from_date} to {to_date}")
        
        # Get orders from local database first
        orders = crud.get_filtered_orders(
            db=db,
            client_code=client_code,
            status=status,
            order_type=order_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
            user_id=current_user.id
        )
        
        # Try to get updated status from BSE
        bse_orders = []
        try:
            # Get encrypted password for BSE authentication
            encrypted_password = await bse_authenticator.get_encrypted_password()
            
            # Get order history from BSE
            bse_response = await bse_order_placer.get_orders_by_criteria(
                from_date=from_date,
                to_date=to_date,
                client_code=client_code,
                transaction_type=None,
                order_type=order_type,
                sub_order_type=None,
                settlement_type=None,
                encrypted_password=encrypted_password
            )
            
            if bse_response.success:
                logger.info(f"Successfully retrieved BSE order status for client {client_code}")
                # Parse BSE response if needed
                # bse_orders = parse_bse_order_response(bse_response.details)
            else:
                logger.warning(f"BSE order status retrieval failed: {bse_response.message}")
                
        except Exception as bse_error:
            logger.warning(f"Could not fetch BSE order status for client {client_code}: {str(bse_error)}")
        
        # Map to response schema
        response_data = []
        for order in orders:
            # Get status history for the order
            status_history = crud.get_order_status_history(db=db, order_id=order.id)
            
            # Map status history to response schema
            status_history_data = [
                schemas.OrderStatusHistoryResponse(
                    status=hist.status,
                    remarks=hist.remarks,
                    createdAt=hist.created_at,
                    createdBy=hist.user.user_id if hist.user else "system"
                )
                for hist in status_history
            ]
            
            order_detail = schemas.OrderStatusResponse(
                internalOrderId=order.id,
                orderId=order.order_id_bse,
                uniqueRefNo=order.unique_ref_no,
                orderDate=order.order_timestamp.date(),
                orderTime=order.order_timestamp.strftime("%H:%M:%S"),
                clientCode=order.client_code,
                clientName=order.client.client_name if order.client else None,
                schemeCode=order.scheme_code,
                schemeName=order.scheme.scheme_name if order.scheme else None,
                orderType=order.order_type,
                transactionType=order.transaction_type,
                amount=order.amount,
                quantity=order.quantity,
                folioNo=order.folio_no,
                orderStatus=order.status,
                paymentStatus=order.payment_status,
                paymentReference=order.payment_reference,
                paymentDate=order.payment_date,
                allotmentDate=order.allotment_date,
                allotmentNav=order.allotment_nav,
                unitsAllotted=order.units_allotted,
                settlementDate=order.settlement_date,
                settlementAmount=order.settlement_amount,
                statusHistory=status_history_data,
                remarks=order.bse_remarks
            )
            response_data.append(order_detail)
            
        logger.info(f"Retrieved {len(response_data)} orders for client {client_code}")
        return response_data
        
    except (BSEAuthError, BSEOrderError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error retrieving client order status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving client order status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve client order status: {str(e)}"
        )

# TODO: Add endpoints for fetching order status, potentially querying BSE or local DB
# TODO: Add endpoint for client registration if needed, using BSEClientRegistrarDependency

