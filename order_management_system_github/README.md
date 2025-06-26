# Order Management System with BSE STAR MF Integration

This system provides an API for managing mutual fund orders, integrating with BSE STAR MF for order placement, and tracking order status updates.

## Project Structure

```
order_management_system_github/
├── src/
│   ├── bse_integration/  # BSE STAR MF API integration code
│   ├── routers/          # FastAPI router endpoints
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
├── setup_db.py           # Script to initialize the database
├── migration.py          # Script to migrate data from SQLite to PostgreSQL
├── docker-compose.yml    # Docker Compose configuration for PostgreSQL and pgAdmin
└── Dockerfile            # Docker configuration for the application
```

## Setup Instructions

### Option 1: Using Docker (PostgreSQL)

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd order_management_system_github
   ```

2. **Configure Environment Variables**:
   * Copy the example environment file:
     ```bash
     cp .env.example .env 
     ```
   * Edit the `.env` file with your settings if needed

3. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```
   
   This will:
   - Start a PostgreSQL database
   - Start pgAdmin (available at http://localhost:5050)
   - Build and run the application
   - Migrate data from SQLite to PostgreSQL
   - Start the API server

   The API will be available at `http://localhost:8000`.
   Interactive API documentation (Swagger UI) will be at `http://localhost:8000/docs`.

### Option 2: Manual Setup (PostgreSQL)

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd order_management_system_github
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   * Copy the example environment file:
     ```bash
     cp .env.example .env 
     ```
   * Edit the `.env` file and add your database connection details and BSE credentials

5. **Set up PostgreSQL Database**:
   * Install PostgreSQL if not already installed
   * Create a database named `order_management`
   * Update the DATABASE_URL in the .env file if needed

6. **Migrate Data from SQLite to PostgreSQL**:
   ```bash
   python migration.py
   ```

7. **Run the Application**:
   ```bash
   uvicorn src.main:app --reload
   ```

   The API will be available at `http://127.0.0.1:8000`.
   Interactive API documentation (Swagger UI) will be at `http://127.0.0.1:8000/docs`.

### Option 3: Local Setup with SQLite

If you prefer to use SQLite (the original database), follow the manual setup steps above but make the following changes:

1. Modify `.env` to use SQLite:
   ```
   DATABASE_URL=sqlite:///./order_management.db
   ```

2. Initialize the SQLite database:
   ```bash
   python setup_db.py
   ```

## pgAdmin Setup (For Docker Option)

When using the Docker setup, pgAdmin is available at http://localhost:5050.

1. Login with:
   * Email: admin@example.com
   * Password: admin

2. Connect to the PostgreSQL server:
   * Right-click on "Servers" → "Register" → "Server"
   * Name: Order Management System
   * Connection tab:
     * Host: postgres
     * Port: 5432
     * Username: postgres
     * Password: postgres

## Running Tests

Navigate to the project root directory (`order_management_system_github/`) and run:

```bash
# Run all tests in the tests/ directory
python -m unittest discover tests

# Run a specific test file
python tests/test_client_registration.py 
```

## Important Notes

* **Network Access**: Full functionality, especially BSE integration, requires the application environment to have network access to the relevant BSE STAR MF API endpoints.
* **Validation**: The BSE integration components were developed based on reference code and documentation. Due to sandbox limitations, end-to-end testing was performed using mocks. Thorough testing in an environment connected to BSE is crucial before production use. Refer to `docs/bse_integration_external_validation_guide.md`.
* **Credentials**: Ensure your `.env` file is kept secure and is not committed to version control.
* **Passkey**: The `passkey` required for BSE authentication and order placement needs to be handled securely. The current implementation might use placeholders or require user input; adapt this as needed for your security requirements.

## Documentation

Detailed documentation can be found in the `/docs` directory, including:
* API Structure
* Database Schema
* BSE Integration Design Notes
* External Validation Guide
* Client Registration Update Notes

