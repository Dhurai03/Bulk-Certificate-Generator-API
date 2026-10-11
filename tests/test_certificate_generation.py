from datetime import date
from pathlib import Path
from app.services.certificate_generator import generate_certificate, format_certificate_date


def test_format_certificate_date():
    """Verify certificate date formatting converts dates into readable strings."""
    assert format_certificate_date(date(2026, 10, 10)) == "10 October 2026"
    assert format_certificate_date("2026-10-10") == "10 October 2026"
    assert format_certificate_date("Custom Date String") == "Custom Date String"


def test_generate_certificate_pdf(tmp_path: Path):
    """Verify generate_certificate produces a valid, non-empty PDF file."""
    output_pdf = tmp_path / "subfolder" / "certificate_1.pdf"

    result_path = generate_certificate(
        certificate_id=1,
        recipient_name="Dhurai Murugan",
        event_name="Python Workshop 2026",
        event_date=date(2026, 10, 10),
        organization_name="ABC Organization",
        output_path=output_pdf,
    )

    assert result_path.exists()
    assert result_path.is_file()
    assert result_path.stat().st_size > 500

    # Read binary header to ensure it's a valid PDF file
    with open(result_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"


def test_generate_certificate_with_string_date(tmp_path: Path):
    """Verify generate_certificate works with string date representations."""
    output_pdf = tmp_path / "certificate_2.pdf"

    result_path = generate_certificate(
        certificate_id=2,
        recipient_name="Arun Kumar",
        event_name="FastAPI Masterclass",
        event_date="2026-10-10",
        organization_name="ABC Organization",
        output_path=output_pdf,
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 500
