from pathlib import Path
from fastapi.testclient import TestClient
from app.config import settings
from app.models.certificate import Certificate, CertificateStatus


def test_download_certificate_not_found(client: TestClient):
    """Verify downloading a non-existent certificate returns 404."""
    response = client.get("/api/certificates/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_successful_certificate(client: TestClient):
    """Verify downloading an existing, generated certificate returns a valid PDF."""
    payload = {
        "event_name": "API Design Best Practices",
        "event_date": "2026-10-10",
        "organization_name": "ABC Organization",
        "recipients": [{"name": "Dhurai Murugan", "email": "dhurai@example.com"}],
    }

    create_resp = client.post("/api/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    certs_resp = client.get(f"/api/jobs/{job_id}/certificates")
    assert certs_resp.status_code == 200
    cert = certs_resp.json()[0]
    cert_id = cert["certificate_id"]

    download_resp = client.get(f"/api/certificates/{cert_id}")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"
    assert f"certificate_{cert_id}.pdf" in download_resp.headers.get("content-disposition", "")
    assert download_resp.content.startswith(b"%PDF-")


def test_download_missing_physical_file(client: TestClient, db):
    """Verify returning 404 when database record exists but the physical PDF is missing."""
    ghost_cert = Certificate(
        job_id=1,
        recipient_name="Ghost User",
        recipient_email="ghost@example.com",
        status=CertificateStatus.SUCCESS.value,
        file_path=str(settings.GENERATED_DIR / "non_existent_file_12345.pdf"),
    )
    db.add(ghost_cert)
    db.commit()
    db.refresh(ghost_cert)

    response = client.get(f"/api/certificates/{ghost_cert.id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_unauthorized_path_traversal(client: TestClient, db):
    """Verify returning 403 when a certificate record points outside the generated directory."""
    traversal_cert = Certificate(
        job_id=1,
        recipient_name="Hacker User",
        recipient_email="hacker@example.com",
        status=CertificateStatus.SUCCESS.value,
        file_path="C:/Windows/System32/drivers/etc/hosts",
    )
    db.add(traversal_cert)
    db.commit()
    db.refresh(traversal_cert)

    response = client.get(f"/api/certificates/{traversal_cert.id}")
    assert response.status_code == 403
    assert "unauthorized" in response.json()["detail"].lower()
