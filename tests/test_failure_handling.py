import pytest
from fastapi.testclient import TestClient
from app.services.certificate_generator import generate_certificate as original_generate_certificate


def test_individual_certificate_failure_isolation(client: TestClient, monkeypatch):
    """
    Simulate failure for an individual recipient and verify:
    1. Recipient 1 (Dhurai) -> SUCCESS
    2. Recipient 2 (Arun)   -> FAILED (simulated exception)
    3. Recipient 3 (Priya)  -> SUCCESS
    4. Overall job status is COMPLETED with successful=2, failed=1, total=3.
    """
    def mock_generate_certificate(certificate_id, recipient_name, event_name, event_date, organization_name, output_path):
        if "Arun" in recipient_name:
            raise RuntimeError("Simulated PDF generation error for Arun")
        return original_generate_certificate(
            certificate_id=certificate_id,
            recipient_name=recipient_name,
            event_name=event_name,
            event_date=event_date,
            organization_name=organization_name,
            output_path=output_path,
        )

    # Monkeypatch the generator function in the job_processor module
    monkeypatch.setattr(
        "app.services.job_processor.generate_certificate",
        mock_generate_certificate,
    )

    payload = {
        "event_name": "Python Workshop 2026",
        "event_date": "2026-10-10",
        "organization_name": "ABC Organization",
        "recipients": [
            {"name": "Dhurai Murugan", "email": "dhurai@example.com"},
            {"name": "Arun Kumar", "email": "arun@example.com"},
            {"name": "Priya", "email": "priya@example.com"},
        ],
    }

    create_resp = client.post("/api/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    # Verify overall job status
    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    assert status_data["job_id"] == job_id
    assert status_data["status"] == "COMPLETED"
    assert status_data["total"] == 3
    assert status_data["completed"] == 3
    assert status_data["successful"] == 2
    assert status_data["failed"] == 1
    assert status_data["progress_percentage"] == 100

    # Verify individual certificate results
    certs_resp = client.get(f"/api/jobs/{job_id}/certificates")
    assert certs_resp.status_code == 200
    certs = certs_resp.json()
    assert len(certs) == 3

    # Find certificates by recipient
    dhurai_cert = next(c for c in certs if c["recipient_name"] == "Dhurai Murugan")
    arun_cert = next(c for c in certs if c["recipient_name"] == "Arun Kumar")
    priya_cert = next(c for c in certs if c["recipient_name"] == "Priya")

    # Dhurai should be successful
    assert dhurai_cert["status"] == "SUCCESS"
    assert dhurai_cert["file_name"] is not None
    assert dhurai_cert["error_message"] is None

    # Arun should be failed with error details recorded
    assert arun_cert["status"] == "FAILED"
    assert arun_cert["file_name"] is None
    assert arun_cert["error_message"] == "Simulated PDF generation error for Arun"

    # Priya should be successful despite Arun's failure earlier in the batch
    assert priya_cert["status"] == "SUCCESS"
    assert priya_cert["file_name"] is not None
    assert priya_cert["error_message"] is None

    # Verify download behaviors
    # Dhurai: 200 OK
    resp_dhurai = client.get(f"/api/certificates/{dhurai_cert['certificate_id']}")
    assert resp_dhurai.status_code == 200
    assert resp_dhurai.headers["content-type"] == "application/pdf"

    # Arun: 400 Bad Request
    resp_arun = client.get(f"/api/certificates/{arun_cert['certificate_id']}")
    assert resp_arun.status_code == 400
    assert "Simulated PDF generation error" in resp_arun.json()["detail"]

    # Priya: 200 OK
    resp_priya = client.get(f"/api/certificates/{priya_cert['certificate_id']}")
    assert resp_priya.status_code == 200
    assert resp_priya.headers["content-type"] == "application/pdf"
