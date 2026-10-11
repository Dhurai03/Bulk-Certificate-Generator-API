from datetime import date
from typing import List
from pydantic import BaseModel, Field, field_validator
from app.schemas.certificate import RecipientCreate


class JobCreate(BaseModel):
    """Schema for creating a new bulk certificate generation job."""

    event_name: str = Field(..., description="Name of the event")
    event_date: date = Field(..., description="Date of the event in YYYY-MM-DD format")
    organization_name: str = Field(..., description="Name of the issuing organization")
    recipients: List[RecipientCreate] = Field(
        ...,
        min_length=1,
        description="List of recipients (at least 1 recipient required)",
    )

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Event name cannot be empty or blank")
        return trimmed

    @field_validator("organization_name")
    @classmethod
    def validate_organization_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Organization name cannot be empty or blank")
        return trimmed


class JobCreateResponse(BaseModel):
    """Schema for the response returned immediately upon job creation (HTTP 202)."""

    job_id: int
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Schema for retrieving overall job status and progress metrics."""

    job_id: int
    status: str
    total: int
    completed: int
    successful: int
    failed: int
    progress_percentage: int

    @classmethod
    def from_job_model(cls, job) -> "JobStatusResponse":
        completed = job.successful_count + job.failed_count
        progress = int((completed / job.total_count) * 100) if job.total_count > 0 else 0
        return cls(
            job_id=job.id,
            status=job.status,
            total=job.total_count,
            completed=completed,
            successful=job.successful_count,
            failed=job.failed_count,
            progress_percentage=progress,
        )

    model_config = {
        "from_attributes": True,
    }
