"""Fee structure lifecycle and revisions."""

from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.enums import FeeStructureApprovalAction, FeeStructureLifecycleStatus, RefundabilityClass
from app.modules.accounts_finance.fee_structure_repository import find_conflicting_active_structure, validate_effective_period
from app.modules.accounts_finance.models import (
    FinanceFeeCategory,
    FinanceFeeStructure,
    FinanceFeeStructureApprovalHistory,
    FinanceFeeStructureComponent,
    FinanceFeeStructureVersion,
)
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.policy import (
    authorize_finance_structure_approve,
    authorize_finance_structure_manage,
    authorize_finance_structure_read,
    require_finance_tenant_scope,
)
from app.modules.accounts_finance.schemas import (
    FeeStructureCreate,
    FeeStructureRead,
    FeeStructureRevision,
    FeeStructureTransition,
)
from app.modules.accounts_finance.structure_sync import sync_active_structure_to_authoritative
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.finance_admin_models import StudentFeeAssessment
from app.modules.college_admin.security_admin_service import append_institution_audit


async def _validate_academic_refs(tenant_id, academic_year_label: str, programme_code: str) -> None:
    year = await AcademicYear.find_one(
        Eq(AcademicYear.tenant_id, tenant_id),
        Eq(AcademicYear.label, academic_year_label),
    )
    if year is None:
        year = await AcademicYear.find_one(
            Eq(AcademicYear.tenant_id, tenant_id),
            Eq(AcademicYear.year_code, academic_year_label),
        )
    if year is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown academic year reference", status_code=422)
    programme = await AcademicProgramme.find_one(
        Eq(AcademicProgramme.tenant_id, tenant_id),
        Eq(AcademicProgramme.programme_code, programme_code.upper()),
    )
    if programme is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown programme reference", status_code=422)


async def _validate_categories(tenant_id, components: list) -> None:
    for comp in components:
        cat = await FinanceFeeCategory.find_one(
            Eq(FinanceFeeCategory.tenant_id, tenant_id),
            Eq(FinanceFeeCategory.fee_code, comp.fee_category_code.strip().upper()),
        )
        if cat is None:
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Unknown fee category {comp.fee_category_code}",
                status_code=422,
            )
        if not cat.active:
            raise AppError(code="VALIDATION_ERROR", message=f"Fee category {cat.fee_code} is inactive", status_code=422)


async def _persist_components(tenant_id, structure_id: str, components: list) -> tuple[list[FinanceFeeStructureComponent], float]:
    await FinanceFeeStructureComponent.find(
        Eq(FinanceFeeStructureComponent.tenant_id, tenant_id),
        Eq(FinanceFeeStructureComponent.structure_id, structure_id),
    ).delete()
    total = 0.0
    saved: list[FinanceFeeStructureComponent] = []
    for comp in components:
        cid = comp.component_id or f"cmp_{uuid4().hex[:12]}"
        code = comp.fee_category_code.strip().upper()
        amount = round_money(comp.amount)
        total += amount
        doc = FinanceFeeStructureComponent(
            tenant_id=tenant_id,
            component_id=cid,
            structure_id=structure_id,
            fee_category_code=code,
            amount=amount,
            due_date=comp.due_date,
            billing_frequency=comp.billing_frequency,
            student_group=comp.student_group,
            mandatory=comp.mandatory,
            optional_flag=comp.optional_flag,
            refundability=comp.refundability or RefundabilityClass.NON_REFUNDABLE,
            installment_eligible=comp.installment_eligible,
            effective_from=comp.effective_from,
            effective_to=comp.effective_to,
        )
        await doc.insert()
        saved.append(doc)
    return saved, round_money(total)


async def _append_approval_history(
    tenant_id,
    structure_id: str,
    actor_id,
    action: str,
    from_status: str | None,
    to_status: str | None,
    note: str | None = None,
) -> None:
    await FinanceFeeStructureApprovalHistory(
        tenant_id=tenant_id,
        structure_id=structure_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
        note=note,
    ).insert()


async def create_fee_structure(scope: AccessScope, payload: FeeStructureCreate) -> FeeStructureRead:
    authorize_finance_structure_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    sid = payload.structure_id.strip()
    if await FinanceFeeStructure.find_one(Eq(FinanceFeeStructure.tenant_id, tenant_id), Eq(FinanceFeeStructure.structure_id, sid)):
        raise AppError(code="CONFLICT", message="structure_id already exists", status_code=409)
    validate_effective_period(payload.effective_from, payload.effective_to)
    programme = payload.programme_code.upper()
    await _validate_academic_refs(tenant_id, payload.academic_year_label, programme)
    await _validate_categories(tenant_id, payload.components)
    conflict = await find_conflicting_active_structure(
        tenant_id,
        programme_code=programme,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
    )
    if conflict:
        raise AppError(
            code="CONFLICT",
            message="An active or approved structure exists for this programme/year/semester",
            status_code=409,
        )
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    campus = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    doc = FinanceFeeStructure(
        tenant_id=tenant_id,
        structure_id=sid,
        template_key=payload.template_key,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        programme_code=programme,
        department_id=dept,
        batch_year=payload.batch_year,
        student_category=payload.student_category,
        campus_id=campus,
        admission_type=payload.admission_type,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        installment_eligible=payload.installment_eligible,
        created_by=scope.user_id,
    )
    await doc.insert()
    components, total = await _persist_components(tenant_id, sid, payload.components)
    doc.total_amount = total
    await doc.save()
    await _append_approval_history(
        tenant_id, sid, scope.user_id, "create", None, doc.status.value, note="Created fee structure"
    )
    await append_institution_audit(
        tenant_id, actor_id=scope.user_id, action="finance.structure.create", module="accounts_finance", resource_type="fee_structure", resource_id=sid
    )
    return FeeStructureRead.from_parts(doc, components)


async def get_fee_structure(scope: AccessScope, structure_id: str) -> FeeStructureRead:
    authorize_finance_structure_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await FinanceFeeStructure.find_one(
        Eq(FinanceFeeStructure.tenant_id, tenant_id),
        Eq(FinanceFeeStructure.structure_id, structure_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Fee structure not found", status_code=404)
    components = await FinanceFeeStructureComponent.find(
        Eq(FinanceFeeStructureComponent.tenant_id, tenant_id),
        Eq(FinanceFeeStructureComponent.structure_id, structure_id),
    ).to_list()
    return FeeStructureRead.from_parts(doc, components)


async def list_fee_structures(
    scope: AccessScope,
    pagination: Pagination,
    *,
    status: FeeStructureLifecycleStatus | None = None,
    programme_code: str | None = None,
) -> Page[FeeStructureRead]:
    authorize_finance_structure_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query = FinanceFeeStructure.find(Eq(FinanceFeeStructure.tenant_id, tenant_id))
    if status:
        query = query.find(Eq(FinanceFeeStructure.status, status))
    if programme_code:
        query = query.find(Eq(FinanceFeeStructure.programme_code, programme_code.upper()))
    total = await query.count()
    docs = await query.sort("-updated_at").skip(pagination.offset).limit(pagination.limit).to_list()
    items: list[FeeStructureRead] = []
    for doc in docs:
        components = await FinanceFeeStructureComponent.find(
            Eq(FinanceFeeStructureComponent.tenant_id, tenant_id),
            Eq(FinanceFeeStructureComponent.structure_id, doc.structure_id),
        ).to_list()
        items.append(FeeStructureRead.from_parts(doc, components))
    return Page(items=items, total=total, offset=pagination.offset, limit=pagination.limit)


_TRANSITIONS: dict[tuple[FeeStructureLifecycleStatus, FeeStructureApprovalAction], FeeStructureLifecycleStatus] = {
    (FeeStructureLifecycleStatus.DRAFT, FeeStructureApprovalAction.SUBMIT): FeeStructureLifecycleStatus.SUBMITTED,
    (FeeStructureLifecycleStatus.SUBMITTED, FeeStructureApprovalAction.APPROVE): FeeStructureLifecycleStatus.APPROVED,
    (FeeStructureLifecycleStatus.SUBMITTED, FeeStructureApprovalAction.REJECT): FeeStructureLifecycleStatus.DRAFT,
    (FeeStructureLifecycleStatus.APPROVED, FeeStructureApprovalAction.SCHEDULE): FeeStructureLifecycleStatus.SCHEDULED,
    (FeeStructureLifecycleStatus.APPROVED, FeeStructureApprovalAction.ACTIVATE): FeeStructureLifecycleStatus.ACTIVE,
    (FeeStructureLifecycleStatus.SCHEDULED, FeeStructureApprovalAction.ACTIVATE): FeeStructureLifecycleStatus.ACTIVE,
    (FeeStructureLifecycleStatus.ACTIVE, FeeStructureApprovalAction.SUSPEND): FeeStructureLifecycleStatus.SUSPENDED,
    (FeeStructureLifecycleStatus.SUSPENDED, FeeStructureApprovalAction.ACTIVATE): FeeStructureLifecycleStatus.ACTIVE,
    (FeeStructureLifecycleStatus.ACTIVE, FeeStructureApprovalAction.SUPERSEDE): FeeStructureLifecycleStatus.SUPERSEDED,
    (FeeStructureLifecycleStatus.ACTIVE, FeeStructureApprovalAction.EXPIRE): FeeStructureLifecycleStatus.EXPIRED,
    (FeeStructureLifecycleStatus.EXPIRED, FeeStructureApprovalAction.ARCHIVE): FeeStructureLifecycleStatus.ARCHIVED,
    (FeeStructureLifecycleStatus.SUPERSEDED, FeeStructureApprovalAction.ARCHIVE): FeeStructureLifecycleStatus.ARCHIVED,
}


async def transition_fee_structure(scope: AccessScope, structure_id: str, payload: FeeStructureTransition) -> FeeStructureRead:
    tenant_id = require_finance_tenant_scope(scope)
    doc = await FinanceFeeStructure.find_one(
        Eq(FinanceFeeStructure.tenant_id, tenant_id),
        Eq(FinanceFeeStructure.structure_id, structure_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Fee structure not found", status_code=404)
    action = payload.action
    if action in (FeeStructureApprovalAction.SUBMIT, FeeStructureApprovalAction.REVISION_REQUEST):
        authorize_finance_structure_manage(scope)
    else:
        authorize_finance_structure_approve(scope)
    key = (doc.status, action)
    new_status = _TRANSITIONS.get(key)
    if new_status is None:
        raise AppError(code="VALIDATION_ERROR", message="Invalid lifecycle transition", status_code=422)
    old = doc.status
    doc.status = new_status
    doc.updated_at = utcnow()
    if action == FeeStructureApprovalAction.APPROVE:
        doc.approved_by = scope.user_id
        doc.approved_at = utcnow()
    if new_status == FeeStructureLifecycleStatus.ACTIVE:
        conflict = await find_conflicting_active_structure(
            tenant_id,
            programme_code=doc.programme_code,
            academic_year_label=doc.academic_year_label,
            semester_label=doc.semester_label,
            exclude_structure_id=structure_id,
        )
        if conflict:
            raise AppError(code="CONFLICT", message="Another active structure exists for scope", status_code=409)
        await sync_active_structure_to_authoritative(tenant_id, doc)
    await doc.save()
    await _append_approval_history(
        tenant_id,
        structure_id,
        scope.user_id,
        action.value,
        old.value,
        new_status.value,
        note=payload.note,
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action=f"finance.structure.{action.value}",
        module="accounts_finance",
        resource_type="fee_structure",
        resource_id=structure_id,
    )
    return await get_fee_structure(scope, structure_id)


async def revise_fee_structure(scope: AccessScope, structure_id: str, payload: FeeStructureRevision) -> FeeStructureRead:
    authorize_finance_structure_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await FinanceFeeStructure.find_one(
        Eq(FinanceFeeStructure.tenant_id, tenant_id),
        Eq(FinanceFeeStructure.structure_id, structure_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Fee structure not found", status_code=404)
    prior_status = doc.status
    if doc.status in (FeeStructureLifecycleStatus.ACTIVE, FeeStructureLifecycleStatus.SUPERSEDED, FeeStructureLifecycleStatus.ARCHIVED):
        assessed = await StudentFeeAssessment.find_one(
            Eq(StudentFeeAssessment.tenant_id, tenant_id),
            Eq(StudentFeeAssessment.structure_id, structure_id),
        )
        if assessed:
            raise AppError(
                code="CONFLICT",
                message="Cannot revise amounts for structures with posted assessments",
                status_code=409,
            )
    validate_effective_period(payload.effective_from or doc.effective_from, payload.effective_to or doc.effective_to)
    await _validate_categories(tenant_id, payload.components)
    old_components = await FinanceFeeStructureComponent.find(
        Eq(FinanceFeeStructureComponent.tenant_id, tenant_id),
        Eq(FinanceFeeStructureComponent.structure_id, structure_id),
    ).to_list()
    previous_snapshot = {
        "total_amount": doc.total_amount,
        "components": [{"component_id": c.component_id, "amount": c.amount} for c in old_components],
        "effective_from": doc.effective_from.isoformat() if doc.effective_from else None,
        "effective_to": doc.effective_to.isoformat() if doc.effective_to else None,
    }
    components, total = await _persist_components(tenant_id, structure_id, payload.components)
    if payload.installment_eligible is not None:
        doc.installment_eligible = payload.installment_eligible
    if payload.effective_from:
        doc.effective_from = payload.effective_from
    if payload.effective_to:
        doc.effective_to = payload.effective_to
    doc.total_amount = total
    doc.version += 1
    if doc.status == FeeStructureLifecycleStatus.APPROVED:
        doc.status = FeeStructureLifecycleStatus.DRAFT
    doc.updated_at = utcnow()
    new_snapshot = {
        "total_amount": total,
        "components": [{"component_id": c.component_id, "amount": c.amount} for c in components],
        "effective_from": doc.effective_from.isoformat() if doc.effective_from else None,
        "effective_to": doc.effective_to.isoformat() if doc.effective_to else None,
    }
    await FinanceFeeStructureVersion(
        tenant_id=tenant_id,
        structure_id=structure_id,
        version=doc.version,
        reason=payload.reason,
        effective_date=payload.effective_date,
        requested_by=scope.user_id,
        previous_snapshot=previous_snapshot,
        new_snapshot=new_snapshot,
    ).insert()
    await doc.save()
    await _append_approval_history(
        tenant_id, structure_id, scope.user_id, "revision", prior_status.value, doc.status.value, note=payload.reason
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.structure.revise",
        module="accounts_finance",
        resource_type="fee_structure",
        resource_id=structure_id,
    )
    return FeeStructureRead.from_parts(doc, components)