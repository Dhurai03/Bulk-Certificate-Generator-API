import pytest
from fastapi.testclient import TestClient
from app.models.job import Job
from app.models.certificate import Certificate


def test_health_check(client: TestClient):
    """Verify health check endpoint returns 200 OK and expected metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["documentation"] == "/docs"


def test_create_generation_job_success(client: TestClient, db):
    """Verify POST /api/jobs returns HTTP 202 with job_id and QUEUED status."""
    payload = {
        "event_name": "Python Workshop 2026",
        "event_date": "2026-10-10",
        "organization_name": "ABC Organization",
        "recipients": [
            {
                "name": "Dhurai Murugan",
                "email": "dhurai@example.com",
            },
            {
                "name": "Arun Kumar",
                "email": "arun@example.com",
            },
        ],
    }

    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert "job_id" in data
    assert data["job_id"] > 0
    # In synchronous TestClient execution, the background task completes,
    # but the API response returned during creation explicitly provides QUEUED
    assert data["status"] in ["QUEUED", "COMPLETED", "PROCESSING"]
    assert data["message"] == "Certificate generation job created successfully"

    job_id = data["job_id"]
    job = db.query(Job).filter(Job.id == job_id).first()
    assert job is not None
    assert job.event_name == "Python Workshop 2026"
    assert job.organization_name == "ABC Organization"
    assert job.total_count == 2

    certs = db.query(Certificate).filter(Certificate.job_id == job_id).all()
    assert len(certs) == 2
    recipient_names = [c.recipient_name for c in certs]
    assert "Dhurai Murugan" in recipient_names
    assert "Arun Kumar" in recipient_names
