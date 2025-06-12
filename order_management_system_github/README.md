# Order Management System with BSE Integration

## Overview

This project is a FastAPI-based API designed for managing mutual fund orders. It includes functionality for user authentication, placing lumpsum and SIP orders, and integrates with the BSE STAR MF platform for authentication, client registration, and order placement.

## Features

*   **User Authentication**: Secure user registration and login using JWT tokens.
*   **BSE Client Registration**: Register and update client details via the BSE STAR MF Client Master API (using direct HTTP POST).
*   **BSE Authentication**: Authenticate with the BSE platform to obtain session credentials (using SOAP).
*   **Lumpsum Order Placement**: Submit lumpsum purchase/redemption orders via the BSE STAR MF Order Entry API (using SOAP).
*   **SIP Order Registration**: Register Systematic Investment Plans (SIPs) via the BSE STAR MF Order Entry API (using SOAP).
*   **Database**: Uses SQLAlchemy and SQLite for data persistence.
*   **API Documentation**: Automatic interactive API documentation provided by FastAPI (Swagger UI/ReDoc).

## Technology Stack

*   **Backend**: Python 3.11+, FastAPI
*   **Database**: SQLAlchemy, SQLite
*   **BSE Integration**: 
    *   `requests` (for Client Registration - POST)
    *   `zeep` (for Authentication & Order Entry - SOAP)
*   **Authentication**: JWT (python-jose), Passlib
*   **Configuration**: Pydantic-Settings
*   **Testing**: unittest, unittest.mock

## Project Structure

```
order_management_system_github/
├── docs/                 # Documentation files (API structure, DB schema, integration notes, etc.)
├── src/                  # Source code for the FastAPI application
│   ├── bse_integration/  # Modules for interacting with BSE APIs
│   ├── routers/          # API endpoint definitions
│   ├── __init__.py
│   ├── crud.py           # Database Create, Read, Update, Delete operations
│   ├── database.py       # Database session setup
│   ├── dependencies.py   # FastAPI dependencies (e.g., authentication)
│   ├── main.py           # FastAPI application entry point
│   ├── models.py         # SQLAlchemy database models
│   ├── schemas.py        # Pydantic data validation models
│   ├── security.py       # Password hashing and JWT handling
│   └── utils.py          # Utility functions
├── tests/                # Unit and integration tests
│   ├── bse_test_connectivity.py # Script to test basic BSE auth connectivity
│   └── test_client_registration.py # Unit tests for client registration
├── .env.example          # Example environment file (copy to .env)
├── .gitignore            # Specifies intentionally untracked files that Git should ignore
├── README.md             # This file
├── requirements.txt      # Python package dependencies
└── setup_db.py           # Script to initialize the database
```

## Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd order_management_system_github
    ```

2.  **Create and Activate Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    *   Copy the example environment file:
        ```bash
        cp .env.example .env 
        ```
    *   Edit the `.env` file and add your actual BSE STAR MF credentials (User ID, Password, Member Code).
    *   Verify the BSE API URLs (Base URL, Paths, WSDLs) are correct for your target environment (Demo/Production).

5.  **Initialize the Database**:
    ```bash
    python setup_db.py
    ```
    This will create the `order_management.db` SQLite file.

## Running the Application

Use Uvicorn to run the FastAPI application:

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Interactive API documentation (Swagger UI) will be at `http://127.0.0.1:8000/docs`.

## Running Tests

Navigate to the project root directory (`order_management_system_github/`) and run:

```bash
# Run all tests in the tests/ directory
python -m unittest discover tests

# Run a specific test file
python tests/test_client_registration.py 
```

## Important Notes

*   **Network Access**: Full functionality, especially BSE integration, requires the application environment to have network access to the relevant BSE STAR MF API endpoints.
*   **Validation**: The BSE integration components were developed based on reference code and documentation. Due to sandbox limitations, end-to-end testing was performed using mocks. Thorough testing in an environment connected to BSE is crucial before production use. Refer to `docs/bse_integration_external_validation_guide.md`.
*   **Credentials**: Ensure your `.env` file is kept secure and is not committed to version control.
*   **Passkey**: The `passkey` required for BSE authentication and order placement needs to be handled securely. The current implementation might use placeholders or require user input; adapt this as needed for your security requirements.

## Documentation

Detailed documentation can be found in the `/docs` directory, including:
*   API Structure
*   Database Schema
*   BSE Integration Design Notes
*   External Validation Guide
*   Client Registration Update Notes

