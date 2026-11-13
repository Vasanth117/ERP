"""Faculty self-service API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class EmploymentInfoRead(BaseModel):
    status: str
    data: dict[str, Any]


class LeaveRequestCreate(BaseModel):
    leave_type: str = "casual"
    start_date: date
    end_date: date
    reason: str = Field(min_length=5, max_length=500)

    model_config = {"extra": "forbid"}


class LeaveRequestRead(BaseModel):
    id: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    status: str
    created_at: datetime


class PayslipListRead(BaseModel):
    status: str
    items: list[dict[str, Any]]


class PersonalDocumentRead(BaseModel):
    id: str
    label: str
    file_name: str
    mime_type: str
    document_type: str
    created_at: datetime


class ReportExportRead(BaseModel):
    id: str
    report_type: str
    status: str
    generated_at: datetime
    download_url: str | None = None


class PersonalActivityHistoryItem(BaseModel):
    activity_type: str
    title: str
    occurred_at: datetime
    source_module: str


class WorkloadReportRead(BaseModel):
    items: list[dict[str, Any]]
