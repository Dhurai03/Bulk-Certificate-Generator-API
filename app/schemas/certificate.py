from pathlib import Path
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class RecipientCreate(BaseModel):
    """Schema for individual recipient input."""

    name: str = Field(..., description="Full name of the certificate recipient")
    email: EmailStr = Field(..., description="Valid email address of the recipient")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Recipient name cannot be empty or blank")
        return trimmed

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class CertificateResponse(BaseModel):
    """Schema for certificate status and details in job listings."""

    certificate_id: int
    recipient_name: str
    recipient_email: str
    status: str
    file_name: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def from_orm_model(cls, cert) -> "CertificateResponse":
        file_name = Path(cert.file_path).name if cert.file_path else None
        return cls(
            certificate_id=cert.id,
            recipient_name=cert.recipient_name,
            recipient_email=cert.recipient_email,
            status=cert.status,
            file_name=file_name,
            error_message=cert.error_message,
        )

    model_config = {
        "from_attributes": True,
    }
