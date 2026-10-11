from fastapi.testclient import TestClient


def test_job_not_found(client: TestClient):
    """Verify GET /api/jobs/{job_id} returns 404 when job does not exist."""
    response = client.get("/api/jobs/999999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_job_certificates_not_found(client: TestClient):
    """Verify GET /api/jobs/{job_id}/certificates returns 404 when job does not exist."""
    response = client.get("/api/jobs/999999/certificates")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_job_status_and_certificates_flow(client: TestClient):
    """Verify complete job progress flow and certificates retrieval."""
    payload = {
        "event_name": "Docker & Kubernetes 101",
        "event_date": "2026-11-15",
        "organization_name": "Tech Academy",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
        ],
    }

    create_resp = client.post("/api/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    # In TestClient, background tasks run synchronously
    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    assert status_data["job_id"] == job_id
    assert status_data["status"] == "COMPLETED"
    assert status_data["total"] == 2
    assert status_data["completed"] == 2
    assert status_data["successful"] == 2
    assert status_data["failed"] == 0
    assert status_data["progress_percentage"] == 100

    # Test listing certificates
    certs_resp = client.get(f"/api/jobs/{job_id}/certificates")
    assert certs_resp.status_code == 200
    certs_data = certs_resp.json()

    assert len(certs_data) == 2
    for cert in certs_data:
        assert cert["status"] == "SUCCESS"
        assert cert["file_name"] is not None
        assert cert["file_name"].startswith("certificate_")
        assert cert["file_name"].endswith(".pdf")
        assert cert["error_message"] is None
