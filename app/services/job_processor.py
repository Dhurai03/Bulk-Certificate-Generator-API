import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.job import Job, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.services.certificate_generator import generate_certificate
from app.utils.file_utils import get_certificate_path

logger = logging.getLogger("bulk_certificate_generator.job_processor")


def process_job(job_id: int, db_session: Optional[Session] = None) -> None:
    """
    Process all certificates in a bulk job asynchronously.

    This function:
    1. Updates the job status to 'PROCESSING'.
    2. Iterates through each certificate record.
    3. Generates the PDF certificate using ReportLab.
    4. Handles individual failures in isolation, recording the error
       without aborting other certificates.
    5. Incrementally updates job progress counts.
    6. Marks the overall job as 'COMPLETED' upon finishing all recipients.

    Args:
        job_id: The ID of the job to process.
        db_session: Optional existing DB session (useful for unit tests),
                    otherwise creates a dedicated session for background execution.
    """
    db = db_session or SessionLocal()
    job: Optional[Job] = None

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error("Job %s not found for processing", job_id)
            return

        # Mark job as PROCESSING
        job.status = JobStatus.PROCESSING.value
        db.commit()

        certificates = (
            db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.id)
            .all()
        )

        for cert in certificates:
            try:
                # Generate certificate PDF file
                output_path = get_certificate_path(cert.id)
                generate_certificate(
                    certificate_id=cert.id,
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    event_date=job.event_date,
                    organization_name=job.organization_name,
                    output_path=output_path,
                )

                # Mark individual certificate as SUCCESS
                cert.status = CertificateStatus.SUCCESS.value
                cert.file_path = str(output_path)
                cert.error_message = None
                cert.completed_at = datetime.now(timezone.utc)
                job.successful_count += 1

            except Exception as exc:
                # Isolate failure: Record error, mark certificate FAILED, continue loop
                logger.warning(
                    "Failed to generate certificate for recipient %s (ID %s): %s",
                    cert.recipient_name,
                    cert.id,
                    exc,
                )
                cert.status = CertificateStatus.FAILED.value
                cert.error_message = str(exc) or "Certificate generation failed"
                cert.completed_at = datetime.now(timezone.utc)
                job.failed_count += 1

            finally:
                # Commit progress after each certificate so GET /api/jobs/{id} reflects real-time progress
                db.commit()

        # Once all certificates have been processed, mark the job COMPLETED
        job.status = JobStatus.COMPLETED.value
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            "Job %s completed: total=%d, successful=%d, failed=%d",
            job.id,
            job.total_count,
            job.successful_count,
            job.failed_count,
        )

    except Exception as exc:
        logger.exception("Critical error encountered while processing job %s: %s", job_id, exc)
        if job:
            job.status = JobStatus.FAILED.value
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        # Only close if we created the session locally
        if db_session is None:
            db.close()
