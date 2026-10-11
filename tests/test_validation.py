import pytest
from fastapi.testclient import TestClient


def test_missing_event_name(client: TestClient):
    """Test validation failure when event_name is omitted."""
    payload = {
        "event_date": "2026-10-10",
        "organization_name": "ABC Organization",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_empty_or_whitespace_event_name(client: TestClient):
    """Test validation failure when event_name is empty or whitespace."""
    payload = {
        "event_name": "   ",
        "event_date": "2026-10-10",
        "organization_name": "ABC Organization",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_invalid_event_date(client: TestClient):
    """Test validation failure when event_date is not a valid date format."""
    payload = {
        "event_name": "Python Workshop",
        "event_date": "invalid-date-format",
        "organization_name": "ABC Organization",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_missing_organization_name(client: TestClient):
    """Test validation failure when organization_name is missing."""
    payload = {
        "event_name": "Python Workshop",
        "event_date": "2026-10-10",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_empty_organization_name(client: TestClient):
    """Test validation failure when organization_name is blank whitespace."""
    payload = {
        "event_name": "Python Workshop",
        "event_date": "2026-10-10",
        "organization_name": "   ",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_empty_recipients_list(client: TestClient):
    """Test validation failure when recipients array is empty."""
    payload = {
        "event_name": "Python Workshop",
        "event_date": "2026-10-10",
        "organization_name": "ABC Organization",
        "recipients": [],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_recipient_blank_name(client: TestClient):
    """Test validation failure when recipient name is blank."""
    payload = {
        "event_name": "Python Workshop",
        "event_date": "2026-10-10",
        "organization_name": "ABC Organization",
        "recipients": [{"name": "   ", "email": "user@example.com"}],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_recipient_invalid_email(client: TestClient):
    """Test validation failure when recipient email is malformed."""
    payload = {
        "event_name": "Python Workshop",
        "event_date": "2026-10-10",
        "organization_name": "ABC Organization",
        "recipients": [{"name": "Valid Name", "email": "not-an-email"}],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_whitespace_trimming(client: TestClient):
    """Test that valid input with surrounding whitespace is properly trimmed."""
    payload = {
        "event_name": "   Cloud Architecture Masterclass   ",
        "event_date": "2026-10-10",
        "organization_name": "   Acme Corp   ",
        "recipients": [{"name": "   Jane Doe   ", "email": "  jane@example.com  "}],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status_resp = client.get(f"/api/jobs/{job_id}/certificates")
    assert status_resp.status_code == 200
    certs = status_resp.json()
    assert len(certs) == 1
    assert certs[0]["recipient_name"] == "Jane Doe"
    assert certs[0]["recipient_email"] == "jane@example.com"
