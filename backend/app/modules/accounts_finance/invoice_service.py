"""Invoice and demand management."""

from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq
from pymongo import ReturnDocument

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.config import get_settings
from app.core.database import get_database_client
from app.core.exceptions import AppError
from app.modules.accounts_finance.finance_notify import enqueue_invoice_issued
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase2_enums import FeeAssessmentWorkflowStatus, InvoiceAdjustmentType, StudentInvoiceStatus
from app.modules.accounts_finance.phase2_models import (
    InvoiceAdjustmentHistory,
    StudentCreditNote,
    StudentDebitNote,
    StudentFeeAssessmentItem,
    StudentInvoiceHistory,
    StudentInvoiceItem,
)
from app.modules.accounts_finance.phase2_schemas import (
    InvoiceAdjustmentRequest,
    InvoiceGeneratePreview,
    InvoiceGenerateScope,
    InvoiceItemRead,
    InvoiceRead,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_invoice_issue,
    authorize_finance_invoice_manage,
    authorize_finance_invoice_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.finance_admin_models import StudentFeeAssessment
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand, StudentFeeInvoice
from app.modules.students.models import StudentProfile


async def _next_invoice_number(tenant_id, fiscal_year: str) -> str:
    client = get_database_client()
    db = client[get_settings().mongodb_db_name]
    coll = db["finance_invoice_sequences"]
    result = await coll.find_one_and_update(
        {"tenant_id": tenant_id, "fiscal_year": fiscal_year},
        {"$inc": {"last_value": 1}, "$set": {"updated_at": utcnow()}, "$setOnInsert": {"prefix": "INV"}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    seq = result.get("last_value", 1)
    prefix = result.get("prefix", "INV")
    return f"{prefix}-{fiscal_year}-{seq:06d}"


async def _sync_invoice_payment_status(tenant_id, invoice: StudentFeeInvoice) -> str:
    if invoice.invoice_status in (StudentInvoiceStatus.CANCELLED.value, StudentInvoiceStatus.DRAFT.value):
        return invoice.invoice_status
    if not invoice.demand_id:
        return invoice.invoice_status
    demand = await StudentFeeDemand.find_one(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        Eq(StudentFeeDemand.demand_id, invoice.demand_id),
    )
    if demand is None:
        return invoice.invoice_status
    if demand.status == FeeDemandStatus.PAID:
        return StudentInvoiceStatus.PAID.value
    if demand.status == FeeDemandStatus.PARTIALLY_PAID:
        return StudentInvoiceStatus.PARTIALLY_PAID.value
    if demand.status == FeeDemandStatus.OVERDUE:
        return StudentInvoiceStatus.OVERDUE.value
    txs = await PaymentTransaction.find(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.student_user_id, invoice.student_user_id),
        Eq(PaymentTransaction.demand_id, invoice.demand_id),
    ).to_list()
    verified_paid = sum(t.amount for t in txs if t.status == PaymentTransactionStatus.SUCCESS and (t.payment_mode == "offline" or t.webhook_verified))
    pending = any(t.status in (PaymentTransactionStatus.PENDING, PaymentTransactionStatus.INITIATED) for t in txs)
    if verified_paid >= invoice.amount:
        return StudentInvoiceStatus.PAID.value
    if verified_paid > 0:
        return StudentInvoiceStatus.PARTIALLY_PAID.value
    if pending:
        return StudentInvoiceStatus.UNDER_RECONCILIATION.value
    return invoice.invoice_status


def _invoice_to_read(invoice: StudentFeeInvoice, items: list[StudentInvoiceItem], payment_status: str | None) -> InvoiceRead:
    return InvoiceRead(
        invoice_id=invoice.invoice_id,
        invoice_number=invoice.invoice_number,
        student_user_id=str(invoice.student_user_id),
        assessment_id=invoice.assessment_id,
        academic_year_label=invoice.academic_year_label,
        semester_label=invoice.semester_label,
        original_amount=invoice.original_amount,
        amount=invoice.amount,
        invoice_status=invoice.invoice_status,
        billing_date=invoice.billing_date,
        due_date=invoice.due_date,
        issued_at=invoice.issued_at,
        published=invoice.published,
        items=[
            InvoiceItemRead(
                item_id=i.item_id,
                fee_category_code=i.fee_category_code,
                description=i.description,
                original_amount=i.original_amount,
                adjustment_amount=i.adjustment_amount,
                net_amount=i.net_amount,
            )
            for i in items
        ],
        payment_status_synced=payment_status,
    )


async def preview_invoice_generation(scope: AccessScope, payload: InvoiceGenerateScope) -> InvoiceGeneratePreview:
    authorize_finance_invoice_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    assessments = await _approved_assessments_for_scope(tenant_id, payload)
    would_create = sum(1 for a in assessments if not a.invoice_id)
    duplicate_blocked = len(assessments) - would_create
    return InvoiceGeneratePreview(eligible_assessments=len(assessments), would_create=would_create, duplicate_blocked=duplicate_blocked)


async def _approved_assessments_for_scope(tenant_id, payload: InvoiceGenerateScope) -> list[StudentFeeAssessment]:
    if payload.assessment_ids:
        rows = []
        for aid in payload.assessment_ids:
            doc = await StudentFeeAssessment.find_one(
                Eq(StudentFeeAssessment.tenant_id, tenant_id),
                Eq(StudentFeeAssessment.assessment_id, aid),
                Eq(StudentFeeAssessment.workflow_status, FeeAssessmentWorkflowStatus.APPROVED.value),
            )
            if doc:
                rows.append(doc)
        return rows
    query = StudentFeeAssessment.find(
        Eq(StudentFeeAssessment.tenant_id, tenant_id),
        Eq(StudentFeeAssessment.academic_year_label, payload.academic_year_label),
        Eq(StudentFeeAssessment.semester_label, payload.semester_label),
        Eq(StudentFeeAssessment.workflow_status, FeeAssessmentWorkflowStatus.APPROVED.value),
    )
    if payload.programme_code:
        query = query.find(Eq(StudentFeeAssessment.programme_code, payload.programme_code.upper()))
    return await query.to_list()


async def generate_invoices(scope: AccessScope, payload: InvoiceGenerateScope) -> dict:
    authorize_finance_invoice_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    billing = payload.billing_date or utcnow().date()
    assessments = await _approved_assessments_for_scope(tenant_id, payload)
    created: list[str] = []
    for assessment in assessments:
        if assessment.invoice_id:
            continue
        inv = await _create_draft_invoice(scope, tenant_id, assessment, billing, payload.due_date)
        created.append(inv.invoice_id)
    return {"created_invoice_ids": created, "count": len(created)}


async def _create_draft_invoice(scope, tenant_id, assessment: StudentFeeAssessment, billing_date, due_date) -> StudentFeeInvoice:
    invoice_id = f"inv_{uuid4().hex[:12]}"
    items = await StudentFeeAssessmentItem.find(
        Eq(StudentFeeAssessmentItem.tenant_id, tenant_id),
        Eq(StudentFeeAssessmentItem.assessment_id, assessment.assessment_id),
    ).to_list()
    demand_id = f"dem_{uuid4().hex[:12]}"
    await StudentFeeDemand(
        tenant_id=tenant_id,
        student_user_id=assessment.student_user_id,
        demand_id=demand_id,
        academic_year_label=assessment.academic_year_label,
        semester_label=assessment.semester_label,
        description=f"Fee demand for {assessment.assessment_id}",
        amount=assessment.net_amount,
        due_date=due_date,
        status=FeeDemandStatus.OPEN,
    ).insert()
    invoice = StudentFeeInvoice(
        tenant_id=tenant_id,
        student_user_id=assessment.student_user_id,
        invoice_id=invoice_id,
        assessment_id=assessment.assessment_id,
        academic_year_label=assessment.academic_year_label,
        semester_label=assessment.semester_label,
        demand_id=demand_id,
        original_amount=assessment.assessed_amount,
        amount=assessment.net_amount,
        invoice_status=StudentInvoiceStatus.DRAFT.value,
        billing_date=billing_date,
        issued_at=utcnow(),
        due_date=due_date,
        published=False,
    )
    await invoice.insert()
    for row in items:
        await StudentInvoiceItem(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            item_id=row.item_id,
            fee_category_code=row.fee_category_code,
            description=row.description,
            assessment_id=assessment.assessment_id,
            structure_id=row.structure_id,
            original_amount=row.original_amount,
            adjustment_amount=row.adjustment_amount,
            net_amount=row.net_amount,
        ).insert()
    assessment.invoice_id = invoice_id
    assessment.demand_id = demand_id
    assessment.updated_at = utcnow()
    await assessment.save()
    await StudentInvoiceHistory(
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        action="create_draft",
        from_status=None,
        to_status=StudentInvoiceStatus.DRAFT.value,
        actor_id=scope.user_id,
    ).insert()
    return invoice


async def issue_invoice(scope: AccessScope, invoice_id: str, note: str | None = None) -> InvoiceRead:
    authorize_finance_invoice_issue(scope)
    tenant_id = require_finance_tenant_scope(scope)
    from app.modules.accounts_finance.period_lock_service import assert_period_open_for_date

    await assert_period_open_for_date(tenant_id)
    invoice = await StudentFeeInvoice.find_one(
        Eq(StudentFeeInvoice.tenant_id, tenant_id),
        Eq(StudentFeeInvoice.invoice_id, invoice_id),
    )
    if invoice is None:
        raise AppError(code="NOT_FOUND", message="Invoice not found", status_code=404)
    if invoice.invoice_status != StudentInvoiceStatus.DRAFT.value:
        raise AppError(code="CONFLICT", message="Only draft invoices can be issued", status_code=409)
    fiscal_year = invoice.academic_year_label or str(utcnow().year)
    invoice.invoice_number = await _next_invoice_number(tenant_id, fiscal_year)
    invoice.invoice_status = StudentInvoiceStatus.ISSUED.value
    invoice.published = True
    invoice.issued_at = utcnow()
    invoice.updated_at = utcnow()
    await invoice.save()

    from app.modules.accounts_finance.ledger_posting_service import post_fee_invoice

    await post_fee_invoice(
        tenant_id=tenant_id,
        student_user_id=invoice.student_user_id,
        invoice_id=invoice.invoice_id,
        invoice_number=invoice.invoice_number or invoice.invoice_id,
        amount=invoice.amount,
        academic_year_label=invoice.academic_year_label,
        semester_label=invoice.semester_label,
        posted_by=scope.user_id,
    )

    await StudentInvoiceHistory(
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        action="issue",
        from_status=StudentInvoiceStatus.DRAFT.value,
        to_status=StudentInvoiceStatus.ISSUED.value,
        actor_id=scope.user_id,
        note=note,
    ).insert()
    await append_institution_audit(
        tenant_id, actor_id=scope.user_id, action="finance.invoice.issue", module="accounts_finance", resource_type="invoice", resource_id=invoice_id
    )
    await enqueue_invoice_issued(
        tenant_id,
        student_user_id=invoice.student_user_id,
        invoice_id=invoice.invoice_id,
        invoice_number=invoice.invoice_number or invoice.invoice_id,
        amount=invoice.amount,
    )
    return await get_invoice(scope, invoice_id)


async def get_invoice(scope: AccessScope, invoice_id: str) -> InvoiceRead:
    authorize_finance_invoice_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    invoice = await StudentFeeInvoice.find_one(
        Eq(StudentFeeInvoice.tenant_id, tenant_id),
        Eq(StudentFeeInvoice.invoice_id, invoice_id),
    )
    if invoice is None:
        raise AppError(code="NOT_FOUND", message="Invoice not found", status_code=404)
    items = await StudentInvoiceItem.find(
        Eq(StudentInvoiceItem.tenant_id, tenant_id),
        Eq(StudentInvoiceItem.invoice_id, invoice_id),
    ).to_list()
    payment_status = await _sync_invoice_payment_status(tenant_id, invoice)
    if payment_status != invoice.invoice_status and invoice.invoice_status not in (
        StudentInvoiceStatus.DRAFT.value,
        StudentInvoiceStatus.CANCELLED.value,
    ):
        invoice.invoice_status = payment_status
        invoice.updated_at = utcnow()
        await invoice.save()
    return _invoice_to_read(invoice, items, payment_status)


async def search_invoices(
    scope: AccessScope,
    pagination: Pagination,
    *,
    student_user_id: str | None = None,
    roll_number: str | None = None,
    invoice_number: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    programme_code: str | None = None,
    invoice_status: str | None = None,
) -> Page[InvoiceRead]:
    authorize_finance_invoice_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    if roll_number:
        profile = await StudentProfile.find_one(
            Eq(StudentProfile.tenant_id, tenant_id),
            Eq(StudentProfile.roll_number, roll_number),
        )
        if profile is None:
            return Page(items=[], total=0, offset=pagination.offset, limit=pagination.limit)
        student_user_id = str(profile.user_id)
    query = StudentFeeInvoice.find(Eq(StudentFeeInvoice.tenant_id, tenant_id))
    if student_user_id:
        query = query.find(Eq(StudentFeeInvoice.student_user_id, to_object_id(student_user_id, "student_user_id")))
    if invoice_number:
        query = query.find(Eq(StudentFeeInvoice.invoice_number, invoice_number))
    if academic_year_label:
        query = query.find(Eq(StudentFeeInvoice.academic_year_label, academic_year_label))
    if semester_label:
        query = query.find(Eq(StudentFeeInvoice.semester_label, semester_label))
    if invoice_status:
        query = query.find(Eq(StudentFeeInvoice.invoice_status, invoice_status))
    docs = await query.sort("-created_at").to_list()
    if programme_code:
        assessments = await StudentFeeAssessment.find(
            Eq(StudentFeeAssessment.tenant_id, tenant_id),
            Eq(StudentFeeAssessment.programme_code, programme_code.upper()),
        ).to_list()
        allowed = {a.invoice_id for a in assessments if a.invoice_id}
        docs = [d for d in docs if d.invoice_id in allowed or d.assessment_id in {a.assessment_id for a in assessments}]
    total = len(docs)
    page_docs = docs[pagination.offset : pagination.offset + pagination.limit]
    items = [await get_invoice(scope, d.invoice_id) for d in page_docs]
    return Page(items=items, total=total, offset=pagination.offset, limit=pagination.limit)


async def apply_invoice_adjustment(scope: AccessScope, invoice_id: str, payload: InvoiceAdjustmentRequest) -> InvoiceRead:
    authorize_finance_invoice_issue(scope)
    tenant_id = require_finance_tenant_scope(scope)
    invoice = await StudentFeeInvoice.find_one(
        Eq(StudentFeeInvoice.tenant_id, tenant_id),
        Eq(StudentFeeInvoice.invoice_id, invoice_id),
    )
    if invoice is None:
        raise AppError(code="NOT_FOUND", message="Invoice not found", status_code=404)
    if invoice.invoice_status == StudentInvoiceStatus.DRAFT.value and payload.adjustment_type != "cancellation":
        raise AppError(code="VALIDATION_ERROR", message="Issue invoice before adjustments", status_code=422)
    adj_id = f"adj_{uuid4().hex[:10]}"
    amount = round_money(payload.amount)
    if payload.adjustment_type == "credit_note":
        doc = StudentCreditNote(
            tenant_id=tenant_id,
            credit_note_id=f"cn_{uuid4().hex[:10]}",
            invoice_id=invoice_id,
            student_user_id=invoice.student_user_id,
            amount=amount,
            reason=payload.reason,
            actor_id=scope.user_id,
        )
        await doc.insert()
        invoice.amount = max(0.0, round_money(invoice.amount - amount))
        invoice.invoice_status = StudentInvoiceStatus.ADJUSTED.value
        rel = doc.credit_note_id
        adj_type = InvoiceAdjustmentType.CREDIT_NOTE
    elif payload.adjustment_type == "debit_note":
        doc = StudentDebitNote(
            tenant_id=tenant_id,
            debit_note_id=f"dn_{uuid4().hex[:10]}",
            invoice_id=invoice_id,
            student_user_id=invoice.student_user_id,
            amount=amount,
            reason=payload.reason,
            actor_id=scope.user_id,
        )
        await doc.insert()
        invoice.amount = round_money(invoice.amount + amount)
        invoice.invoice_status = StudentInvoiceStatus.ADJUSTED.value
        rel = doc.debit_note_id
        adj_type = InvoiceAdjustmentType.DEBIT_NOTE
    elif payload.adjustment_type == "cancellation":
        if invoice.invoice_status != StudentInvoiceStatus.DRAFT.value:
            raise AppError(code="CONFLICT", message="Issued invoices require credit note", status_code=409)
        invoice.invoice_status = StudentInvoiceStatus.CANCELLED.value
        rel = None
        adj_type = InvoiceAdjustmentType.CANCELLATION
        amount = invoice.amount
    else:
        raise AppError(code="VALIDATION_ERROR", message="Unknown adjustment type", status_code=422)

    invoice.updated_at = utcnow()
    await invoice.save()
    if invoice.demand_id:
        demand = await StudentFeeDemand.find_one(
            Eq(StudentFeeDemand.tenant_id, tenant_id),
            Eq(StudentFeeDemand.demand_id, invoice.demand_id),
        )
        if demand:
            demand.amount = invoice.amount
            if invoice.invoice_status == StudentInvoiceStatus.CANCELLED.value:
                demand.status = FeeDemandStatus.WAIVED
            await demand.save()

    await InvoiceAdjustmentHistory(
        tenant_id=tenant_id,
        adjustment_id=adj_id,
        invoice_id=invoice_id,
        adjustment_type=adj_type,
        amount=amount,
        related_document_id=rel,
        actor_id=scope.user_id,
        note=payload.reason,
    ).insert()
    await StudentInvoiceHistory(
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        action=payload.adjustment_type,
        from_status=None,
        to_status=invoice.invoice_status,
        actor_id=scope.user_id,
        note=payload.reason,
    ).insert()
    return await get_invoice(scope, invoice_id)