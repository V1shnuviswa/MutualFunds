from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta

from .. import schemas, models
from ..dependencies import get_db, get_current_active_user
from ..monitoring.monitor import order_monitor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)

@router.get("/stuck-orders")
async def get_stuck_orders(
    threshold_minutes: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get orders stuck in intermediate states.
    """
    try:
        stuck_orders = await order_monitor.check_stuck_orders(
            db=db,
            threshold_minutes=threshold_minutes
        )
        
        return {
            "count": len(stuck_orders),
            "orders": [
                {
                    "order_id": order.id,
                    "status": order.status,
                    "last_updated": order.status_updated_at,
                    "client_code": order.client_code,
                    "amount": str(order.amount)
                }
                for order in stuck_orders
            ]
        }
    except Exception as e:
        logger.error(f"Failed to check stuck orders: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check stuck orders"
        )

@router.get("/failed-payments")
async def get_failed_payments(
    time_window_hours: int = 24,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get orders with failed payments.
    """
    try:
        failed_orders = await order_monitor.check_failed_payments(
            db=db,
            time_window_hours=time_window_hours
        )
        
        return {
            "count": len(failed_orders),
            "orders": [
                {
                    "order_id": order.id,
                    "payment_status": order.payment_status,
                    "payment_reference": order.payment_reference,
                    "client_code": order.client_code,
                    "amount": str(order.amount)
                }
                for order in failed_orders
            ]
        }
    except Exception as e:
        logger.error(f"Failed to check failed payments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check failed payments"
        )

@router.get("/success-rate")
async def get_success_rate(
    time_window_hours: int = 24,
    threshold_percentage: float = 95.0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get order success rate metrics.
    """
    try:
        metrics = await order_monitor.check_order_success_rate(
            db=db,
            time_window_hours=time_window_hours,
            threshold_percentage=threshold_percentage
        )
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to check order success rate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check order success rate"
        ) 