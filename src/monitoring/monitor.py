from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas
from ..dependencies import get_db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)

class OrderMonitor:
    """Monitor order processing and send alerts for issues."""
    
    def __init__(self, smtp_config: Optional[Dict[str, str]] = None):
        """
        Initialize order monitor.
        
        Args:
            smtp_config: Optional SMTP configuration for email alerts
        """
        self.smtp_config = smtp_config or {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "from_email": os.getenv("ALERT_FROM_EMAIL"),
            "to_email": os.getenv("ALERT_TO_EMAIL")
        }

    async def check_stuck_orders(self, db: Session, threshold_minutes: int = 30) -> List[models.Order]:
        """
        Check for orders stuck in intermediate states.
        
        Args:
            db: Database session
            threshold_minutes: Time threshold for considering an order stuck
            
        Returns:
            List of stuck orders
        """
        threshold_time = datetime.utcnow() - timedelta(minutes=threshold_minutes)
        
        # Define intermediate states
        intermediate_states = [
            "RECEIVED",
            "PAYMENT_INITIATED",
            "PAYMENT_COMPLETED",
            "BSE_PENDING"
        ]
        
        stuck_orders = db.query(models.Order)\
            .filter(
                models.Order.status.in_(intermediate_states),
                models.Order.status_updated_at <= threshold_time
            )\
            .all()
            
        if stuck_orders:
            await self._send_stuck_orders_alert(stuck_orders)
            
        return stuck_orders

    async def check_failed_payments(self, db: Session, time_window_hours: int = 24) -> List[models.Order]:
        """
        Check for orders with failed payments.
        
        Args:
            db: Database session
            time_window_hours: Time window to check for failed payments
            
        Returns:
            List of orders with failed payments
        """
        start_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        failed_orders = db.query(models.Order)\
            .filter(
                models.Order.payment_status.in_(["FAILED", "EXPIRED", "CANCELLED"]),
                models.Order.status_updated_at >= start_time
            )\
            .all()
            
        if failed_orders:
            await self._send_failed_payments_alert(failed_orders)
            
        return failed_orders

    async def check_order_success_rate(
        self,
        db: Session,
        time_window_hours: int = 24,
        threshold_percentage: float = 95.0
    ) -> Dict[str, Any]:
        """
        Monitor order success rate.
        
        Args:
            db: Database session
            time_window_hours: Time window for calculating success rate
            threshold_percentage: Alert threshold for success rate
            
        Returns:
            Dict containing success rate metrics
        """
        start_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        # Get total orders in time window
        total_orders = db.query(func.count(models.Order.id))\
            .filter(models.Order.order_timestamp >= start_time)\
            .scalar()
            
        if not total_orders:
            return {
                "success_rate": 100.0,
                "total_orders": 0,
                "successful_orders": 0,
                "failed_orders": 0
            }
        
        # Get successful orders
        successful_orders = db.query(func.count(models.Order.id))\
            .filter(
                models.Order.order_timestamp >= start_time,
                models.Order.status == "COMPLETED"
            )\
            .scalar()
            
        success_rate = (successful_orders / total_orders) * 100
        
        metrics = {
            "success_rate": success_rate,
            "total_orders": total_orders,
            "successful_orders": successful_orders,
            "failed_orders": total_orders - successful_orders
        }
        
        if success_rate < threshold_percentage:
            await self._send_success_rate_alert(metrics)
            
        return metrics

    async def _send_stuck_orders_alert(self, orders: List[models.Order]):
        """Send alert for stuck orders."""
        subject = "Alert: Stuck Orders Detected"
        body = "The following orders are stuck in intermediate states:\n\n"
        
        for order in orders:
            body += f"Order ID: {order.id}\n"
            body += f"Status: {order.status}\n"
            body += f"Last Updated: {order.status_updated_at}\n"
            body += f"Client Code: {order.client_code}\n"
            body += "---\n"
            
        await self._send_email_alert(subject, body)

    async def _send_failed_payments_alert(self, orders: List[models.Order]):
        """Send alert for failed payments."""
        subject = "Alert: Failed Payments Detected"
        body = "The following orders have failed payments:\n\n"
        
        for order in orders:
            body += f"Order ID: {order.id}\n"
            body += f"Payment Status: {order.payment_status}\n"
            body += f"Payment Reference: {order.payment_reference}\n"
            body += f"Client Code: {order.client_code}\n"
            body += f"Amount: {order.amount}\n"
            body += "---\n"
            
        await self._send_email_alert(subject, body)

    async def _send_success_rate_alert(self, metrics: Dict[str, Any]):
        """Send alert for low success rate."""
        subject = "Alert: Low Order Success Rate"
        body = "Order success rate has dropped below threshold:\n\n"
        body += f"Success Rate: {metrics['success_rate']:.2f}%\n"
        body += f"Total Orders: {metrics['total_orders']}\n"
        body += f"Successful Orders: {metrics['successful_orders']}\n"
        body += f"Failed Orders: {metrics['failed_orders']}\n"
        
        await self._send_email_alert(subject, body)

    async def _send_email_alert(self, subject: str, body: str):
        """Send email alert."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_config["from_email"]
            msg["To"] = self.smtp_config["to_email"]
            msg["Subject"] = subject
            
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)
                
            logger.info(f"Sent alert email: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}", exc_info=True)

# Create singleton monitor instance
order_monitor = OrderMonitor() 