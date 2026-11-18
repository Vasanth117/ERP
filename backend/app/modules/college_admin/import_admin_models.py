"""College admin data import and migration collections."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class ImportJobStatus(str, Enum):
    UPLOADED = "uploaded"
    MAPPED = "mapped"
    VALIDATED = "validated"
    PREVIEW_READY = "preview_ready"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ImportEntityType(str, Enum):
    STUDENTS = "students"
    FACULTY = "faculty"
    EMPLOYEES = "employees"
    COURSES = "courses"
    ATTENDANCE = "attendance"
    FINANCE = "finance"
    CUSTOM = "custom"


class InstitutionImportTemplate(Document):
    tenant_id: PydanticObjectId
    template_id: str
    entity_type: ImportEntityType
    title: str
    version: int = 1
    required_columns: list[str] = Field(default_factory=list)
    optional_columns: list[str] = Field(default_factory=list)
    max_rows: int = 5000
    requires_approval: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_import_templates"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("template_id", ASCENDING)], unique=True, name="unique_import_template"),
        ]


class InstitutionImportMapping(Document):
    tenant_id: PydanticObjectId
    mapping_id: str
    template_id: str
    column_map: dict[str, str] = Field(default_factory=dict)
    duplicate_key_field: str | None = None
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_import_mappings"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("mapping_id", ASCENDING)], unique=True, name="unique_import_mapping"),
        ]


class InstitutionImportJob(Document):
    tenant_id: PydanticObjectId
    job_id: str
    idempotency_key: str
    template_id: str
    mapping_id: str | None = None
    entity_type: ImportEntityType
    status: ImportJobStatus = ImportJobStatus.UPLOADED
    file_name: str
    storage_key: str
    file_checksum: str
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    executed_rows: int = 0
    failed_rows: int = 0
    progress_percent: float = 0
    error_message: str | None = None
    requires_approval: bool = True
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    rollback_token: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "institution_import_jobs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("job_id", ASCENDING)], unique=True, name="unique_import_job"),
            IndexModel([("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)], unique=True, name="unique_import_idempotency"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], name="import_jobs_status"),
        ]


class InstitutionImportValidationError(Document):
    tenant_id: PydanticObjectId
    job_id: str
    row_number: int
    field: str | None = None
    error_code: str
    message: str
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_import_validation_errors"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("job_id", ASCENDING), ("row_number", ASCENDING)], name="import_errors"),
        ]


class InstitutionImportRowResult(Document):
    tenant_id: PydanticObjectId
    job_id: str
    row_number: int
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_import_row_results"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("job_id", ASCENDING), ("row_number", ASCENDING)], unique=True, name="unique_row_result"),
            IndexModel([("tenant_id", ASCENDING), ("job_id", ASCENDING), ("status", ASCENDING)], name="row_results_status"),
        ]


class InstitutionMigrationHistory(Document):
    tenant_id: PydanticObjectId
    migration_id: str
    job_id: str
    action: str
    summary: str
    compensating_action: dict[str, Any] | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_migration_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="migration_history"),
        ]