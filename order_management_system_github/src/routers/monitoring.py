from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta

from .. import schemas, models, crud
from ..dependencies import get_db, get_current_user
from ..monitoring.monitor import order_monitor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)

@router.get("/system-status", response_model=Dict[str, Any])
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get the current system status including:
    - Database connection
    - BSE connectivity
    - Payment gateway status
    - Recent orders status
    """
    try:
        # Check database by running a simple query
        db_status = "healthy"
        try:
            # Just get one user to verify DB connection
            _ = crud.get_user_by_id(db, user_id=1)
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check BSE connectivity (simplified for now)
        bse_status = "healthy"
        
        # Check payment gateway status (simplified for now)
        payment_status = "healthy"
        
        # Get recent orders status
        recent_orders = crud.get_recent_orders(db, limit=5)
        orders_status = {
            "total": len(recent_orders),
            "recent": [
                {
                    "id": order.id,
                    "status": order.status,
                    "created_at": order.created_at
                }
                for order in recent_orders
            ]
        }
        
        return {
            "status": "operational",
            "components": {
                "database": db_status,
                "bse_connection": bse_status,
                "payment_gateway": payment_status
            },
            "orders": orders_status
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system status: {str(e)}"
        )

@router.get("/orders-summary", response_model=Dict[str, Any])
async def get_orders_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get a summary of orders by status.
    """
    try:
        # Get counts of orders by status
        status_counts = crud.get_order_status_counts(db)
        
        # Get counts by order type
        type_counts = crud.get_order_type_counts(db)
        
        # Calculate total orders and success rate
        total_orders = sum(count for _, count in status_counts)
        success_rate = 0
        if total_orders > 0:
            completed_orders = next((count for status, count in status_counts if status == "COMPLETED"), 0)
            success_rate = (completed_orders / total_orders) * 100
        
        return {
            "total_orders": total_orders,
            "success_rate": round(success_rate, 2),
            "status_breakdown": {
                status: count for status, count in status_counts
            },
            "type_breakdown": {
                order_type: count for order_type, count in type_counts
            }
        }
    except Exception as e:
        logger.error(f"Error getting orders summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting orders summary: {str(e)}"
        )

@router.get("/client-activity", response_model=List[Dict[str, Any]])
async def get_client_activity(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get client activity summary.
    """
    try:
        # Get client activity
        client_activity = crud.get_client_activity(db)
        
        return [
            {
                "client_code": activity.client_code,
                "client_name": activity.client_name,
                "total_orders": activity.total_orders,
                "last_order_date": activity.last_order_date,
                "total_investment": float(activity.total_investment) if activity.total_investment else 0,
                "active_sips": activity.active_sips
            }
            for activity in client_activity
        ]
    except Exception as e:
        logger.error(f"Error getting client activity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting client activity: {str(e)}"
        )

@router.get("/stuck-orders")
async def get_stuck_orders(
    threshold_minutes: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
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
    current_user: models.User = Depends(get_current_user)
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
    current_user: models.User = Depends(get_current_user)
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