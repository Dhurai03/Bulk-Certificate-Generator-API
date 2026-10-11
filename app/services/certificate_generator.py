from datetime import date, datetime
from pathlib import Path
from typing import Union
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def format_certificate_date(event_date: Union[date, str]) -> str:
    """Format the event date into a human-readable display string."""
    if isinstance(event_date, date):
        return event_date.strftime("%d %B %Y")
    if isinstance(event_date, str):
        try:
            parsed = datetime.strptime(event_date, "%Y-%m-%d").date()
            return parsed.strftime("%d %B %Y")
        except ValueError:
            return event_date
    return str(event_date)


def generate_certificate(
    certificate_id: int,
    recipient_name: str,
    event_name: str,
    event_date: Union[date, str],
    organization_name: str,
    output_path: Path,
) -> Path:
    """
    Generate a professional PDF certificate for a recipient using a fixed, elegant template.

    Args:
        certificate_id: Unique database ID of the certificate.
        recipient_name: Full name of the recipient.
        event_name: Title of the event or workshop.
        event_date: Date the event took place.
        organization_name: Issuing organization or institution.
        output_path: Filesystem path where the PDF should be saved.

    Returns:
        Path: Path to the generated PDF certificate.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Standard landscape letter size: 792 pt x 612 pt
    page_width, page_height = landscape(letter)
    c = canvas.Canvas(str(output_path), pagesize=landscape(letter))
    c.setTitle(f"Certificate - {recipient_name}")

    # Color palette
    navy = colors.HexColor("#0F2942")
    gold = colors.HexColor("#C59B27")
    charcoal = colors.HexColor("#2D3748")
    subtext_color = colors.HexColor("#4A5568")
    light_gold = colors.HexColor("#FAF089")

    # 1. Decorative Outer Border
    c.setStrokeColor(navy)
    c.setLineWidth(4.0)
    c.rect(28, 28, page_width - 56, page_height - 56, stroke=1, fill=0)

    # 2. Decorative Inner Border
    c.setStrokeColor(gold)
    c.setLineWidth(1.5)
    c.rect(36, 36, page_width - 72, page_height - 72, stroke=1, fill=0)

    # 3. Corner Accent Flourishes
    corner_size = 18
    for (x, y) in [
        (42, 42),
        (page_width - 42 - corner_size, 42),
        (42, page_height - 42 - corner_size),
        (page_width - 42 - corner_size, page_height - 42 - corner_size),
    ]:
        c.setFillColor(gold)
        c.rect(x, y, corner_size, corner_size, stroke=0, fill=1)

    # 4. Title Header
    center_x = page_width / 2.0
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(gold)
    c.drawCentredString(center_x, page_height - 95, "CERTIFICATE OF PARTICIPATION")

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(navy)
    c.drawCentredString(center_x, page_height - 130, "CERTIFICATE OF EXCELLENCE")

    # Decorative header divider
    c.setStrokeColor(gold)
    c.setLineWidth(2)
    c.line(center_x - 120, page_height - 142, center_x + 120, page_height - 142)

    # 5. Presentation Text
    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(subtext_color)
    c.drawCentredString(center_x, page_height - 185, "This certificate is proudly presented to")

    # 6. Recipient Name
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(navy)
    c.drawCentredString(center_x, page_height - 235, recipient_name.upper())

    # Underline for name
    name_width = max(c.stringWidth(recipient_name.upper(), "Helvetica-Bold", 28) + 40, 240)
    c.setStrokeColor(gold)
    c.setLineWidth(1.5)
    c.line(center_x - (name_width / 2), page_height - 248, center_x + (name_width / 2), page_height - 248)

    # 7. Achievement Statement
    c.setFont("Helvetica", 13)
    c.setFillColor(subtext_color)
    c.drawCentredString(center_x, page_height - 290, "for successfully completing")

    # 8. Event Name
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(charcoal)
    c.drawCentredString(center_x, page_height - 325, event_name)

    # 9. Issuing Details (Date & Organization)
    formatted_date = format_certificate_date(event_date)

    # Left Column: Event Date
    date_x = 180
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(navy)
    c.drawCentredString(date_x, 150, formatted_date)
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.setLineWidth(1)
    c.line(date_x - 80, 140, date_x + 80, 140)
    c.setFont("Helvetica", 10)
    c.setFillColor(subtext_color)
    c.drawCentredString(date_x, 125, "Date of Issuance")

    # Right Column: Organization
    org_x = page_width - 180
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(navy)
    c.drawCentredString(org_x, 150, organization_name)
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.setLineWidth(1)
    c.line(org_x - 100, 140, org_x + 100, 140)
    c.setFont("Helvetica", 10)
    c.setFillColor(subtext_color)
    c.drawCentredString(org_x, 125, "Issuing Organization")

    # 10. Footer Certificate ID / Verification Badge
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#A0AEC0"))
    c.drawCentredString(
        center_x,
        55,
        f"Certificate ID: CERT-{certificate_id:06d}  |  Verified Digital Credential",
    )

    c.showPage()
    c.save()

    return output_path
