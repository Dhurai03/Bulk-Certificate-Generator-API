from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Job(Base):
    """Database model for bulk certificate generation jobs."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_name = Column(String(255), nullable=False)
    event_date = Column(Date, nullable=False)
    organization_name = Column(String(255), nullable=False)
    status = Column(
        String(50),
        default=JobStatus.QUEUED.value,
        nullable=False,
        index=True,
    )
    total_count = Column(Integer, default=0, nullable=False)
    successful_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime, nullable=True)

    # Relationship to individual certificate records
    certificates = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="Certificate.id",
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, status={self.status}, total={self.total_count})>"
