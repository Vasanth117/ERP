"""System GL posting from mapping rules (idempotent)."""

import uuid
from datetime import date

from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.journal_service import _next_journal_number, _validate_lines, post_journal
from app.modules.accounts_finance.mapping_service import get_active_rule
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.period_lock_service import assert_period_open_for_date
from app.modules.accounts_finance.phase9_enums import JournalSource, JournalStatus
from app.modules.accounts_finance.phase9_models import AccountingReversalHistory, GeneralLedgerEntry, JournalEntry, JournalEntryLine
from app.common.access import AccessScope


async def post_mapped_event(
    *,
    tenant_id,
    event_type: str,
    source_reference: str,
    amount: float,
    journal_date: date,
    narration: str,
    posted_by,
    financial_period_code: str | None = None,
    department_id=None,
    campus_id=None,
    cost_centre_code: str | None = None,
) -> JournalEntry | None:
    amount = round_money(amount)
    if amount <= 0:
        return None
    posting_key = f"gl:{event_type}:{source_reference}"
    existing = await JournalEntry.find_one(
        Eq(JournalEntry.tenant_id, tenant_id),
        Eq(JournalEntry.posting_key, posting_key),
    )
    if existing is not None:
        if existing.status == JournalStatus.POSTED:
            return existing
        raise AppError(code="CONFLICT", message="Duplicate journal in workflow", status_code=409)

    rule = await get_active_rule(tenant_id, event_type)
    if rule is None:
        return None

    await assert_period_open_for_date(tenant_id, journal_date)
    lines = [
        {
            "account_code": rule.debit_account_code,
            "debit": amount,
            "credit": 0,
            "department_id": str(department_id) if department_id else None,
            "campus_id": str(campus_id) if campus_id else None,
            "cost_centre_code": cost_centre_code,
        },
        {
            "account_code": rule.credit_account_code,
            "debit": 0,
            "credit": amount,
            "department_id": str(department_id) if department_id else None,
            "campus_id": str(campus_id) if campus_id else None,
            "cost_centre_code": cost_centre_code,
        },
    ]
    await _validate_lines(tenant_id, lines)
    journal_id = f"jnl_{uuid.uuid4().hex[:12]}"
    journal_number = await _next_journal_number(tenant_id)
    now = utcnow()
    doc = JournalEntry(
        tenant_id=tenant_id,
        journal_id=journal_id,
        journal_number=journal_number,
        journal_date=journal_date,
        financial_period_code=financial_period_code,
        narration=narration,
        lines=lines,
        journal_source=JournalSource.SYSTEM.value,
        source_reference=source_reference,
        posting_key=posting_key,
        status=JournalStatus.APPROVED,
        created_by=posted_by,
        approved_by=posted_by,
        posted_at=now,
        updated_at=now,
    )
    await doc.insert()
    for line in lines:
        await JournalEntryLine(
            tenant_id=tenant_id,
            line_id=f"jln_{uuid.uuid4().hex[:12]}",
            journal_id=journal_id,
            account_code=line["account_code"],
            debit=round_money(line["debit"]),
            credit=round_money(line["credit"]),
            cost_centre_code=cost_centre_code,
        ).insert()
        await GeneralLedgerEntry(
            tenant_id=tenant_id,
            gl_entry_id=f"gle_{uuid.uuid4().hex[:12]}",
            journal_id=journal_id,
            journal_number=journal_number,
            journal_date=journal_date,
            financial_period_code=financial_period_code,
            account_code=line["account_code"],
            debit=round_money(line["debit"]),
            credit=round_money(line["credit"]),
            source_reference=source_reference,
            posted_at=now,
        ).insert()
    doc.status = JournalStatus.POSTED
    await doc.save()
    return doc


async def reverse_journal(scope: AccessScope, journal_id: str, reason: str) -> dict:
    from app.modules.accounts_finance.policy import authorize_finance_gl_journal_post, require_finance_tenant_scope

    authorize_finance_gl_journal_post(scope)
    tenant_id = require_finance_tenant_scope(scope)
    original = await JournalEntry.find_one(Eq(JournalEntry.tenant_id, tenant_id), Eq(JournalEntry.journal_id, journal_id))
    if original is None or original.status != JournalStatus.POSTED:
        raise AppError(code="CONFLICT", message="Only posted journals can be reversed", status_code=409)
    reversed_lines = []
    for line in original.lines:
        reversed_lines.append(
            {
                "account_code": line["account_code"],
                "debit": line.get("credit") or 0,
                "credit": line.get("debit") or 0,
            }
        )
    rev_id = f"jnl_{uuid.uuid4().hex[:12]}"
    rev = JournalEntry(
        tenant_id=tenant_id,
        journal_id=rev_id,
        journal_date=date.today(),
        narration=f"Reversal of {journal_id}: {reason}",
        lines=reversed_lines,
        journal_source=JournalSource.REVERSAL.value,
        source_reference=original.source_reference,
        posting_key=f"gl:reversal:{journal_id}",
        status=JournalStatus.APPROVED,
        reversal_of_journal_id=journal_id,
        created_by=scope.user_id,
        approved_by=scope.user_id,
    )
    await rev.insert()
    scope_post = AccessScope(
        role=scope.role,
        user_id=scope.user_id,
        tenant_id=tenant_id,
        department_id=scope.department_id,
        effective_permissions=scope.effective_permissions,
    )
    result = await post_journal(scope_post, rev_id)
    await AccountingReversalHistory(
        tenant_id=tenant_id,
        reversal_id=f"rev_{uuid.uuid4().hex[:12]}",
        original_journal_id=journal_id,
        reversal_journal_id=rev_id,
        reason=reason,
        actor_id=scope.user_id,
    ).insert()
    original.status = JournalStatus.REVERSED
    await original.save()
    return result