# Import all routers
from .auth import router as auth_router
from .orders import router as orders_router
from .reports import router as reports_router
from .price import router as price_router
from .payment import router as payment_router
from .monitoring import router as monitoring_router
from .holdings import router as holdings_router
from .registration import router as registration_router

# Export routers
auth = auth_router
orders = orders_router
reports = reports_router
price = price_router
payment = payment_router
monitoring = monitoring_router
holdings = holdings_router
registration = registration_router
