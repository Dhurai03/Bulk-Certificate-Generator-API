# Bulk Certificate Generator API

A clean, production-ready backend REST API built with Python and FastAPI to generate bulk PDF certificates asynchronously from recipient lists.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [API Documentation](#api-documentation)
- [Example Workflow](#example-workflow)
- [Example curl Requests](#example-curl-requests)
- [Design Decisions & Architecture](#design-decisions--architecture)
- [Failure Isolation Mechanism](#failure-isolation-mechanism)
- [Testing](#testing)
- [Learning & Key Takeaways](#learning--key-takeaways)
- [Future Scope & Production Enhancements](#future-scope--production-enhancements)

---

## Overview

In educational workshops, conferences, and corporate training events, organizers often need to issue personalized certificates to hundreds or thousands of participants. Generating PDFs synchronously in a single HTTP request can cause server timeouts, poor user experience, and catastrophic batch failures if one recipient record is invalid or fails rendering.

The **Bulk Certificate Generator API** solves this problem by:
1. Accepting bulk generation requests and persisting them immediately.
2. Delegating PDF rendering to an asynchronous background worker.
3. Isolating individual certificate rendering errors so that a failure for one recipient never halts or cancels the certificates of others.
4. Providing endpoints to poll real-time job progress and download individual PDF certificates securely.

---

## Features

- **Bulk Certificate Generation**: Accepts an event payload with multiple recipients and generates certificates in bulk.
- **Strict Request Validation**: Validates event details, date formatting, and recipient email addresses using Pydantic schemas.
- **Asynchronous Background Processing**: Offloads heavy PDF generation to `FastAPI BackgroundTasks` without blocking the client.
- **Real-Time Job Progress Tracking**: Tracks status (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`), total count, success count, failure count, and percentage completion.
- **Individual Certificate Tracking**: Each certificate maintains its own lifecycle status (`PENDING`, `SUCCESS`, `FAILED`) and records specific failure reasons if errors occur.
- **Failure Isolation**: An exception when rendering one certificate (e.g., corrupt fonts, formatting error) is trapped and logged, while remaining certificates continue generating normally.
- **High-Quality PDF Generation**: Uses ReportLab to generate professional landscape certificates complete with borders, accents, dynamic typography, and verifiable IDs.
- **Secure Certificate Retrieval**: Serves generated PDFs via streaming `FileResponse` with path-traversal safeguards.
- **Comprehensive Automated Tests**: Pytest test suite with isolated in-memory/temporary databases and mock failure simulations.

---

## Technology Stack

- **Python 3.11+**: Modern, expressive language with robust typing support.
- **FastAPI**: High-performance asynchronous web framework providing automated OpenAPI/Swagger documentation, fast execution, and built-in background task primitives.
- **Pydantic (v2)**: Data parsing, rigorous schema validation, and automatic data transformation (e.g., trimming whitespace and validating emails).
- **SQLAlchemy (v2)**: Python SQL toolkit and Object Relational Mapper (ORM) defining relational models between jobs and certificate line items.
- **SQLite**: Zero-configuration, serverless SQL database engine ideal for lightweight local deployment and isolated testing.
- **ReportLab**: Established PDF generation library used to draw vector graphics, custom decorative borders, and typography onto a canvas.
- **Pytest & HTTPX**: Testing framework and HTTP client used to exercise synchronous endpoints, background tasks, validation edge cases, and failure mocks.

---

## Project Structure

```text
Bulk-Certificate-Generator-API/
├── app/
│   ├── __init__.py                 # App package initialization
│   ├── config.py                   # Centralized application settings (Pydantic Settings)
│   ├── database.py                 # SQLite engine, SessionLocal, Base, and init_db
│   ├── main.py                     # FastAPI application factory, lifespan, and CORS
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── job.py                  # Job database model & JobStatus enum
│   │   └── certificate.py          # Certificate database model & CertificateStatus enum
│   │
│   ├── schemas/                    # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── job.py                  # JobCreate, JobCreateResponse, JobStatusResponse
│   │   └── certificate.py          # RecipientCreate, CertificateResponse
│   │
│   ├── routes/                     # FastAPI route controllers
│   │   ├── __init__.py
│   │   ├── jobs.py                 # POST /api/jobs, GET /api/jobs/{id}, GET /api/jobs/{id}/certificates
│   │   └── certificates.py         # GET /api/certificates/{id} (PDF file download)
│   │
│   ├── services/                   # Business logic and processing services
│   │   ├── __init__.py
│   │   ├── certificate_generator.py # ReportLab PDF canvas drawing service
│   │   └── job_processor.py        # Background task processor with error isolation
│   │
│   └── utils/                      # Helper utilities
│       ├── __init__.py
│       └── file_utils.py           # Safe path resolution, filename helpers, traversal checks
│
├── generated/                      # Directory where generated PDF files are saved
│   └── .gitkeep
│
├── tests/                          # Automated test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures, test database setup, and monkeypatches
│   ├── test_job_creation.py        # Tests for job creation and health check
│   ├── test_validation.py          # Tests for input validation, trimming, and error codes
│   ├── test_certificate_generation.py # Unit tests for ReportLab PDF generator
│   ├── test_job_status.py          # Tests for job metrics and certificate listings
│   ├── test_failure_handling.py    # Failure isolation simulation tests
│   └── test_certificate_download.py# Tests for PDF file downloads and traversal protection
│
├── .env.example                    # Template environment variables
├── .gitignore                      # Git ignore file for virtualenvs, caches, and artifacts
├── requirements.txt                # Project dependencies
└── README.md                       # Complete documentation
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.11 or higher installed on your system.
- Git.

### 2. Clone the Repository
```bash
git clone https://github.com/Dhurai03/Bulk-Certificate-Generator-API.git
cd Bulk-Certificate-Generator-API
```

### 3. Create a Virtual Environment
```bash
python -m venv venv
```

### 4. Activate the Virtual Environment
- **On Windows (Command Prompt / PowerShell)**:
  ```powershell
  venv\Scripts\activate
  ```
- **On macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. Environment Configuration (Optional)
Copy `.env.example` to `.env` if you want to override default settings:
```bash
cp .env.example .env
```

### 7. Run the Application
Start the Uvicorn development server:
```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

---

## API Documentation

Interactive Swagger documentation is automatically generated and accessible in the browser:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Summary of Endpoints

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/` | API Health Check and Metadata | `200 OK` |
| `POST` | `/api/jobs` | Submit a bulk certificate generation job | `202 Accepted` |
| `GET` | `/api/jobs/{job_id}` | Retrieve job status, progress counts, and percentage | `200 OK` / `404 Not Found` |
| `GET` | `/api/jobs/{job_id}/certificates` | List all certificate records for a specific job | `200 OK` / `404 Not Found` |
| `GET` | `/api/certificates/{certificate_id}` | Download the generated PDF certificate | `200 OK` / `400 Bad Request` / `404 Not Found` |

---

### Detailed Endpoint Specifications

#### 1. POST `/api/jobs`
Creates a generation job, persists recipient records, and kicks off background processing.

- **Status Code**: `202 Accepted`
- **Request Body**:
```json
{
  "event_name": "Python Workshop 2026",
  "event_date": "2026-10-10",
  "organization_name": "ABC Organization",
  "recipients": [
    {
      "name": "Dhurai Murugan",
      "email": "dhurai@example.com"
    },
    {
      "name": "Arun Kumar",
      "email": "arun@example.com"
    }
  ]
}
```
- **Response Body**:
```json
{
  "job_id": 1,
  "status": "QUEUED",
  "message": "Certificate generation job created successfully"
}
```
- **Error Responses**:
  - `422 Unprocessable Entity`: Missing fields, invalid date format, invalid recipient email, or empty recipient list.

---

#### 2. GET `/api/jobs/{job_id}`
Returns the current job status and real-time processing metrics.

- **Status Code**: `200 OK`
- **Response Body (In Progress)**:
```json
{
  "job_id": 1,
  "status": "PROCESSING",
  "total": 100,
  "completed": 65,
  "successful": 63,
  "failed": 2,
  "progress_percentage": 65
}
```
- **Response Body (Completed)**:
```json
{
  "job_id": 1,
  "status": "COMPLETED",
  "total": 100,
  "completed": 100,
  "successful": 97,
  "failed": 3,
  "progress_percentage": 100
}
```
- **Error Responses**:
  - `404 Not Found`: Job does not exist.

---

#### 3. GET `/api/jobs/{job_id}/certificates`
Retrieves all individual certificate items under the specified job.

- **Status Code**: `200 OK`
- **Response Body**:
```json
[
  {
    "certificate_id": 1,
    "recipient_name": "Dhurai Murugan",
    "recipient_email": "dhurai@example.com",
    "status": "SUCCESS",
    "file_name": "certificate_1.pdf",
    "error_message": null
  },
  {
    "certificate_id": 2,
    "recipient_name": "Arun Kumar",
    "recipient_email": "arun@example.com",
    "status": "FAILED",
    "file_name": null,
    "error_message": "Certificate generation failed"
  }
]
```
- **Error Responses**:
  - `404 Not Found`: Job does not exist.

---

#### 4. GET `/api/certificates/{certificate_id}`
Streams the generated PDF certificate directly to the client as a download attachment.

- **Status Code**: `200 OK`
- **Response Headers**:
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="certificate_1.pdf"`
- **Response Body**: Binary PDF stream.
- **Error Responses**:
  - `400 Bad Request`: Certificate is still `PENDING` or status is `FAILED` (returns error explanation).
  - `403 Forbidden`: Security restriction if an arbitrary file path is requested outside the storage directory.
  - `404 Not Found`: Certificate ID does not exist or file is missing on the filesystem.

---

## Example Workflow

```text
Client
  │
  ├─► POST /api/jobs
  │   └── Receives HTTP 202 Accepted + job_id
  │
  ├─► GET /api/jobs/{job_id}
  │   └── Polls progress metrics until status == "COMPLETED"
  │
  ├─► GET /api/jobs/{job_id}/certificates
  │   └── Inspects list of recipients and their generated certificate_ids
  │
  └─► GET /api/certificates/{certificate_id}
      └── Downloads the individual PDF certificate
```

---

## Example curl Requests

### 1. Create a Job
```bash
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Python Workshop 2026",
    "event_date": "2026-10-10",
    "organization_name": "ABC Organization",
    "recipients": [
      {"name": "Dhurai Murugan", "email": "dhurai@example.com"},
      {"name": "Arun Kumar", "email": "arun@example.com"},
      {"name": "Priya", "email": "priya@example.com"}
    ]
  }'
```

### 2. Check Job Status
```bash
curl -X GET "http://localhost:8000/api/jobs/1"
```

### 3. List Certificates for the Job
```bash
curl -X GET "http://localhost:8000/api/jobs/1/certificates"
```

### 4. Download a Certificate PDF
```bash
curl -O -J "http://localhost:8000/api/certificates/1"
```

---

## Design Decisions & Architecture

### 1. Why FastAPI?
- Native asynchronous execution and first-class support for `BackgroundTasks`.
- Seamless integration with Pydantic for validation and serialization.
- Automatic interactive documentation via OpenAPI/Swagger.
- High developer velocity and lightweight runtime footprint.

### 2. Why SQLite?
- Zero external service dependencies: runs out-of-the-box without needing Docker or cloud database setup.
- Perfect for an intern evaluation assignment and single-node service instances.
- Fully compatible with standard SQL, making migration to PostgreSQL effortless via SQLAlchemy connection strings.

### 3. Why SQLAlchemy?
- Provides clean Object-Relational Mapping (ORM) and declarative models.
- Decouples business logic from database-specific SQL dialect.
- Provides explicit relationship cascades (`Job` -> `Certificate`), transaction management, and connection pooling.

### 4. Why FastAPI BackgroundTasks?
- Keeps the system architecture lightweight and focused by avoiding external message brokers like Celery, RabbitMQ, or Redis for smaller to medium bulk workloads.
- Allows immediate return of `HTTP 202 Accepted` to the client so HTTP requests never timeout while waiting for PDF rendering.

### 5. Why ReportLab?
- Native Python vector graphics and PDF rendering engine with high fidelity.
- Provides millimeter-accurate coordinate placement for title, double decorative borders, corner ornaments, recipient names, dates, and certificate ID badges.
- Avoids external binaries like `wkhtmltopdf` or headless browser automation tools (Puppeteer / Chromium) which add significant operational overhead and security risk.

### 6. Why Individual Certificate Records?
- Storing individual rows in the `certificates` table per recipient provides fine-grained visibility.
- Enables per-recipient status tracking (`SUCCESS` vs `FAILED`), explicit file path references, and persistent error logs.
- Allows users to query the status of their specific certificate directly without inspecting full job blobs.

---

## Failure Isolation Mechanism

A core requirement of bulk generation is that **a failure on one recipient must not stop the remaining certificates**.

In `app/services/job_processor.py`, each certificate is generated within an isolated `try/except` boundary:

```python
for cert in certificates:
    try:
        output_path = get_certificate_path(cert.id)
        generate_certificate(
            certificate_id=cert.id,
            recipient_name=cert.recipient_name,
            event_name=job.event_name,
            event_date=job.event_date,
            organization_name=job.organization_name,
            output_path=output_path,
        )
        cert.status = CertificateStatus.SUCCESS.value
        cert.file_path = str(output_path)
        job.successful_count += 1
    except Exception as exc:
        cert.status = CertificateStatus.FAILED.value
        cert.error_message = str(exc)
        job.failed_count += 1
    finally:
        db.commit()  # Commits progress immediately so clients see live updates
```

**Outcome**:
If Recipient #2 triggers an exception:
- Recipient #1 is marked `SUCCESS`.
- Recipient #2 is marked `FAILED` with the exact error message recorded.
- Recipient #3 is generated and marked `SUCCESS`.
- The overall job finishes with status `COMPLETED`, `total=3`, `completed=3`, `successful=2`, `failed=1`.

---

## Testing

The project includes an extensive automated test suite covering all functional and non-functional requirements.

### Running Tests
Execute the tests using `pytest`:
```bash
pytest -v
```

### Test Coverage Highlights:
- **`test_job_creation.py`**: Health check, valid job submission, database record persistence.
- **`test_validation.py`**: Blank strings, missing keys, invalid dates, malformed emails, empty recipient lists, whitespace trimming.
- **`test_certificate_generation.py`**: Direct ReportLab canvas drawing, header signature verification (`%PDF-`), human-readable date formatting.
- **`test_job_status.py`**: 404 handling, real-time progress calculations, certificates list inspection.
- **`test_failure_handling.py`**: Failure isolation mock test demonstrating successful generation for recipients even when an intermediate recipient fails.
- **`test_certificate_download.py`**: Valid PDF streaming response, headers verification, 404 on missing physical files, 403 on path-traversal attacks.

---

## Learning & Key Takeaways

1. **RESTful Asynchronous Workflows**: Designing long-running operations using HTTP `202 Accepted`, task tracking IDs, and status polling endpoints.
2. **Robust Schema Validation with Pydantic**: Leveraging `@field_validator` and `EmailStr` to sanitize, trim, and reject bad inputs at the API boundary before touching databases or filesystem.
3. **Database Relationships in SQLAlchemy**: Defining foreign keys, explicit relationships (`Job` 1-to-N `Certificate`), and transaction commits.
4. **Resilient Background Error Handling**: Implementing granular error boundaries so that unexpected errors in one item do not crash the entire worker.
5. **Programmatic PDF Generation**: Using ReportLab canvases, coordinate math, fonts, and borders to create professional certificates.
6. **Defensive File Security**: Generating filenames strictly from database IDs and asserting path constraints to eliminate Directory Traversal (`../`) vulnerabilities.

---

## Future Scope & Production Enhancements

While this project is deliberately structured without over-engineering for an intern assignment, it is architected so that the following production enhancements can be integrated seamlessly:

1. **Dedicated Distributed Task Queues**: Replace in-process `BackgroundTasks` with **Celery** or **ARQ** backed by **Redis** or RabbitMQ for multi-worker scaling across multiple servers.
2. **PostgreSQL Database**: Migrate from SQLite to PostgreSQL with connection pooling (`asyncpg` / `psycopg`) to support high concurrency.
3. **Cloud Object Storage (AWS S3 / GCP Cloud Storage)**: Store generated PDF assets in S3 buckets with signed expiring URLs instead of the local filesystem.
4. **Email Delivery Integration**: Add an optional flag to automatically email the generated PDF attachment to each recipient upon completion using SendGrid, SES, or SMTP.
5. **Bulk ZIP Download**: Provide an endpoint (`GET /api/jobs/{job_id}/download-zip`) that compresses all generated PDFs into a single ZIP archive for event administrators.
6. **Multiple Certificate Templates**: Allow organizers to pick from a catalog of predefined visual themes (e.g., modern, academic, gold-foil).
7. **Authentication & Multi-Tenancy**: Protect administrative endpoints using JWT / OAuth2 authentication and organize jobs by user or organization accounts.
8. **Observability & Metrics**: Add OpenTelemetry tracing and Prometheus metrics to monitor generation latency and failure rates.
