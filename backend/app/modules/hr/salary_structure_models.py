"""Salary components, templates, assignments and revision history."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import (
    HrSalaryAssignmentStatus,
    HrSalaryCalcType,
    HrSalaryComponentCategory,
    HrSalaryRevisionStatus,
    HrSalaryTemplateStatus,
)


class HrSalaryComponent(Document):
    tenant_id: PydanticObjectId
    component_code: str = Field(max_length=64)
    name: str = Field(max_length=200)
    category: HrSalaryComponentCategory
    calc_type: HrSalaryCalcType = HrSalaryCalcType.FIXED
    calculation_basis: str | None = Field(default=None, max_length=64)
    percentage_of: str | None = Field(default=None, max_length=64)
    employee_categories: list[str] = Field(default_factory=list)
    proration_rule: str | None = Field(default=None, max_length=64)
    statutory_ref: str | None = Field(default=None, max_length=128)
    tax_classification_ref: str | None = Field(default=None, max_length=128)
    effective_from: date
    effective_to: date | None = None
    is_active: bool = True
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_salary_components"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("component_code", ASCENDING)], unique=True, name="unique_salary_component"),
        ]


class HrSalaryTemplate(Document):
    tenant_id: PydanticObjectId
    template_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    template_kind: str = Field(max_length=64)
    component_lines: list[dict[str, Any]] = Field(default_factory=list)
    status: HrSalaryTemplateStatus = HrSalaryTemplateStatus.ACTIVE
    version: int = 1
    duplicated_from_version: int | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_salary_templates"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("template_code", ASCENDING), ("version", DESCENDING)],
                unique=True,
                name="unique_salary_template_version",
            ),
        ]


class HrEmployeeSalaryAssignment(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    template_id: PydanticObjectId
    template_version: int
    component_amounts: dict[str, str] = Field(default_factory=dict)
    earnings_total: str = "0"
    deductions_total: str = "0"
    gross_salary: str = "0"
    net_salary: str = "0"
    employer_contributions_total: str = "0"
    annual_compensation: str = "0"
    ctc: str | None = None
    effective_from: date
    effective_to: date | None = None
    status: HrSalaryAssignmentStatus = HrSalaryAssignmentStatus.DRAFT
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_salary_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("effective_from", DESCENDING)],
                name="salary_assignment_by_employee",
            ),
        ]


class HrEmployeeSalaryRevisionHistory(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    revision_code: str = Field(max_length=64)
    reason: str = Field(max_length=2000)
    revision_type: str = Field(max_length=64)
    current_assignment_id: PydanticObjectId | None = None
    template_id: PydanticObjectId | None = None
    proposed_component_amounts: dict[str, str] = Field(default_factory=dict)
    difference_summary: dict[str, str] = Field(default_factory=dict)
    effective_from: date
    status: HrSalaryRevisionStatus = HrSalaryRevisionStatus.DRAFT
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    resulting_assignment_id: PydanticObjectId | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_salary_revision_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("revision_code", ASCENDING)], unique=True, name="unique_salary_revision"),
            IndexModel([("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("created_at", DESCENDING)], name="salary_revisions_by_employee"),
        ]