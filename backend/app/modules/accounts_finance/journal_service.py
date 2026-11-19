"""Journal entry workflow and posting to general ledger."""

import uuid
from datetime import date
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.period_lock_service import assert_period_open_for_date
from app.modules.accounts_finance.phase9_enums import JournalSource, JournalStatus
from app.modules.accounts_finance.phase9_models import (
    ChartOfAccount,
    GeneralLedgerEntry,
    JournalApprovalHistory,
    JournalEntry,
    JournalEntryLine,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_gl_approve,
    authorize_finance_gl_journal_post,
    authorize_finance_gl_manage,
    authorize_finance_gl_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit


async def _validate_lines(tenant_id, lines: list[dict]) -> tuple[float, float]:
    if not lines:
        raise AppError(code="VALIDATION_ERROR", message="Journal requires lines", status_code=400)
    total_debit = 0.0
    total_credit = 0.0
    for line in lines:
        debit = round_money(float(line.get("debit") or 0))
        credit = round_money(float(line.get("credit") or 0))
        if debit > 0 and credit > 0:
            raise AppError(code="VALIDATION_ERROR", message="Line cannot have both debit and credit", status_code=400)
        if debit == 0 and credit == 0:
            raise AppError(code="VALIDATION_ERROR", message="Line must have debit or credit", status_code=400)
        code = line["account_code"]
        acct = await ChartOfAccount.find_one(Eq(ChartOfAccount.tenant_id, tenant_id), Eq(ChartOfAccount.account_code, code))
        if acct is None or not acct.active:
            raise AppError(code="VALIDATION_ERROR", message=f"Invalid account {code}", status_code=400)
        total_debit += debit
        total_credit += credit
    total_debit = round_money(total_debit)
    total_credit = round_money(total_credit)
    if total_debit != total_credit:
        raise AppError(
            code="UNBALANCED_JOURNAL",
            message=f"Debits {total_debit} != credits {total_credit}",
            status_code=400,
        )
    return total_debit, total_credit


async def _next_journal_number(tenant_id) -> str:
    count = await JournalEntry.find(Eq(JournalEntry.tenant_id, tenant_id)).count()
    return f"JRN-{count + 1:06d}"


async def _history(tenant_id, journal_id: str, from_status: str | None, to_status: str, actor_id, note: str | None = None) -> None:
    await JournalApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"jah_{uuid.uuid4().hex[:12]}",
        journal_id=journal_id,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
        note=note,
    ).insert()


async def create_manual_journal(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    journal_date: date = payload["journal_date"]
    await assert_period_open_for_date(tenant_id, journal_date)
    lines = payload["lines"]
    await _validate_lines(tenant_id, lines)
    journal_id = f"jnl_{uuid.uuid4().hex[:12]}"
    doc = JournalEntry(
        tenant_id=tenant_id,
        journal_id=journal_id,
        journal_date=journal_date,
        financial_period_code=payload.get("financial_period_code"),
        narration=payload["narration"],
        lines=lines,
        journal_source=JournalSource.MANUAL.value,
        status=JournalStatus.DRAFT,
        currency=payload.get("currency") or "INR",
        document_refs=payload.get("document_refs") or [],
        created_by=scope.user_id,
    )
    await doc.insert()
    await _history(tenant_id, journal_id, None, JournalStatus.DRAFT.value, scope.user_id)
    return {"journal_id": journal_id, "status": doc.status.value}


async def submit_journal(scope: AccessScope, journal_id: str) -> dict:
    authorize_finance_gl_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await JournalEntry.find_one(Eq(JournalEntry.tenant_id, tenant_id), Eq(JournalEntry.journal_id, journal_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Journal not found", status_code=404)
    if doc.status != JournalStatus.DRAFT:
        raise AppError(code="CONFLICT", message="Only draft journals can be submitted", status_code=409)
    await _validate_lines(tenant_id, doc.lines)
    prev = doc.status.value
    doc.status = JournalStatus.SUBMITTED
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, journal_id, prev, doc.status.value, scope.user_id)
    return {"journal_id": journal_id, "status": doc.status.value}


async def approve_journal(scope: AccessScope, journal_id: str, note: str | None = None) -> dict:
    authorize_finance_gl_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await JournalEntry.find_one(Eq(JournalEntry.tenant_id, tenant_id), Eq(JournalEntry.journal_id, journal_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Journal not found", status_code=404)
    if doc.status not in (JournalStatus.SUBMITTED, JournalStatus.UNDER_REVIEW):
        raise AppError(code="CONFLICT", message="Journal not awaiting approval", status_code=409)
    prev = doc.status.value
    doc.status = JournalStatus.APPROVED
    doc.approved_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, journal_id, prev, doc.status.value, scope.user_id, note)
    return {"journal_id": journal_id, "status": doc.status.value}


async def post_journal(scope: AccessScope, journal_id: str) -> dict:
    authorize_finance_gl_journal_post(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await JournalEntry.find_one(Eq(JournalEntry.tenant_id, tenant_id), Eq(JournalEntry.journal_id, journal_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Journal not found", status_code=404)
    if doc.status == JournalStatus.POSTED:
        return {"journal_id": journal_id, "status": doc.status.value, "idempotent": True}
    if doc.status != JournalStatus.APPROVED and doc.journal_source != JournalSource.SYSTEM.value:
        raise AppError(code="CONFLICT", message="Journal must be approved before posting", status_code=409)
    await assert_period_open_for_date(tenant_id, doc.journal_date)
    await _validate_lines(tenant_id, doc.lines)
    if doc.journal_number is None:
        doc.journal_number = await _next_journal_number(tenant_id)
    now = utcnow()
    for line in doc.lines:
        line_id = f"jln_{uuid.uuid4().hex[:12]}"
        dept = to_object_id(line["department_id"], "department_id") if line.get("department_id") else None
        campus = to_object_id(line["campus_id"], "campus_id") if line.get("campus_id") else None
        await JournalEntryLine(
            tenant_id=tenant_id,
            line_id=line_id,
            journal_id=journal_id,
            account_code=line["account_code"],
            debit=round_money(line.get("debit") or 0),
            credit=round_money(line.get("credit") or 0),
            department_id=dept,
            campus_id=campus,
            cost_centre_code=line.get("cost_centre_code"),
            narration=line.get("narration"),
        ).insert()
        await GeneralLedgerEntry(
            tenant_id=tenant_id,
            gl_entry_id=f"gle_{uuid.uuid4().hex[:12]}",
            journal_id=journal_id,
            journal_number=doc.journal_number,
            journal_date=doc.journal_date,
            financial_period_code=doc.financial_period_code,
            account_code=line["account_code"],
            debit=round_money(line.get("debit") or 0),
            credit=round_money(line.get("credit") or 0),
            source_reference=doc.source_reference,
            department_id=dept,
            campus_id=campus,
            cost_centre_code=line.get("cost_centre_code"),
            posted_at=now,
        ).insert()
    prev = doc.status.value
    doc.status = JournalStatus.POSTED
    doc.posted_at = now
    doc.updated_at = now
    await doc.save()
    await _history(tenant_id, journal_id, prev, doc.status.value, scope.user_id, "posted")
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.gl.journal.post",
        module="accounts_finance",
        resource_type="journal_entry",
        resource_id=journal_id,
    )
    return {"journal_id": journal_id, "journal_number": doc.journal_number, "status": doc.status.value}


async def get_journal(scope: AccessScope, journal_id: str) -> dict:
    authorize_finance_gl_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await JournalEntry.find_one(Eq(JournalEntry.tenant_id, tenant_id), Eq(JournalEntry.journal_id, journal_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Journal not found", status_code=404)
    return doc.model_dump()


async def list_journals(scope: AccessScope, *, status: str | None = None) -> list[dict]:
    authorize_finance_gl_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query = JournalEntry.find(Eq(JournalEntry.tenant_id, tenant_id))
    if status:
        query = query.find(Eq(JournalEntry.status, JournalStatus(status)))
    rows = await query.sort("-created_at").limit(100).to_list()
    return [
        {
            "journal_id": r.journal_id,
            "journal_number": r.journal_number,
            "journal_date": r.journal_date.isoformat(),
            "status": r.status.value,
            "journal_source": r.journal_source,
            "source_reference": r.source_reference,
        }
        for r in rows
    ]