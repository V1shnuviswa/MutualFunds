# /home/ubuntu/order_management_system/src/main.py

from fastapi import FastAPI, Depends, HTTPException

from src.database import engine, database, create_tables, connect_db, disconnect_db
from src import models
from src.routers import auth, orders, reports, price, payment, monitoring

# Create database tables if they don't exist
# In a production scenario, you might use Alembic for migrations
# models.Base.metadata.create_all(bind=engine)
# Let's create a function to call this explicitly if needed
def setup_database():
    print("Creating database tables...")
    create_tables()
    print("Database tables created.")

app = FastAPI(
    title="Order Management System API",
    description="API based on BSE StAR MF Webservice Structure for managing mutual fund orders.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json", # Standardize API doc path
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

@app.on_event("startup")
async def startup():
    await connect_db()
    # Optionally create tables on startup if db doesn't exist
    # setup_database() # Uncomment if you want tables created automatically

@app.on_event("shutdown")
async def shutdown():
    await disconnect_db()

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(price.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")

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

# Command to run: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
# Need to be in the /home/ubuntu/order_management_system directory

