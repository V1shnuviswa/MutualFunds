# /home/ubuntu/order_management_system/src/main.py
import os 
from fastapi import FastAPI, Depends, HTTPException, Request, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable, Dict, Any, Optional
import functools
import logging
from datetime import datetime
from src.database import engine, database, create_tables, connect_db, disconnect_db
from src import models, schemas
from src.routers import (
    auth_router, orders_router, reports_router, price_router,
    payment_router, monitoring_router, holdings_router, registration_router,
    bse_auth

)
import requests
from src.bse_integration.auth import bse_router
from src.bse_integration.config import bse_settings
from src.bse_integration.order import BSEOrderPlacer
from src.routers.registration import bse_router as bse_registration_router
from src.utils import preprocess_payload  # Import the utility function
from dotenv import load_dotenv
load_dotenv()
print("Loaded BSE_USER_ID:", os.getenv("BSE_USER_ID"))
print("Loaded BSE_MEMBER_CODE:", os.getenv("BSE_MEMBER_CODE"))
# Configure logging - Set to DEBUG level for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bse_integration.log')
    ]
)
logger = logging.getLogger(__name__)
# Enable detailed logging for BSE integration
logging.getLogger('src.bse_integration').setLevel(logging.DEBUG)
logging.getLogger('src.routers.registration').setLevel(logging.DEBUG)
logging.getLogger('zeep').setLevel(logging.DEBUG)
logging.getLogger('requests').setLevel(logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.DEBUG)

# Create database tables if they don't exist
# In a production scenario, you might use Alembic for migrations
# models.Base.metadata.create_all(bind=engine)
# Let's create a function to call this explicitly if needed
def setup_database():
    print("Creating database tables...")
    create_tables()
    print("Database tables created.")

# Use the custom route class in the app initialization
app = FastAPI(
    title="Order Management System API",
    description="API for BSE Star MF Order Management",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Custom OpenAPI to fix issues with query parameters
#def custom_openapi():
#    if app.openapi_schema:
#        return app.openapi_schema
#    openapi_schema = get_openapi(
#        title=app.title,
#        version=app.version,
#        description=app.description,
#        routes=app.routes,
#    )
#    app.openapi_schema = openapi_schema
#    return app.openapi_schema

#app.openapi = custom_openapi

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",  # React frontend
    "http://localhost:8000",  # FastAPI itself for development
    "http://localhost:8080",  # Alternative frontend port
]

# Configure middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await connect_db()
    # Don't create tables automatically - they already exist
    # setup_database()  # Tables are already created
    if os.getenv("INIT_DB", "false").lower() == "true":
        print("🚀 INIT_DB is true. Creating tables...")
        setup_database()
    else:
        print("✅ Skipping table creation (INIT_DB not true)")
    # Using real BSE services
    print("Using REAL BSE services")

@app.on_event("shutdown")
async def shutdown():
    await disconnect_db()

# Include routers - auth_router already has prefix "/auth" in its definition
# No need to add prefix to routers as they already have their own prefixes defined
app.include_router(auth_router)  # This router already has "/auth" prefix
app.include_router(bse_router)   # Include BSE authentication router
app.include_router(orders_router) # This router already has "/api/v1/orders" prefix
app.include_router(reports_router) # This router already has its prefix
app.include_router(price_router) # This router already has its prefix
app.include_router(payment_router) # This router already has its prefix
app.include_router(monitoring_router) # This router already has its prefix
app.include_router(holdings_router) # This router already has its prefix
app.include_router(registration_router) # This router already has its prefix
app.include_router(bse_auth.router)    # Include the new BSE auth router
app.include_router(bse_registration_router)  # Include the BSE client registration router


@app.get("/api/v1/health", tags=["Health Check"])
async def health_check():
    # Check database connection
    try:
        await database.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {e}"
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")

    return {"status": "ok", "database": db_status}

# Add a root endpoint for basic info
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to the Order Management System API. See /api/v1/docs for details."}

@app.get("/debug/routes", include_in_schema=False)
def debug_routes():
    return [
        {
            "path": route.path,
            "name": getattr(route.endpoint, "__name__", str(route.endpoint)),
            "methods": list(route.methods),
            "endpoint": str(route.endpoint)
        }
        for route in app.routes
    ]
@app.get("/my-ip", include_in_schema=False)
def get_my_ip():
    ip = requests.get("https://api64.ipify.org?format=json").json()
    return ip

@app.get("/test-bse-wsdl")
def test_bse_wsdl():
    import requests
    try:
        response = requests.get("https://bsestarmfdemo.bseindia.com/MFOrderEntry/MFOrder.svc?wsdl", timeout=10)
        return {"status": "success", "content": response.text[:500]}  # show just the first part
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Create a direct implementation of the lumpsum endpoint at the original path
#@app.post("/api/v1/orders/lumpsum-direct", tags=["orders"], include_in_schema=True)
#async def direct_lumpsum_order(request: Request):
#    """
#    Create a lumpsum order using BSE-compliant request format
#    """
#    try:
#        # Parse the raw request body
#        #order_request = await request.json()
#
#        # Return a success response with the order details
#        return {
#            "message": "Lumpsum order received successfully",
#            "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
#            "status": "SUCCESS",
#            "unique_ref_no": order_request.get("TransNo", ""),
#            "client_code": order_request.get("ClientCode", ""),
#            "scheme_code": order_request.get("SchemeCd", ""),
#            "transaction_type": order_request.get("BuySell", ""),
#            "amount": order_request.get("Amount", 0),
#            "folio_no": order_request.get("FolioNo", "")
#        }
#
#    except Exception as e:
#        logger.error(f"Error processing lumpsum order: {str(e)}", exc_info=True)
#        return JSONResponse(
#            status_code=422,
#            content={
#                "detail": f"Error processing lumpsum order: {str(e)}"
#            }
#        )

# Create a direct implementation of the SIP order endpoint
#@app.post("/api/v1/orders/sip-direct", tags=["orders"], include_in_schema=True)
#async def direct_sip_order(request: Request):
#    """
#    Create a SIP order using BSE-compliant request format
#    """
#    try:
#        # Parse the raw request body
#        #order_request = await request.json()
#
#        # Return a success response with the order details
#        return {
#            "message": "SIP order received successfully",
#            "sip_id": f"SIP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
#            "status": "SUCCESS",
#            "unique_ref_no": order_request.get("unique_ref_no", ""),
#            "bse_sip_reg_id": f"BSE{datetime.now().strftime('%Y%m%d%H%M%S')}",
#            "bse_status_code": "100",
#            "bse_remarks": "SIP registration successful"
#        }
#
#    except Exception as e:
#        logger.error(f"Error processing SIP order: {str(e)}", exc_info=True)
#        return JSONResponse(
#            status_code=422,
#            content={
#                "detail": f"Error processing SIP order: {str(e)}"
#            }
#        )

# Command to run: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
# Need to be in the /home/ubuntu/order_management_system directory