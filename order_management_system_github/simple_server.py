from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple app
app = FastAPI(
    title="Simple Order Management System API",
    description="Simplified API for testing",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
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
    return {"message": "Welcome to the simple Order Management System API. See /api/v1/docs for API documentation."}

@app.get("/api/v1/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok"}

# Add simple lumpsum and SIP order endpoints
@app.post("/api/v1/orders/lumpsum", tags=["orders"])
async def place_lumpsum_order(request: Request):
    """
    Place a lumpsum order using BSE-compliant request format
    """
    try:
        # Return a success response with dummy details
        return {
            "message": "Lumpsum order received successfully",
            "order_id": "ORD-123456",
            "status": "SUCCESS"
        }
    except Exception as e:
        logger.error(f"Error processing lumpsum order: {str(e)}")
        return {"detail": f"Error processing lumpsum order: {str(e)}"}

@app.post("/api/v1/orders/sip", tags=["orders"])
async def place_sip_order(request: Request):
    """
    Place a SIP order using BSE-compliant request format
    """
    try:
        # Return a success response with dummy details
        return {
            "message": "SIP order received successfully",
            "sip_id": "SIP-123456",
            "status": "SUCCESS"
        }
    except Exception as e:
        logger.error(f"Error processing SIP order: {str(e)}")
        return {"detail": f"Error processing SIP order: {str(e)}"}

# Command to run: uvicorn simple_server:app --reload