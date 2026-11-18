"""Library report export jobs."""

from datetime import datetime
from enum import StrEnum

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class LibraryReportJobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LibraryReportJob(Document):
    tenant_id: PydanticObjectId
    requested_by: PydanticObjectId
    report_type: str = Field(max_length=64)
    filters: dict = Field(default_factory=dict)
    output_format: str = Field(default="json", max_length=16)
    status: LibraryReportJobStatus = LibraryReportJobStatus.PENDING
    row_count: int = 0
    totals: dict = Field(default_factory=dict)
    file_content_base64: str | None = None
    error_message: str | None = Field(default=None, max_length=2000)
    expires_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "library_report_jobs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_library_report_job_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("requested_by", ASCENDING), ("created_at", DESCENDING)],
                name="library_report_job_requester",
            ),
        ]