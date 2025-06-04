# Order Management System Database Schema

This document outlines the database schema designed to support the Order Management System API (`api_structure.md`), derived from the BSE StAR MF requirements.

## Database Type

Relational Database (e.g., PostgreSQL, MySQL, SQLite - SQLite will be used for simplicity in initial implementation).

## Tables

### 1. `users`

Stores user/member credentials for authentication.

| Column Name   | Data Type     | Constraints              | Description                     |
|---------------|---------------|--------------------------|---------------------------------|
| `id`          | INTEGER       | PRIMARY KEY AUTOINCREMENT| Unique user identifier          |
| `user_id`     | VARCHAR(50)   | NOT NULL, UNIQUE         | User ID provided during login   |
| `member_id`   | VARCHAR(50)   | NOT NULL                 | Member ID associated with user  |
| `password_hash`| VARCHAR(255)  | NOT NULL                 | Hashed user password            |
| `pass_key`    | VARCHAR(255)  | NULL                     | Optional passkey (hashed/encrypted) |
| `created_at`  | TIMESTAMP     | NOT NULL DEFAULT NOW()   | Timestamp of user creation      |
| `updated_at`  | TIMESTAMP     | NOT NULL DEFAULT NOW()   | Timestamp of last update        |

### 2. `clients`

Stores client information. Assumes `clientCode` is the primary identifier.

| Column Name      | Data Type     | Constraints              | Description                        |
|------------------|---------------|--------------------------|------------------------------------|
| `client_code`    | VARCHAR(50)   | PRIMARY KEY              | Unique client identifier           |
| `client_name`    | VARCHAR(255)  | NULL                     | Full name of the client            |
| `pan`            | VARCHAR(10)   | NULL, UNIQUE             | Permanent Account Number           |
| `kyc_status`     | CHAR(1)       | NOT NULL DEFAULT 'N'     | KYC status ('Y' or 'N')            |
| `account_type`   | VARCHAR(50)   | NULL                     | e.g., 'Individual', 'Corporate'    |
| `holding_type`   | VARCHAR(50)   | NULL                     | e.g., 'Single', 'Joint'            |
| `tax_status`     | VARCHAR(50)   | NULL                     | Tax status code/description        |
| `created_at`     | TIMESTAMP     | NOT NULL DEFAULT NOW()   | Timestamp of client creation       |
| `updated_at`     | TIMESTAMP     | NOT NULL DEFAULT NOW()   | Timestamp of last update           |
| `created_by_user`| INTEGER       | NULL, FOREIGN KEY(users.id)| User who created the client record |

*Note: More fields from the UCC registration section (pg 80+) can be added here.* 

### 3. `schemes`

Stores details about mutual fund schemes.

| Column Name   | Data Type     | Constraints              | Description                     |
|---------------|---------------|--------------------------|---------------------------------|
| `scheme_code` | VARCHAR(50)   | PRIMARY KEY              | Unique scheme identifier        |
| `scheme_name` | VARCHAR(255)  | NOT NULL                 | Full name of the scheme         |
| `amc_code`    | VARCHAR(50)   | NULL                     | Asset Management Company code   |
| `rta_code`    | VARCHAR(50)   | NULL                     | Registrar and Transfer Agent code |
| `isin`        | VARCHAR(12)   | NULL, UNIQUE             | ISIN code for the scheme        |
| `category`    | VARCHAR(100)  | NULL                     | Scheme category (e.g., Equity Large Cap) |
| `is_active`   | BOOLEAN       | NOT NULL DEFAULT TRUE    | Whether the scheme is active    |
| `added_at`    | TIMESTAMP     | NOT NULL DEFAULT NOW()   | Timestamp when scheme was added |

### 4. `orders`

Stores details for all types of orders (Lumpsum, SIP registration, etc.).

| Column Name        | Data Type     | Constraints                     | Description                               |
|--------------------|---------------|---------------------------------|-------------------------------------------|
| `id`               | INTEGER       | PRIMARY KEY AUTOINCREMENT       | Unique order identifier                   |
| `order_id_bse`     | VARCHAR(50)   | NULL, UNIQUE                    | Order ID received from BSE (if applicable)|
| `unique_ref_no`    | VARCHAR(50)   | NOT NULL, UNIQUE                | Client-generated unique reference number  |
| `client_code`      | VARCHAR(50)   | NOT NULL, FOREIGN KEY(clients.client_code) | Client placing the order              |
| `scheme_code`      | VARCHAR(50)   | NOT NULL, FOREIGN KEY(schemes.scheme_code) | Scheme for the order                  |
| `order_type`       | VARCHAR(20)   | NOT NULL                        | 'LUMPSUM', 'SIP_REG', 'REDEMPTION', etc.  |
| `transaction_type` | VARCHAR(20)   | NULL                            | 'PURCHASE', 'REDEMPTION', 'SWITCH_IN', etc. |
| `amount`           | DECIMAL(15, 2)| NULL                            | Order amount (for purchase/SIP)           |
| `quantity`         | DECIMAL(15, 4)| NULL                            | Order quantity (for redemption)           |
| `folio_no`         | VARCHAR(50)   | NULL                            | Existing Folio number                     |
| `order_timestamp`  | TIMESTAMP     | NOT NULL DEFAULT NOW()          | Timestamp when order was placed in system |
| `status`           | VARCHAR(30)   | NOT NULL DEFAULT 'RECEIVED'     | Current status (e.g., RECEIVED, SENT_TO_BSE, PROCESSED, REJECTED) |
| `status_message`   | TEXT          | NULL                            | Additional details/reason for status      |
| `bse_status_code`  | VARCHAR(10)   | NULL                            | Status code from BSE response             |
| `bse_remarks`      | TEXT          | NULL                            | Remarks from BSE response                 |
| `user_id`          | INTEGER       | NOT NULL, FOREIGN KEY(users.id) | User who placed the order                 |
| `ip_address`       | VARCHAR(45)   | NULL                            | IP address of the user placing the order  |
| `euin`             | VARCHAR(50)   | NULL                            | EUIN                                      |
| `euin_declared`    | CHAR(1)       | NULL                            | EUIN declaration ('Y'/'N')                 |
| `sub_arn_code`     | VARCHAR(50)   | NULL                            | Sub-ARN code                              |
| `created_at`       | TIMESTAMP     | NOT NULL DEFAULT NOW()          | Timestamp of record creation              |
| `updated_at`       | TIMESTAMP     | NOT NULL DEFAULT NOW()          | Timestamp of last update                  |

### 5. `sip_registrations`

Stores details specific to SIP registrations.

| Column Name        | Data Type     | Constraints                     | Description                               |
|--------------------|---------------|---------------------------------|-------------------------------------------|
| `id`               | INTEGER       | PRIMARY KEY AUTOINCREMENT       | Unique SIP registration identifier        |
| `sip_reg_id_bse`   | VARCHAR(50)   | NULL, UNIQUE                    | SIP Registration ID from BSE              |
| `order_id`         | INTEGER       | NOT NULL, FOREIGN KEY(orders.id)| Link to the initial registration order    |
| `client_code`      | VARCHAR(50)   | NOT NULL, FOREIGN KEY(clients.client_code) | Client for the SIP                    |
| `scheme_code`      | VARCHAR(50)   | NOT NULL, FOREIGN KEY(schemes.scheme_code) | Scheme for the SIP                    |
| `frequency`        | VARCHAR(20)   | NOT NULL                        | e.g., 'MONTHLY', 'QUARTERLY'              |
| `amount`           | DECIMAL(15, 2)| NOT NULL                        | Installment amount                        |
| `installments`     | INTEGER       | NULL                            | Total number of installments (if fixed)   |
| `start_date`       | DATE          | NOT NULL                        | Date of first installment                 |
| `end_date`         | DATE          | NULL                            | Date of last installment (if fixed)       |
| `mandate_id`       | VARCHAR(50)   | NULL                            | Associated mandate ID                     |
| `first_order_today`| CHAR(1)       | NULL                            | Whether first order is placed today ('Y'/'N') |
| `status`           | VARCHAR(30)   | NOT NULL DEFAULT 'REGISTERED'   | Current status (e.g., REGISTERED, ACTIVE, PAUSED, CANCELLED) |
| `created_at`       | TIMESTAMP     | NOT NULL DEFAULT NOW()          | Timestamp of record creation              |
| `updated_at`       | TIMESTAMP     | NOT NULL DEFAULT NOW()          | Timestamp of last update                  |

### 6. `mandates`

Stores mandate details (for SIP, etc.).

| Column Name      | Data Type     | Constraints              | Description                         |
|------------------|---------------|--------------------------|-------------------------------------|
| `mandate_id`     | VARCHAR(50)   | PRIMARY KEY              | Unique Mandate ID (from BSE/Bank)   |
| `client_code`    | VARCHAR(50)   | NOT NULL, FOREIGN KEY(clients.client_code) | Associated client               |
| `bank_account_no`| VARCHAR(50)   | NOT NULL                 | Bank account number                 |
| `bank_name`      | VARCHAR(100)  | NOT NULL                 | Name of the bank                    |
| `ifsc_code`      | VARCHAR(11)   | NOT NULL                 | IFSC code of the bank branch        |
| `amount`         | DECIMAL(15, 2)| NOT NULL                 | Maximum amount per transaction      |
| `mandate_type`   | VARCHAR(20)   | NOT NULL                 | e.g., 'NACH', 'BILLER'              |
| `status`         | VARCHAR(30)   | NOT NULL DEFAULT 'PENDING' | Current status (e.g., PENDING, APPROVED, REJECTED, CANCELLED) |
| `registration_date`| DATE          | NULL                     | Date mandate was registered         |
| `expiry_date`    | DATE          | NULL                     | Mandate expiry date                 |
| `created_at`     | TIMESTAMP     | NOT NULL DEFAULT NOW()   | Timestamp of record creation        |
| `updated_at`     | TIMESTAMP     | NOT NULL DEFAULT NOW()   | Timestamp of last update            |

## Relationships

- `users` <-> `clients` (One-to-Many, optional: if tracking who created client)
- `users` <-> `orders` (One-to-Many: user places many orders)
- `clients` <-> `orders` (One-to-Many: client has many orders)
- `schemes` <-> `orders` (One-to-Many: scheme can be in many orders)
- `clients` <-> `sip_registrations` (One-to-Many)
- `schemes` <-> `sip_registrations` (One-to-Many)
- `orders` <-> `sip_registrations` (One-to-One: SIP registration starts with an order)
- `clients` <-> `mandates` (One-to-Many)
- `mandates` <-> `sip_registrations` (One-to-Many, optional: SIP uses a mandate)

## Indexes

- Create indexes on foreign key columns (`client_code`, `scheme_code`, `user_id`, `order_id`, `mandate_id`).
- Create indexes on frequently queried columns like `status`, `order_timestamp`, `start_date`, `end_date`.
- Create indexes on unique identifiers like `order_id_bse`, `sip_reg_id_bse`, `pan`.

