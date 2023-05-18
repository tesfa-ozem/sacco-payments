# Sacco-payments - Flask API Integration with Odoo

Welcome to the Sacco API, a Flask API project that connects to Odoo and exposes endpoints for a SACCO (Savings and Credit Cooperative) system. This API allows users to interact with the SACCO platform, manage member accounts, savings, loans, and perform various transactions.

## Getting Started

To get started with the Sacco API, follow the instructions below:

### Prerequisites

- Python 3.7 or higher
- Flask and its dependencies
- Odoo XML-RPC library (e.g., `odoo-xmlrpc`)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/tesfa-ozem/sacco-payments.git
   cd sacco-payments
   ```

2. Create a virtual environment (optional, but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the Odoo connection:
   - Open the `.env` file and modify the `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`,`ODOO_PASSWORD` variables with your Odoo instance details.
   - Modifify this additional variables `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, and `MAIL_PASSWORD` 

5. Run the application:
   ```bash
   flask run
   ```

6. The application should now be running locally at `http://localhost:5000`.

### Member Endpoints

#### Create a new member account

- **Endpoint**: `/api/member`
- **Method**: `POST`
- **Description**: Create a new member account.
- **Request Body**:
  - `username`: Username of the member.
  - `password`: Password of the member.
  - `email`: Email address of the member.
- **Response**:
  - `username`: Username of the created member.
- **Authentication**: Not required.

#### Update a member account

- **Endpoint**: `/api/member`
- **Method**: `PUT`
- **Description**: Update the details of a specific member.
- **Request Body**: Updated details of the member.
- **Authentication**: Token-based authentication required.

#### Retrieve member information

- **Endpoint**: `/api/member`
- **Method**: `GET`
- **Description**: Retrieve a list of all SACCO members.
- **Authentication**: Token-based authentication required.

### Sacco Payment Process

#### Lipa Na Mpesa Online

- **Endpoint**: `/api/MakePayment`
- **Method**: `POST`
- **Description**: Perform an online payment using Mpesa.
- **Request Body**:
  - `lines`: Payment details.
  - `phone`: Phone number for the payment.
- **Authentication**: Token-based authentication required.

### Loan Process

#### Get Loan Limit

- **Endpoint**: `/api/LoanLimit`
- **Method**: `GET`
- **Description**: Get the loan limit for a member.
- **Authentication**: Not required.

#### Repay Loan

- **Endpoint**: `/api/RepayLoan`
- **Method**: `GET`
- **Description**: Repay a loan.
- **Authentication**: Not required.

#### Loan Payment Schedule

- **Endpoint**: `/api/LoanPaymentSchedule`
- **Method**: `GET`
- **Description**: Get the repayment schedule for a loan.
- **Authentication**: Not required.

### Mpesa Callback

#### Mpesa Callback

- **Endpoint**: `/api/v1/c2b/callback`
- **Method**: `POST`
- **Description**: Callback URL for Mpesa transactions.
- **Authentication**: Not required

.

### Loan Application

#### Apply for Loan

- **Endpoint**: `/api/ApplyLoan`
- **Method**: `POST`
- **Description**: Apply for a loan.
- **Request Body**:
  - `amount`: Amount of the loan.
- **Authentication**: Token-based authentication required.

#### Get Application Status

- **Endpoint**: `/api/getAppStatus`
- **Method**: `GET`
- **Description**: Get the application status.
- **Authentication**: Token-based authentication required.

### C2B API

#### Validation Response

- **Endpoint**: `/api/validationResponse`
- **Method**: `GET`
- **Description**: Response for C2B validation.
- **Authentication**: Not required.

#### Confirmation Callback

- **Endpoint**: `/api/confirmationCallback`
- **Method**: `GET`
- **Description**: Callback for C2B confirmation.
- **Authentication**: Not required.

#### Make C2B Payment

- **Endpoint**: `/api/c2bPayment`
- **Method**: `GET`
- **Description**: Make a C2B payment.
- **Authentication**: Not required.

## Authentication

Some endpoints require authentication using a token-based authentication system. To obtain an authentication token, you can use the following endpoint:

- **Endpoint**: `/api/token`
- **Method**: `GET`
- **Description**: Get an authentication token.
- **Authentication**: Basic authentication required.

## Error Handling

The Sacco API returns appropriate HTTP status codes and error messages when requests fail. Error responses are returned in JSON format and include an `error` field describing the issue.
