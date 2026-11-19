"""HR organization API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.identity_schemas import InstitutionDepartmentCreate, InstitutionDepartmentRead, InstitutionDepartmentUpdate, OrganizationUnitRead
from app.modules.hr.enums import HrEmployeeTransferStatus, HrEmploymentClassificationKind, HrWorkLocationStatus
from app.modules.hr.structure_models import (
    HrDesignation,
    HrEmploymentClassification,
    HrEmployeeCurrentAssignment,
    HrEmployeeTransferRequest,
    HrWorkLocation,
)


class OrgHierarchyNode(BaseModel):
    node_id: str
    node_type: str
    code: str
    name: str
    parent_id: str | None = None
    status: str | None = None
    head_user_id: str | None = None
    children: list["OrgHierarchyNode"] = Field(default_factory=list)


class OrganizationOverview(BaseModel):
    department_count: int = 0
    organization_unit_count: int = 0
    campus_count: int = 0
    active_designations: int = 0
    work_locations: int = 0
    hierarchy: list[OrgHierarchyNode] = Field(default_factory=list)


class DepartmentEmployeeStats(BaseModel):
    department_id: str
    total_employees: int = 0
    active_employees: int = 0
    probation_employees: int = 0


class DepartmentEmployeesRead(BaseModel):
    department: InstitutionDepartmentRead
    stats: DepartmentEmployeeStats
    employee_user_ids: list[str] = Field(default_factory=list)


class HrDesignationCreate(BaseModel):
    designation_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str | None = None
    hierarchy_level: int = 0
    parent_designation_id: str | None = None
    applicable_department_ids: list[str] = Field(default_factory=list)
    applicable_employment_categories: list[str] = Field(default_factory=list)


class HrDesignationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    hierarchy_level: int | None = None
    parent_designation_id: str | None = None
    applicable_department_ids: list[str] | None = None
    applicable_employment_categories: list[str] | None = None
    is_active: bool | None = None


class HrDesignationRead(BaseModel):
    designation_id: str
    designation_code: str
    name: str
    description: str | None
    category: str | None
    hierarchy_level: int
    parent_designation_id: str | None
    is_active: bool
    employee_count: int = 0

    @classmethod
    def from_doc(cls, doc: HrDesignation, *, employee_count: int = 0) -> "HrDesignationRead":
        return cls(
            designation_id=str(doc.id),
            designation_code=doc.designation_code,
            name=doc.name,
            description=doc.description,
            category=doc.category,
            hierarchy_level=doc.hierarchy_level,
            parent_designation_id=str(doc.parent_designation_id) if doc.parent_designation_id else None,
            is_active=doc.is_active,
            employee_count=employee_count,
        )


class HrEmploymentClassificationUpsert(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=200)
    kind: HrEmploymentClassificationKind
    description: str | None = None
    rules: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class HrEmploymentClassificationRead(BaseModel):
    classification_id: str
    code: str
    label: str
    kind: HrEmploymentClassificationKind
    description: str | None
    rules: dict[str, Any]
    is_active: bool

    @classmethod
    def from_doc(cls, doc: HrEmploymentClassification) -> "HrEmploymentClassificationRead":
        return cls(
            classification_id=str(doc.id),
            code=doc.code,
            label=doc.label,
            kind=doc.kind,
            description=doc.description,
            rules=doc.rules,
            is_active=doc.is_active,
        )


class HrWorkLocationCreate(BaseModel):
    campus_id: str
    location_code: str
    name: str
    office_label: str | None = None
    institution_department_id: str | None = None


class HrWorkLocationRead(BaseModel):
    work_location_id: str
    campus_id: str
    location_code: str
    name: str
    office_label: str | None
    institution_department_id: str | None
    status: HrWorkLocationStatus

    @classmethod
    def from_doc(cls, doc: HrWorkLocation) -> "HrWorkLocationRead":
        return cls(
            work_location_id=str(doc.id),
            campus_id=str(doc.campus_id),
            location_code=doc.location_code,
            name=doc.name,
            office_label=doc.office_label,
            institution_department_id=str(doc.institution_department_id) if doc.institution_department_id else None,
            status=doc.status,
        )


class EmployeeAssignmentRead(BaseModel):
    employee_user_id: str
    institution_department_id: str | None = None
    central_department_id: str | None = None
    designation_id: str | None = None
    designation_code: str | None = None
    employment_type_code: str | None = None
    employment_category_code: str | None = None
    campus_id: str | None = None
    work_location_id: str | None = None
    organization_unit_id: str | None = None
    reporting_manager_user_id: str | None = None
    effective_from: date | None = None

    @classmethod
    def from_doc(cls, doc: HrEmployeeCurrentAssignment) -> "EmployeeAssignmentRead":
        return cls(
            employee_user_id=str(doc.employee_user_id),
            institution_department_id=str(doc.institution_department_id) if doc.institution_department_id else None,
            central_department_id=str(doc.central_department_id) if doc.central_department_id else None,
            designation_id=str(doc.designation_id) if doc.designation_id else None,
            designation_code=doc.designation_code,
            employment_type_code=doc.employment_type_code,
            employment_category_code=doc.employment_category_code,
            campus_id=str(doc.campus_id) if doc.campus_id else None,
            work_location_id=str(doc.work_location_id) if doc.work_location_id else None,
            organization_unit_id=str(doc.organization_unit_id) if doc.organization_unit_id else None,
            reporting_manager_user_id=str(doc.reporting_manager_user_id) if doc.reporting_manager_user_id else None,
            effective_from=doc.effective_from,
        )


class EmployeeAssignmentUpdate(BaseModel):
    institution_department_id: str | None = None
    designation_id: str | None = None
    employment_type_code: str | None = None
    employment_category_code: str | None = None
    campus_id: str | None = None
    work_location_id: str | None = None
    reporting_manager_user_id: str | None = None
    effective_from: date | None = None
    reason: str = Field(min_length=3, max_length=2000)


class ReportingManagerUpdate(BaseModel):
    manager_user_id: str
    effective_from: date | None = None
    reason: str = Field(min_length=3, max_length=2000)


class EmployeeTransferCreate(BaseModel):
    to_institution_department_id: str | None = None
    to_central_department_id: str | None = None
    to_designation_id: str | None = None
    to_employment_type_code: str | None = None
    to_employment_category_code: str | None = None
    to_campus_id: str | None = None
    to_work_location_id: str | None = None
    to_reporting_manager_user_id: str | None = None
    effective_date: date
    reason: str = Field(min_length=3, max_length=2000)
    requires_approval: bool = True


class TransferApproval(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    note: str | None = Field(default=None, max_length=2000)


class EmployeeTransferRead(BaseModel):
    transfer_id: str
    employee_user_id: str
    status: HrEmployeeTransferStatus
    from_assignment: dict[str, Any]
    effective_date: date
    reason: str
    requires_approval: bool
    approved_by: str | None = None
    approval_note: str | None = None
    rejection_note: str | None = None

    @classmethod
    def from_doc(cls, doc: HrEmployeeTransferRequest) -> "EmployeeTransferRead":
        return cls(
            transfer_id=str(doc.id),
            employee_user_id=str(doc.employee_user_id),
            status=doc.status,
            from_assignment=doc.from_assignment,
            effective_date=doc.effective_date,
            reason=doc.reason,
            requires_approval=doc.requires_approval,
            approved_by=str(doc.approved_by) if doc.approved_by else None,
            approval_note=doc.approval_note,
            rejection_note=doc.rejection_note,
        )


class AssignmentHistoryItem(BaseModel):
    change_type: str
    assignment_snapshot: dict[str, Any]
    effective_from: date | None
    effective_to: date | None
    reason: str | None
    approval: dict[str, Any]
    created_at: datetime


class ReportingHierarchyRead(BaseModel):
    employee_user_id: str
    chain: list[str] = Field(default_factory=list)
    direct_reports: list[str] = Field(default_factory=list)