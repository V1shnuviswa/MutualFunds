#!/usr/bin/env python
"""
Run the FastAPI server for testing the BSE STAR MF integration.

This script starts the FastAPI server with the correct settings for testing
the BSE STAR MF API integration.

Usage:
    python run_api_server.py
"""

import os
import sys
import uvicorn

# Add the project root to the Python path
sys.path.append(os.path.abspath("."))

if __name__ == "__main__":
    print("Starting Order Management System API server...")
    print("Access the API documentation at: http://localhost:8000/api/v1/docs")
    print("Press Ctrl+C to stop the server")
    
    # Run the FastAPI server
    uvicorn.run(
        "order_management_system_github.src.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    ) 