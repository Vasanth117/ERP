"""Salary structure API schemas."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrSalaryAssignmentStatus, HrSalaryCalcType, HrSalaryComponentCategory, HrSalaryRevisionStatus, HrSalaryTemplateStatus
from app.modules.hr.salary_structure_models import HrEmployeeSalaryAssignment, HrSalaryComponent, HrSalaryTemplate


class SalaryComponentUpsert(BaseModel):
    component_code: str
    name: str
    category: HrSalaryComponentCategory
    calc_type: HrSalaryCalcType = HrSalaryCalcType.FIXED
    calculation_basis: str | None = None
    percentage_of: str | None = None
    employee_categories: list[str] = Field(default_factory=list)
    proration_rule: str | None = None
    statutory_ref: str | None = None
    tax_classification_ref: str | None = None
    effective_from: date


class SalaryComponentRead(BaseModel):
    id: str
    component_code: str
    name: str
    category: HrSalaryComponentCategory

    @classmethod
    def from_document(cls, doc: HrSalaryComponent) -> "SalaryComponentRead":
        return cls(id=str(doc.id), component_code=doc.component_code, name=doc.name, category=doc.category)


class SalaryTemplateUpsert(BaseModel):
    template_code: str
    title: str
    template_kind: str
    component_lines: list[dict[str, Any]]


class SalaryTemplateRead(BaseModel):
    id: str
    template_code: str
    title: str
    version: int
    status: HrSalaryTemplateStatus

    @classmethod
    def from_document(cls, doc: HrSalaryTemplate) -> "SalaryTemplateRead":
        return cls(id=str(doc.id), template_code=doc.template_code, title=doc.title, version=doc.version, status=doc.status)


class SalaryAssignmentCreate(BaseModel):
    employee_user_id: str
    template_id: str
    component_amounts: dict[str, str]
    effective_from: date


class SalaryAssignmentRead(BaseModel):
    id: str
    employee_user_id: str
    status: HrSalaryAssignmentStatus
    gross_salary: str
    net_salary: str
    effective_from: date

    @classmethod
    def from_document(cls, doc: HrEmployeeSalaryAssignment) -> "SalaryAssignmentRead":
        return cls(
            id=str(doc.id),
            employee_user_id=str(doc.employee_user_id),
            status=doc.status,
            gross_salary=doc.gross_salary,
            net_salary=doc.net_salary,
            effective_from=doc.effective_from,
        )


class SalaryRevisionCreate(BaseModel):
    employee_user_id: str
    revision_type: str
    reason: str = Field(min_length=1, max_length=2000)
    proposed_component_amounts: dict[str, str]
    effective_from: date
    template_id: str | None = None


class SalaryRevisionReview(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    note: str | None = None


class SalaryRevisionRead(BaseModel):
    id: str
    revision_code: str
    status: HrSalaryRevisionStatus

    @classmethod
    def from_document(cls, doc) -> "SalaryRevisionRead":
        return cls(id=str(doc.id), revision_code=doc.revision_code, status=doc.status)