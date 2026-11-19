"""Salary components, templates, assignments and revisions."""

from datetime import date, timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.employee_sync import log_hr_activity
from app.modules.hr.enums import HrSalaryAssignmentStatus, HrSalaryRevisionStatus, HrSalaryTemplateStatus, HrStaffActivityType
from app.modules.hr.policy import authorize_hr_salary_manage, authorize_hr_salary_read, require_hr_tenant_scope
from app.modules.hr.salary_calculation import calculate_structure, diff_amounts
from app.modules.hr.salary_structure_models import (
    HrEmployeeSalaryAssignment,
    HrEmployeeSalaryRevisionHistory,
    HrSalaryComponent,
    HrSalaryTemplate,
)
from app.modules.hr.salary_structure_schemas import (
    SalaryAssignmentCreate,
    SalaryAssignmentRead,
    SalaryComponentRead,
    SalaryComponentUpsert,
    SalaryRevisionCreate,
    SalaryRevisionRead,
    SalaryRevisionReview,
    SalaryTemplateRead,
    SalaryTemplateUpsert,
)


async def upsert_salary_component(scope: AccessScope, payload: SalaryComponentUpsert) -> SalaryComponentRead:
    authorize_hr_salary_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrSalaryComponent.find_one(
        Eq(HrSalaryComponent.tenant_id, tenant_id),
        Eq(HrSalaryComponent.component_code, payload.component_code),
    )
    if doc:
        doc.name = payload.name
        doc.category = payload.category
        doc.calc_type = payload.calc_type
        doc.calculation_basis = payload.calculation_basis
        doc.percentage_of = payload.percentage_of
        doc.employee_categories = payload.employee_categories
        doc.proration_rule = payload.proration_rule
        doc.statutory_ref = payload.statutory_ref
        doc.tax_classification_ref = payload.tax_classification_ref
        doc.effective_from = payload.effective_from
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrSalaryComponent(
            tenant_id=tenant_id,
            component_code=payload.component_code,
            name=payload.name,
            category=payload.category,
            calc_type=payload.calc_type,
            calculation_basis=payload.calculation_basis,
            percentage_of=payload.percentage_of,
            employee_categories=payload.employee_categories,
            proration_rule=payload.proration_rule,
            statutory_ref=payload.statutory_ref,
            tax_classification_ref=payload.tax_classification_ref,
            effective_from=payload.effective_from,
            actor_id=scope.user_id,
        )
        await doc.insert()
    return SalaryComponentRead.from_document(doc)


async def list_salary_components(scope: AccessScope) -> list[SalaryComponentRead]:
    authorize_hr_salary_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrSalaryComponent.find(Eq(HrSalaryComponent.tenant_id, tenant_id), Eq(HrSalaryComponent.is_active, True)).to_list()
    return [SalaryComponentRead.from_document(r) for r in rows]


async def upsert_salary_template(scope: AccessScope, payload: SalaryTemplateUpsert, *, duplicate: bool = False) -> SalaryTemplateRead:
    authorize_hr_salary_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    existing = await HrSalaryTemplate.find(
        Eq(HrSalaryTemplate.tenant_id, tenant_id),
        Eq(HrSalaryTemplate.template_code, payload.template_code),
    ).sort(-HrSalaryTemplate.version).limit(1).to_list()
    base = existing[0] if existing else None
    version = (base.version + 1) if base else 1
    if base and not duplicate:
        base.status = HrSalaryTemplateStatus.INACTIVE
        base.updated_at = utcnow()
        await base.save()
    row = HrSalaryTemplate(
        tenant_id=tenant_id,
        template_code=payload.template_code,
        title=payload.title,
        template_kind=payload.template_kind,
        component_lines=payload.component_lines,
        version=version,
        duplicated_from_version=base.version if duplicate and base else None,
        actor_id=scope.user_id,
    )
    await row.insert()
    return SalaryTemplateRead.from_document(row)


async def list_salary_templates(scope: AccessScope) -> list[SalaryTemplateRead]:
    authorize_hr_salary_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrSalaryTemplate.find(Eq(HrSalaryTemplate.tenant_id, tenant_id), Eq(HrSalaryTemplate.status, HrSalaryTemplateStatus.ACTIVE)).to_list()
    return [SalaryTemplateRead.from_document(r) for r in rows]


async def create_salary_assignment(scope: AccessScope, payload: SalaryAssignmentCreate) -> SalaryAssignmentRead:
    authorize_hr_salary_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, uid))
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    template = await HrSalaryTemplate.get(to_object_id(payload.template_id, "template_id"))
    if template is None or template.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Salary template not found", status_code=404)
    calc = calculate_structure(component_defs=template.component_lines, amounts=payload.component_amounts)
    assignment = HrEmployeeSalaryAssignment(
        tenant_id=tenant_id,
        employee_user_id=uid,
        template_id=template.id,
        template_version=template.version,
        component_amounts=calc["computed_amounts"],
        earnings_total=calc["earnings_total"],
        deductions_total=calc["deductions_total"],
        gross_salary=calc["gross_salary"],
        net_salary=calc["net_salary"],
        employer_contributions_total=calc["employer_contributions_total"],
        annual_compensation=calc["annual_compensation"],
        ctc=calc["ctc"],
        effective_from=payload.effective_from,
        status=HrSalaryAssignmentStatus.DRAFT,
        actor_id=scope.user_id,
    )
    await assignment.insert()
    return SalaryAssignmentRead.from_document(assignment)


async def submit_salary_assignment(scope: AccessScope, assignment_id: str) -> SalaryAssignmentRead:
    authorize_hr_salary_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    row = await HrEmployeeSalaryAssignment.get(to_object_id(assignment_id, "assignment_id"))
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    row.status = HrSalaryAssignmentStatus.PENDING_APPROVAL
    row.updated_at = utcnow()
    await row.save()
    return SalaryAssignmentRead.from_document(row)


async def activate_salary_assignment(scope: AccessScope, assignment_id: str) -> SalaryAssignmentRead:
    authorize_hr_salary_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    row = await HrEmployeeSalaryAssignment.get(to_object_id(assignment_id, "assignment_id"))
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    if row.status != HrSalaryAssignmentStatus.PENDING_APPROVAL:
        raise AppError(code="CONFLICT", message="Assignment is not pending approval", status_code=409)
    active = await HrEmployeeSalaryAssignment.find_one(
        Eq(HrEmployeeSalaryAssignment.tenant_id, tenant_id),
        Eq(HrEmployeeSalaryAssignment.employee_user_id, row.employee_user_id),
        Eq(HrEmployeeSalaryAssignment.status, HrSalaryAssignmentStatus.ACTIVE),
    )
    if active:
        active.status = HrSalaryAssignmentStatus.SUPERSEDED
        active.effective_to = row.effective_from - timedelta(days=1) if row.effective_from else None
        active.updated_at = utcnow()
        await active.save()
    row.status = HrSalaryAssignmentStatus.ACTIVE
    row.approved_by = scope.user_id
    row.approved_at = utcnow()
    row.updated_at = utcnow()
    await row.save()
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, row.employee_user_id))
    if employee:
        confidential = dict(employee.confidential_hr or {})
        confidential["salary_structure"] = {
            "assignment_id": str(row.id),
            "gross_salary": row.gross_salary,
            "net_salary": row.net_salary,
            "effective_from": row.effective_from.isoformat(),
        }
        employee.confidential_hr = confidential
        employee.updated_at = utcnow()
        await employee.save()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.PAYROLL_ACTIVITY,
        "Salary assignment activated",
        actor_id=scope.user_id,
        employee_user_id=row.employee_user_id,
        resource_type="employee_salary_assignment",
        resource_id=str(row.id),
    )
    return SalaryAssignmentRead.from_document(row)


async def create_salary_revision(scope: AccessScope, payload: SalaryRevisionCreate) -> SalaryRevisionRead:
    authorize_hr_salary_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    current = await HrEmployeeSalaryAssignment.find_one(
        Eq(HrEmployeeSalaryAssignment.tenant_id, tenant_id),
        Eq(HrEmployeeSalaryAssignment.employee_user_id, uid),
        Eq(HrEmployeeSalaryAssignment.status, HrSalaryAssignmentStatus.ACTIVE),
    )
    before = current.component_amounts if current else {}
    diff = diff_amounts(before, payload.proposed_component_amounts)
    code = f"SREV-{uuid4().hex[:10].upper()}"
    row = HrEmployeeSalaryRevisionHistory(
        tenant_id=tenant_id,
        employee_user_id=uid,
        revision_code=code,
        reason=payload.reason,
        revision_type=payload.revision_type,
        current_assignment_id=current.id if current else None,
        template_id=to_object_id(payload.template_id, "template_id") if payload.template_id else (current.template_id if current else None),
        proposed_component_amounts=payload.proposed_component_amounts,
        difference_summary=diff,
        effective_from=payload.effective_from,
        status=HrSalaryRevisionStatus.PENDING_APPROVAL,
        actor_id=scope.user_id,
    )
    await row.insert()
    return SalaryRevisionRead.from_document(row)


async def review_salary_revision(scope: AccessScope, revision_id: str, payload: SalaryRevisionReview) -> SalaryRevisionRead:
    authorize_hr_salary_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    row = await HrEmployeeSalaryRevisionHistory.get(to_object_id(revision_id, "revision_id"))
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Revision not found", status_code=404)
    if payload.decision == "reject":
        row.status = HrSalaryRevisionStatus.REJECTED
        row.updated_at = utcnow()
        await row.save()
        return SalaryRevisionRead.from_document(row)
    if row.status != HrSalaryRevisionStatus.PENDING_APPROVAL:
        raise AppError(code="CONFLICT", message="Revision is not pending approval", status_code=409)
    template_id = row.template_id
    template_version = 1
    component_lines: list = []
    if row.current_assignment_id:
        current = await HrEmployeeSalaryAssignment.get(row.current_assignment_id)
        if current:
            template_version = current.template_version
    if template_id:
        template = await HrSalaryTemplate.get(template_id)
        if template:
            template_version = template.version
            component_lines = template.component_lines
    if not template_id or not component_lines:
        raise AppError(code="VALIDATION_ERROR", message="Salary template required for revision", status_code=422)
    calc = calculate_structure(component_defs=component_lines, amounts=row.proposed_component_amounts)
    assignment = HrEmployeeSalaryAssignment(
        tenant_id=tenant_id,
        employee_user_id=row.employee_user_id,
        template_id=template_id,
        template_version=template_version,
        component_amounts=calc["computed_amounts"],
        earnings_total=calc["earnings_total"],
        deductions_total=calc["deductions_total"],
        gross_salary=calc["gross_salary"],
        net_salary=calc["net_salary"],
        employer_contributions_total=calc["employer_contributions_total"],
        annual_compensation=calc["annual_compensation"],
        ctc=calc["ctc"],
        effective_from=row.effective_from,
        status=HrSalaryAssignmentStatus.PENDING_APPROVAL,
        actor_id=scope.user_id,
    )
    await assignment.insert()
    activated = await activate_salary_assignment(scope, str(assignment.id))
    row.status = HrSalaryRevisionStatus.APPLIED
    row.approved_by = scope.user_id
    row.approved_at = utcnow()
    row.resulting_assignment_id = to_object_id(activated.id, "assignment_id")
    row.updated_at = utcnow()
    await row.save()
    return SalaryRevisionRead.from_document(row)