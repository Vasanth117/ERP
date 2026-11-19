"""Examination report export jobs."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class ExamReportJobStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExamReportJob(Document):
    tenant_id: PydanticObjectId
    requested_by: PydanticObjectId
    report_type: str
    filters: dict[str, Any] = Field(default_factory=dict)
    output_format: str = "json"
    status: ExamReportJobStatus = ExamReportJobStatus.PROCESSING
    row_count: int = 0
    totals: dict[str, Any] = Field(default_factory=dict)
    file_content_base64: str | None = None
    error_message: str | None = None
    idempotency_key: str | None = None
    expires_at: datetime
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "exam_report_jobs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", ASCENDING)], name="exam_report_jobs_tenant"),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_exam_report_job_idempotency",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]