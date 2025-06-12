from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import os

from .. import schemas, crud, models
from ..dependencies import get_db, get_current_user
from ..payment.payment_gateway import get_payment_gateway
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/payment",
    tags=["payment"],
    responses={404: {"description": "Not found"}},
)

# Initialize payment gateway
payment_gateway = get_payment_gateway(
    gateway_type="razorpay",
    api_key=os.getenv("RAZORPAY_KEY_ID"),
    api_secret=os.getenv("RAZORPAY_KEY_SECRET")
)

@router.post("/initiate", response_model=schemas.PaymentResponse)
async def initiate_payment(
    payment_request: schemas.PaymentRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Initiate payment for an order.
    """
    # Verify order exists and belongs to the client
    order = crud.get_order(db, order_id=payment_request.order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.client_code != payment_request.client_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Order does not belong to the specified client"
        )

    try:
        # Initiate payment with gateway
        payment_response = await payment_gateway.initiate_payment(payment_request)
        
        # Update order with payment reference
        crud.update_order_status(
            db=db,
            order_id=order.id,
            status="PAYMENT_INITIATED",
            user_id=current_user.id,
            payment_status="INITIATED",
            payment_reference=payment_response.payment_reference
        )
        
        return payment_response

    except ValueError as e:
        logger.error(f"Payment initiation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during payment initiation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payment"
        )

@router.get("/verify/{payment_reference}", response_model=schemas.PaymentVerificationResponse)
async def verify_payment(
    payment_reference: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Verify payment status.
    """
    try:
        # Get payment verification from gateway
        verification_result = await payment_gateway.verify_payment(payment_reference)
        
        # Find order by payment reference
        order = crud.get_order_by_payment_reference(db, payment_reference)
        if order and verification_result["verified"]:
            # Update order status if payment is verified
            crud.update_order_status(
                db=db,
                order_id=order.id,
                status="PAYMENT_COMPLETED",
                user_id=current_user.id,
                payment_status=verification_result["status"],
                payment_date=verification_result.get("payment_time")
            )
        
        return schemas.PaymentVerificationResponse(**verification_result)

    except ValueError as e:
        logger.error(f"Payment verification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during payment verification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment"
        ) 