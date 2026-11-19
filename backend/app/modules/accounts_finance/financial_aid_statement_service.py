"""Scholarship and concession student financial aid statement."""

from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.modules.accounts_finance.phase5_models import StudentFeeConcessionAward, StudentFeeWaiver, StudentScholarshipAward
from app.modules.accounts_finance.policy import authorize_finance_ledger_read, require_finance_tenant_scope
from app.modules.college_admin.finance_admin_models import StudentFeeAssessment
from app.modules.finance.finance_models import StudentFeeInvoice


async def student_financial_aid_statement(scope: AccessScope, student_user_id: str, invoice_id: str | None = None) -> dict[str, Any]:
    authorize_finance_ledger_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    sid = to_object_id(student_user_id, "student_user_id")

    original_fees = 0.0
    if invoice_id:
        inv = await StudentFeeInvoice.find_one(
            Eq(StudentFeeInvoice.tenant_id, tenant_id),
            Eq(StudentFeeInvoice.invoice_id, invoice_id),
        )
        if inv:
            original_fees = (inv.original_amount if inv.original_amount else None) or inv.amount
        else:
            from app.modules.finance.finance_models import StudentFinancialLedgerEntry

            led = await StudentFinancialLedgerEntry.find_one(
                Eq(StudentFinancialLedgerEntry.tenant_id, tenant_id),
                Eq(StudentFinancialLedgerEntry.invoice_id, invoice_id),
            )
            if led:
                original_fees = led.debit
    else:
        assessment = (
            await StudentFeeAssessment.find({"tenant_id": tenant_id, "student_user_id": sid})
            .sort("-created_at")
            .limit(1)
            .to_list()
        )
        if assessment:
            doc = assessment[0]
            original_fees = doc.assessed_amount or doc.net_amount

    scholarships = await StudentScholarshipAward.find(
        Eq(StudentScholarshipAward.tenant_id, tenant_id),
        Eq(StudentScholarshipAward.student_user_id, sid),
    ).to_list()
    scholarship_total = sum(a.approved_amount for a in scholarships if a.status.value in ("active", "approved"))

    concessions = await StudentFeeConcessionAward.find(
        Eq(StudentFeeConcessionAward.tenant_id, tenant_id),
        Eq(StudentFeeConcessionAward.student_user_id, sid),
    ).to_list()
    concession_total = sum(c.approved_amount for c in concessions if c.status.value in ("active", "approved"))

    waivers = await StudentFeeWaiver.find(
        Eq(StudentFeeWaiver.tenant_id, tenant_id),
        Eq(StudentFeeWaiver.student_user_id, sid),
    ).to_list()
    waiver_total = sum(w.waived_amount for w in waivers if w.status == "approved")

    total_aid = scholarship_total + concession_total + waiver_total
    remaining = max(0.0, original_fees - total_aid)

    return {
        "student_user_id": student_user_id,
        "invoice_id": invoice_id,
        "original_fees": original_fees,
        "scholarship_award": scholarship_total,
        "concession_amount": concession_total,
        "waiver_amount": waiver_total,
        "total_financial_aid": total_aid,
        "remaining_fee_obligation": remaining,
        "scholarship_awards": [
            {"award_id": a.award_id, "amount": a.approved_amount, "status": a.status.value, "programme_id": a.programme_id}
            for a in scholarships
        ],
        "concession_awards": [
            {"award_id": c.award_id, "amount": c.approved_amount, "status": c.status.value, "policy_id": c.policy_id}
            for c in concessions
        ],
        "waivers": [
            {"waiver_id": w.waiver_id, "waived_amount": w.waived_amount, "status": w.status, "reason": w.reason} for w in waivers
        ],
    }