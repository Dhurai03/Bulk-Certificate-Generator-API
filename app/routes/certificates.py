from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.certificate import Certificate, CertificateStatus
from app.utils.file_utils import get_certificate_filename, is_safe_path

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}",
    summary="Download certificate PDF",
    description="Returns the generated certificate PDF for a recipient if successfully processed.",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "The generated PDF certificate file.",
        },
        400: {"description": "Certificate is not yet ready or generation failed."},
        404: {"description": "Certificate record or physical file not found."},
    },
)
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
):
    """
    Downloads an individual recipient's certificate PDF.
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID {certificate_id} not found",
        )

    if cert.status == CertificateStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation failed: {cert.error_message or 'Unknown error'}",
        )

    if cert.status == CertificateStatus.PENDING.value or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate generation is still in progress. Please check back shortly.",
        )

    raw_path = Path(cert.file_path)
    # If path stored was relative, resolve relative to settings.GENERATED_DIR
    pdf_path = raw_path if raw_path.is_absolute() else (settings.GENERATED_DIR / raw_path)

    # Validate that file resides safely in our configured generated directory
    if not is_safe_path(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized file access path",
        )

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated certificate file was not found on the server filesystem",
        )

    filename = get_certificate_filename(cert.id)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
    )
