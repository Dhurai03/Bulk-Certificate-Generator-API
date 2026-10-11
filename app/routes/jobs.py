from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.job import JobCreate, JobCreateResponse, JobStatusResponse
from app.schemas.certificate import CertificateResponse
from app.services.job_processor import process_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a bulk certificate generation job",
    description="Validates recipients, persists the job and certificate records, and begins generation in the background.",
)
def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobCreateResponse:
    """
    Accepts bulk recipient data, initializes a generation job, and schedules background processing.
    """
    # 1. Create Job record
    new_job = Job(
        event_name=payload.event_name,
        event_date=payload.event_date,
        organization_name=payload.organization_name,
        status=JobStatus.QUEUED.value,
        total_count=len(payload.recipients),
        successful_count=0,
        failed_count=0,
    )
    db.add(new_job)
    db.flush()  # Populates new_job.id without closing transaction

    # 2. Create Certificate records for each recipient
    certificates = [
        Certificate(
            job_id=new_job.id,
            recipient_name=rec.name,
            recipient_email=rec.email,
            status=CertificateStatus.PENDING.value,
        )
        for rec in payload.recipients
    ]
    db.add_all(certificates)
    db.commit()
    db.refresh(new_job)

    # 3. Schedule background processing
    background_tasks.add_task(process_job, new_job.id)

    # 4. Return HTTP 202 Accepted response immediately
    return JobCreateResponse(
        job_id=new_job.id,
        status=new_job.status,
        message="Certificate generation job created successfully",
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status and progress",
    description="Retrieves the current status, total count, successful count, failed count, and progress percentage.",
)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    """
    Fetches the status and progress metrics of a generation job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found",
        )

    return JobStatusResponse.from_job_model(job)


@router.get(
    "/{job_id}/certificates",
    response_model=List[CertificateResponse],
    summary="List certificates belonging to a job",
    description="Returns detailed records for all individual certificates generated or pending within the job.",
)
def get_job_certificates(
    job_id: int,
    db: Session = Depends(get_db),
) -> List[CertificateResponse]:
    """
    Lists all recipient certificates belonging to the specified job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found",
        )

    return [CertificateResponse.from_orm_model(cert) for cert in job.certificates]
