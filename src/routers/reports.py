# /home/ubuntu/order_management_system/src/routers/reports.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime
import logging

from .. import schemas, models, crud, dependencies
from ..database import get_db

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    dependencies=[Depends(dependencies.get_current_active_user)]
)

logger = logging.getLogger(__name__)

@router.get("/order_status", response_model=schemas.EnhancedOrderStatusResponse)
async def get_order_status(
    clientCode: str,
    fromDate: datetime.date,
    toDate: datetime.date,
    memberId: str,
    orderId: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """
    Get enhanced order status with detailed tracking information.
    """
    # Validate if the requesting user is allowed to see this clientCode's orders
    if current_user.member_id != memberId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view orders for this member ID"
        )

    # Validate date range (optional, e.g., limit duration)
    if fromDate > toDate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fromDate cannot be after toDate."
        )

    query_params = schemas.OrderStatusQuery(
        clientCode=clientCode,
        fromDate=fromDate,
        toDate=toDate,
        orderId=orderId,
        status=status
    )

    try:
        orders = crud.get_orders_by_status_query(db=db, query_params=query_params)

        # Map DB models to enhanced Pydantic response schema
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
                    createdBy=hist.user.username if hist.user else "system"
                )
                for hist in status_history
            ]

            order_detail = schemas.EnhancedOrderStatusDetail(
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
                # Enhanced tracking information
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

        return schemas.EnhancedOrderStatusResponse(
            status="Success",
            data=response_data
        )

    except Exception as e:
        logger.error(f"Failed to retrieve order status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order status: {str(e)}"
        )

