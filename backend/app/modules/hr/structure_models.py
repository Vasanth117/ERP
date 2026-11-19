"""HR organization structure (designations, classifications, assignments, transfers)."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrEmployeeTransferStatus, HrEmploymentClassificationKind, HrWorkLocationStatus


class HrDesignation(Document):
    tenant_id: PydanticObjectId
    designation_code: str = Field(max_length=64)
    name: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=64)
    hierarchy_level: int = Field(default=0, ge=0)
    parent_designation_id: PydanticObjectId | None = None
    applicable_department_ids: list[PydanticObjectId] = Field(default_factory=list)
    applicable_employment_categories: list[str] = Field(default_factory=list)
    is_active: bool = True
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_designations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("designation_code", ASCENDING)],
                unique=True,
                name="unique_hr_designation_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], name="hr_designations_active"),
        ]


class HrEmploymentClassification(Document):
    tenant_id: PydanticObjectId
    code: str = Field(max_length=64)
    label: str = Field(max_length=200)
    kind: HrEmploymentClassificationKind
    description: str | None = Field(default=None, max_length=2000)
    rules: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employment_classifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("kind", ASCENDING), ("code", ASCENDING)],
                unique=True,
                name="unique_hr_employment_classification",
            ),
        ]


class HrWorkLocation(Document):
    tenant_id: PydanticObjectId
    campus_id: PydanticObjectId
    location_code: str = Field(max_length=64)
    name: str = Field(max_length=200)
    office_label: str | None = Field(default=None, max_length=200)
    institution_department_id: PydanticObjectId | None = None
    status: HrWorkLocationStatus = HrWorkLocationStatus.ACTIVE
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_work_locations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("location_code", ASCENDING)],
                unique=True,
                name="unique_hr_work_location",
            ),
        ]


class HrEmployeeCurrentAssignment(Document):
    """Authoritative HR view of current organizational placement."""

    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    employee_record_id: PydanticObjectId
    institution_department_id: PydanticObjectId | None = None
    central_department_id: PydanticObjectId | None = None
    sub_department_id: PydanticObjectId | None = None
    designation_id: PydanticObjectId | None = None
    designation_code: str | None = None
    employment_type_code: str | None = None
    employment_category_code: str | None = None
    campus_id: PydanticObjectId | None = None
    work_location_id: PydanticObjectId | None = None
    organization_unit_id: PydanticObjectId | None = None
    reporting_manager_user_id: PydanticObjectId | None = None
    effective_from: date | None = None
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employee_current_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING)],
                unique=True,
                name="unique_hr_current_assignment",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("institution_department_id", ASCENDING)],
                name="hr_assignments_by_dept",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("reporting_manager_user_id", ASCENDING)],
                name="hr_assignments_by_manager",
            ),
        ]


class HrEmployeeTransferRequest(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    status: HrEmployeeTransferStatus = HrEmployeeTransferStatus.DRAFT
    from_assignment: dict[str, Any] = Field(default_factory=dict)
    to_institution_department_id: PydanticObjectId | None = None
    to_central_department_id: PydanticObjectId | None = None
    to_designation_id: PydanticObjectId | None = None
    to_designation_code: str | None = None
    to_employment_type_code: str | None = None
    to_employment_category_code: str | None = None
    to_campus_id: PydanticObjectId | None = None
    to_work_location_id: PydanticObjectId | None = None
    to_reporting_manager_user_id: PydanticObjectId | None = None
    to_organization_unit_id: PydanticObjectId | None = None
    effective_date: date
    reason: str = Field(max_length=2000)
    requires_approval: bool = True
    requested_by: PydanticObjectId | None = None
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    approval_note: str | None = Field(default=None, max_length=2000)
    rejection_note: str | None = Field(default=None, max_length=2000)
    applied_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employee_transfer_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("status", ASCENDING)],
                name="hr_transfers_by_employee",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("effective_date", ASCENDING)],
                name="hr_transfers_pending",
            ),
        ]


class HrEmployeeAssignmentHistory(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    change_type: str = Field(max_length=64)
    assignment_snapshot: dict[str, Any] = Field(default_factory=dict)
    effective_from: date | None = None
    effective_to: date | None = None
    reason: str | None = Field(default=None, max_length=2000)
    approval: dict[str, Any] = Field(default_factory=dict)
    transfer_request_id: PydanticObjectId | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employee_assignment_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_assignment_history_by_user",
            ),
        ]


class HrReportingManagerHistory(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    manager_user_id: PydanticObjectId
    effective_from: date
    effective_to: date | None = None
    actor_id: PydanticObjectId | None = None
    reason: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_reporting_manager_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("effective_from", DESCENDING)],
                name="hr_manager_history_by_user",
            ),
        ]


class HrWorkLocationHistory(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    from_campus_id: PydanticObjectId | None = None
    to_campus_id: PydanticObjectId | None = None
    from_work_location_id: PydanticObjectId | None = None
    to_work_location_id: PydanticObjectId | None = None
    effective_from: date
    reason: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_work_location_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("employee_user_id", ASCENDING)], name="hr_location_history_by_user"),
        ]