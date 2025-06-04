from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal
import logging
from ..schemas import PaymentRequest, PaymentResponse
from ..models import Order

logger = logging.getLogger(__name__)

class PaymentGateway(ABC):
    """Abstract base class for payment gateway integration."""
    
    @abstractmethod
    async def initiate_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Initiate a payment transaction."""
        pass

    @abstractmethod
    async def verify_payment(self, payment_reference: str) -> Dict[str, Any]:
        """Verify payment status."""
        pass

class RazorpayGateway(PaymentGateway):
    """Razorpay payment gateway implementation."""
    
    def __init__(self, api_key: str, api_secret: str):
        """Initialize Razorpay client."""
        try:
            import razorpay
            self.client = razorpay.Client(auth=(api_key, api_secret))
            logger.info("Razorpay client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {e}", exc_info=True)
            raise ValueError(f"Failed to initialize Razorpay client: {str(e)}")

    async def initiate_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """
        Create a Razorpay order for payment.
        
        Args:
            payment_request: Payment details including amount and order info
            
        Returns:
            PaymentResponse with payment gateway details
        """
        try:
            # Create Razorpay order
            order_data = {
                "amount": int(payment_request.amount * 100),  # Convert to paise
                "currency": "INR",
                "receipt": payment_request.order_reference,
                "notes": {
                    "order_id": str(payment_request.order_id),
                    "client_code": payment_request.client_code,
                    "scheme_code": payment_request.scheme_code
                }
            }
            
            razorpay_order = self.client.order.create(data=order_data)
            
            return PaymentResponse(
                payment_reference=razorpay_order["id"],
                payment_url=f"https://api.razorpay.com/v1/checkout/embedded/{razorpay_order['id']}",
                amount=payment_request.amount,
                currency="INR",
                status="INITIATED",
                gateway_response=razorpay_order
            )

        except Exception as e:
            logger.error(f"Failed to initiate Razorpay payment: {e}", exc_info=True)
            raise ValueError(f"Failed to initiate payment: {str(e)}")

    async def verify_payment(self, payment_reference: str) -> Dict[str, Any]:
        """
        Verify payment status with Razorpay.
        
        Args:
            payment_reference: Razorpay order ID
            
        Returns:
            Dict containing payment verification details
        """
        try:
            payment_details = self.client.order.payments(payment_reference)
            
            # Get the latest payment attempt
            latest_payment = payment_details["items"][0] if payment_details["items"] else None
            
            if not latest_payment:
                return {
                    "verified": False,
                    "status": "PAYMENT_NOT_FOUND",
                    "message": "No payment found for this reference"
                }
            
            return {
                "verified": latest_payment["status"] == "captured",
                "status": latest_payment["status"].upper(),
                "amount": Decimal(latest_payment["amount"]) / 100,  # Convert from paise
                "payment_id": latest_payment["id"],
                "payment_method": latest_payment["method"],
                "payment_time": datetime.fromtimestamp(latest_payment["created_at"]),
                "gateway_response": latest_payment
            }

        except Exception as e:
            logger.error(f"Failed to verify Razorpay payment: {e}", exc_info=True)
            raise ValueError(f"Failed to verify payment: {str(e)}")

# Factory to get payment gateway instance
def get_payment_gateway(gateway_type: str = "razorpay", **kwargs) -> PaymentGateway:
    """
    Factory function to get payment gateway instance.
    
    Args:
        gateway_type: Type of payment gateway ("razorpay", etc.)
        **kwargs: Gateway-specific configuration
        
    Returns:
        PaymentGateway instance
    """
    if gateway_type.lower() == "razorpay":
        return RazorpayGateway(
            api_key=kwargs.get("api_key"),
            api_secret=kwargs.get("api_secret")
        )
    else:
        raise ValueError(f"Unsupported payment gateway: {gateway_type}")