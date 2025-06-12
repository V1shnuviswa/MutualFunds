from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple app
app = FastAPI(
    title="Simple Order Management System API",
    description="Simplified API for BSE Star MF Order Management",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Order Management System API. See /api/v1/docs for details."}

@app.get("/api/v1/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok"}

@app.post("/api/v1/orders/lumpsum", tags=["orders"])
async def place_lumpsum_order(request: Request):
    """
    Place a lumpsum order using BSE-compliant request format
    """
    try:
        # Parse the raw request body
        order_request = await request.json()
        
        # Return a success response with the order details
        return {
            "message": "Lumpsum order received successfully",
            "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "SUCCESS",
            "unique_ref_no": order_request.get("TransNo", ""),
            "client_code": order_request.get("ClientCode", ""),
            "scheme_code": order_request.get("SchemeCd", ""),
            "transaction_type": order_request.get("BuySell", ""),
            "amount": order_request.get("Amount", 0),
            "folio_no": order_request.get("FolioNo", "")
        }
        
    except Exception as e:
        logger.error(f"Error processing lumpsum order: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=422, 
            content={
                "detail": f"Error processing lumpsum order: {str(e)}"
            }
        )

@app.post("/api/v1/orders/sip", tags=["orders"])
async def place_sip_order(request: Request):
    """
    Place a SIP order using BSE-compliant request format
    """
    try:
        # Parse the raw request body
        order_request = await request.json()
        
        # Return a success response with the order details
        return {
            "message": "SIP order received successfully",
            "sip_id": f"SIP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "SUCCESS",
            "unique_ref_no": order_request.get("unique_ref_no", ""),
            "bse_sip_reg_id": f"BSE{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "bse_status_code": "100",
            "bse_remarks": "SIP registration successful"
        }
        
    except Exception as e:
        logger.error(f"Error processing SIP order: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=422, 
            content={
                "detail": f"Error processing SIP order: {str(e)}"
            }
        )

# Command to run: uvicorn simple_order_system:app --reload 