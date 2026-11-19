"""Student fee assessment workflow."""

from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.assessment_repository import (
    eligible_students,
    has_duplicate_assessment,
    load_structure_components,
    resolve_active_structure,
)
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase2_enums import FeeAssessmentExceptionCode, FeeAssessmentWorkflowStatus
from app.modules.accounts_finance.phase2_models import (
    StudentFeeAssessmentException,
    StudentFeeAssessmentHistory,
    StudentFeeAssessmentItem,
)
from app.modules.accounts_finance.phase2_schemas import (
    AssessmentItemRead,
    AssessmentPreviewResult,
    AssessmentRead,
    AssessmentScopeFilter,
    AssessmentTransition,
    BulkAssessmentCreate,
    IndividualAssessmentCreate,
)
from app.modules.college_admin.finance_admin_models import StudentFeeAssessment
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.accounts_finance.phase5_enums import ConcessionApplicationStatus, ScholarshipAwardStatus
from app.modules.accounts_finance.phase5_models import StudentFeeConcessionAward, StudentScholarshipAward
from app.modules.finance.finance_models import FeeConcession
from app.modules.accounts_finance.policy import (
    authorize_finance_assessment_approve,
    authorize_finance_assessment_manage,
    authorize_finance_assessment_read,
    require_finance_tenant_scope,
)


async def _append_assessment_history(tenant_id, assessment_id, actor_id, action, from_s, to_s, note=None):
    await StudentFeeAssessmentHistory(
        tenant_id=tenant_id,
        assessment_id=assessment_id,
        action=action,
        from_status=from_s,
        to_status=to_s,
        actor_id=actor_id,
        note=note,
    ).insert()


async def _financial_aid(tenant_id, student_user_id) -> tuple[float, float]:
    concessions = await FeeConcession.find(
        Eq(FeeConcession.tenant_id, tenant_id),
        Eq(FeeConcession.student_user_id, student_user_id),
    ).to_list()
    concession_awards = await StudentFeeConcessionAward.find(
        Eq(StudentFeeConcessionAward.tenant_id, tenant_id),
        Eq(StudentFeeConcessionAward.student_user_id, student_user_id),
    ).to_list()
    concession_total = sum(c.amount for c in concessions if c.published)
    concession_total = max(
        concession_total,
        sum(
            a.approved_amount
            for a in concession_awards
            if a.status in (ConcessionApplicationStatus.ACTIVE, ConcessionApplicationStatus.APPROVED)
        ),
    )
    scholarship_awards = await StudentScholarshipAward.find(
        Eq(StudentScholarshipAward.tenant_id, tenant_id),
        Eq(StudentScholarshipAward.student_user_id, student_user_id),
    ).to_list()
    scholarship_total = sum(
        a.approved_amount for a in scholarship_awards if a.status in (ScholarshipAwardStatus.ACTIVE, ScholarshipAwardStatus.APPROVED)
    )
    return round_money(concession_total), round_money(scholarship_total)


async def _build_assessment_for_student(
    scope: AccessScope,
    tenant_id,
    record: StudentRecord,
    *,
    academic_year_label: str,
    semester_label: str,
    structure_id: str | None,
    optional_codes: list[str],
    waiver_amount: float,
    batch_id: str | None,
    persist: bool,
) -> tuple[StudentFeeAssessment | None, list[StudentFeeAssessmentException]]:
    exceptions: list[StudentFeeAssessmentException] = []
    programme = (record.programme_code or "").upper()
    if not programme:
        exceptions.append(
            StudentFeeAssessmentException(
                tenant_id=tenant_id,
                batch_id=batch_id,
                student_user_id=record.user_id,
                code=FeeAssessmentExceptionCode.MISSING_PROGRAMME,
                message="Student programme missing",
            )
        )
        return None, exceptions

    structure = None
    if structure_id:
        from app.modules.accounts_finance.models import FinanceFeeStructure

        structure = await FinanceFeeStructure.find_one(
            Eq(FinanceFeeStructure.tenant_id, tenant_id),
            Eq(FinanceFeeStructure.structure_id, structure_id),
        )
    else:
        structure = await resolve_active_structure(
            tenant_id,
            programme_code=programme,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
            batch_year=record.batch_label,
        )
    if structure is None:
        exceptions.append(
            StudentFeeAssessmentException(
                tenant_id=tenant_id,
                batch_id=batch_id,
                student_user_id=record.user_id,
                code=FeeAssessmentExceptionCode.NO_STRUCTURE,
                message="No active fee structure",
            )
        )
        return None, exceptions

    if await has_duplicate_assessment(tenant_id, record.user_id, academic_year_label, semester_label, structure.structure_id):
        exceptions.append(
            StudentFeeAssessmentException(
                tenant_id=tenant_id,
                batch_id=batch_id,
                student_user_id=record.user_id,
                code=FeeAssessmentExceptionCode.DUPLICATE,
                message="Duplicate assessment exists",
            )
        )
        return None, exceptions

    components = await load_structure_components(tenant_id, structure.structure_id)
    mandatory_total = 0.0
    optional_total = 0.0
    items: list[StudentFeeAssessmentItem] = []
    for comp in components:
        selected = comp.mandatory or comp.fee_category_code in optional_codes
        if not selected:
            continue
        original = round_money(comp.amount)
        if comp.mandatory:
            mandatory_total += original
        else:
            optional_total += original
        items.append(
            StudentFeeAssessmentItem(
                tenant_id=tenant_id,
                assessment_id="",
                item_id=f"itm_{uuid4().hex[:10]}",
                fee_category_code=comp.fee_category_code,
                description=comp.fee_category_code,
                structure_id=structure.structure_id,
                component_id=comp.component_id,
                original_amount=original,
                net_amount=original,
                mandatory=comp.mandatory,
                optional_selected=not comp.mandatory,
            )
        )

    concession, scholarship = await _financial_aid(tenant_id, record.user_id)
    gross = round_money(mandatory_total + optional_total)
    net = max(0.0, round_money(gross - concession - scholarship - waiver_amount))

    if not persist:
        return None, exceptions

    assessment_id = f"assess_{uuid4().hex[:12]}"
    doc = StudentFeeAssessment(
        tenant_id=tenant_id,
        student_user_id=record.user_id,
        assessment_id=assessment_id,
        structure_id=structure.structure_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        assessed_amount=gross,
        mandatory_amount=mandatory_total,
        optional_amount=optional_total,
        concession_amount=concession,
        scholarship_amount=scholarship,
        waiver_amount=waiver_amount,
        adjustment_amount=0,
        net_amount=net,
        programme_code=programme,
        batch_label=record.batch_label,
        workflow_status=FeeAssessmentWorkflowStatus.DRAFT.value,
        bulk_batch_id=batch_id,
        actor_id=scope.user_id,
        updated_at=utcnow(),
    )
    await doc.insert()
    for item in items:
        item.assessment_id = assessment_id
        await item.insert()
    await _append_assessment_history(
        tenant_id, assessment_id, scope.user_id, "create", None, FeeAssessmentWorkflowStatus.DRAFT.value
    )
    await append_institution_audit(
        tenant_id, actor_id=scope.user_id, action="finance.assessment.create", module="accounts_finance", resource_type="assessment", resource_id=assessment_id
    )
    return doc, exceptions


async def preview_bulk_assessment(scope: AccessScope, payload: AssessmentScopeFilter) -> AssessmentPreviewResult:
    authorize_finance_assessment_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    batch_id = f"batch_{uuid4().hex[:10]}"
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    campus = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    students = await eligible_students(
        tenant_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        programme_code=payload.programme_code,
        department_id=dept,
        batch_label=payload.batch_label,
        campus_id=campus,
    )
    all_exceptions: list[dict] = []
    eligible = 0
    for record in students:
        _, excs = await _build_assessment_for_student(
            scope,
            tenant_id,
            record,
            academic_year_label=payload.academic_year_label,
            semester_label=payload.semester_label,
            structure_id=None,
            optional_codes=[],
            waiver_amount=0,
            batch_id=batch_id,
            persist=False,
        )
        if excs:
            for e in excs:
                all_exceptions.append({"student_user_id": str(e.student_user_id), "code": e.code.value, "message": e.message})
        else:
            eligible += 1
    if all_exceptions:
        for raw in all_exceptions[:200]:
            await StudentFeeAssessmentException(
                tenant_id=tenant_id,
                batch_id=batch_id,
                student_user_id=to_object_id(raw["student_user_id"], "student_user_id"),
                code=FeeAssessmentExceptionCode(raw["code"]),
                message=raw["message"],
            ).insert()
    return AssessmentPreviewResult(
        batch_id=batch_id,
        eligible_count=eligible,
        exception_count=len(all_exceptions),
        exceptions=all_exceptions[:50],
    )


async def create_individual_assessment(scope: AccessScope, payload: IndividualAssessmentCreate) -> AssessmentRead:
    authorize_finance_assessment_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    record = await StudentRecord.find_one(Eq(StudentRecord.tenant_id, tenant_id), Eq(StudentRecord.user_id, student_id))
    if record is None:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    doc, excs = await _build_assessment_for_student(
        scope,
        tenant_id,
        record,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        structure_id=payload.structure_id,
        optional_codes=[c.upper() for c in payload.optional_fee_category_codes],
        waiver_amount=payload.waiver_amount,
        batch_id=None,
        persist=True,
    )
    if doc is None:
        msg = excs[0].message if excs else "Assessment failed"
        raise AppError(code="VALIDATION_ERROR", message=msg, status_code=422)
    return await get_assessment(scope, doc.assessment_id)


async def create_bulk_assessment(scope: AccessScope, payload: BulkAssessmentCreate) -> AssessmentPreviewResult:
    authorize_finance_assessment_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    batch_id = payload.batch_id or f"batch_{uuid4().hex[:10]}"
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    campus = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    students = await eligible_students(
        tenant_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        programme_code=payload.programme_code,
        department_id=dept,
        batch_label=payload.batch_label,
        campus_id=campus,
    )
    created = 0
    exceptions: list[dict] = []
    for record in students:
        doc, excs = await _build_assessment_for_student(
            scope,
            tenant_id,
            record,
            academic_year_label=payload.academic_year_label,
            semester_label=payload.semester_label,
            structure_id=payload.structure_id,
            optional_codes=[c.upper() for c in payload.optional_fee_category_codes],
            waiver_amount=0,
            batch_id=batch_id,
            persist=True,
        )
        if doc:
            created += 1
        for e in excs:
            await e.insert()
            exceptions.append({"student_user_id": str(e.student_user_id), "code": e.code.value, "message": e.message})
    return AssessmentPreviewResult(batch_id=batch_id, eligible_count=created, exception_count=len(exceptions), exceptions=exceptions[:50])


async def get_assessment(scope: AccessScope, assessment_id: str) -> AssessmentRead:
    authorize_finance_assessment_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await StudentFeeAssessment.find_one(
        Eq(StudentFeeAssessment.tenant_id, tenant_id),
        Eq(StudentFeeAssessment.assessment_id, assessment_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Assessment not found", status_code=404)
    items = await StudentFeeAssessmentItem.find(
        Eq(StudentFeeAssessmentItem.tenant_id, tenant_id),
        Eq(StudentFeeAssessmentItem.assessment_id, assessment_id),
    ).to_list()
    return AssessmentRead(
        assessment_id=doc.assessment_id,
        student_user_id=str(doc.student_user_id),
        structure_id=doc.structure_id,
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        workflow_status=doc.workflow_status,
        assessed_amount=doc.assessed_amount,
        mandatory_amount=doc.mandatory_amount,
        optional_amount=doc.optional_amount,
        scholarship_amount=doc.scholarship_amount,
        concession_amount=doc.concession_amount,
        waiver_amount=doc.waiver_amount,
        adjustment_amount=doc.adjustment_amount,
        net_amount=doc.net_amount,
        invoice_id=doc.invoice_id,
        items=[
            AssessmentItemRead(
                item_id=i.item_id,
                fee_category_code=i.fee_category_code,
                description=i.description,
                original_amount=i.original_amount,
                adjustment_amount=i.adjustment_amount,
                net_amount=i.net_amount,
                mandatory=i.mandatory,
                optional_selected=i.optional_selected,
            )
            for i in items
        ],
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def list_assessments(
    scope: AccessScope,
    pagination: Pagination,
    *,
    workflow_status: str | None = None,
    academic_year_label: str | None = None,
) -> Page[AssessmentRead]:
    authorize_finance_assessment_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query = StudentFeeAssessment.find(Eq(StudentFeeAssessment.tenant_id, tenant_id))
    if workflow_status:
        query = query.find(Eq(StudentFeeAssessment.workflow_status, workflow_status))
    if academic_year_label:
        query = query.find(Eq(StudentFeeAssessment.academic_year_label, academic_year_label))
    total = await query.count()
    docs = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    items = [await get_assessment(scope, d.assessment_id) for d in docs]
    return Page(items=items, total=total, offset=pagination.offset, limit=pagination.limit)


_TRANSITIONS = {
    ("draft", "submit"): FeeAssessmentWorkflowStatus.IN_REVIEW,
    ("in_review", "approve"): FeeAssessmentWorkflowStatus.APPROVED,
    ("in_review", "return"): FeeAssessmentWorkflowStatus.RETURNED,
    ("returned", "submit"): FeeAssessmentWorkflowStatus.IN_REVIEW,
    ("draft", "cancel"): FeeAssessmentWorkflowStatus.CANCELLED,
    ("in_review", "cancel"): FeeAssessmentWorkflowStatus.CANCELLED,
    ("approved", "cancel"): FeeAssessmentWorkflowStatus.CANCELLED,
}


async def transition_assessment(scope: AccessScope, assessment_id: str, payload: AssessmentTransition) -> AssessmentRead:
    tenant_id = require_finance_tenant_scope(scope)
    doc = await StudentFeeAssessment.find_one(
        Eq(StudentFeeAssessment.tenant_id, tenant_id),
        Eq(StudentFeeAssessment.assessment_id, assessment_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Assessment not found", status_code=404)
    if payload.action in ("submit", "cancel") or payload.action == "return":
        authorize_finance_assessment_manage(scope)
    else:
        authorize_finance_assessment_approve(scope)
    if doc.invoice_id and payload.action == "cancel":
        raise AppError(code="CONFLICT", message="Cannot cancel assessment after invoice posted", status_code=409)
    key = (doc.workflow_status, payload.action)
    new_status = _TRANSITIONS.get(key)
    if new_status is None:
        raise AppError(code="VALIDATION_ERROR", message="Invalid assessment transition", status_code=422)
    old = doc.workflow_status
    doc.workflow_status = new_status.value
    if new_status == FeeAssessmentWorkflowStatus.APPROVED:
        doc.approved_by = scope.user_id
        doc.approved_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await _append_assessment_history(tenant_id, assessment_id, scope.user_id, payload.action, old, new_status.value, payload.note)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action=f"finance.assessment.{payload.action}",
        module="accounts_finance",
        resource_type="assessment",
        resource_id=assessment_id,
    )
    return await get_assessment(scope, assessment_id)