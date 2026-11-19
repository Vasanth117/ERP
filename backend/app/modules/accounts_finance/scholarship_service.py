"""Scholarship programmes, applications, awards and renewals."""

from datetime import date
from typing import Any
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.financial_aid_posting import post_scholarship_credit
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase5_enums import ScholarshipAwardStatus, ScholarshipProgramStatus, ScholarshipWorkflowStatus
from app.modules.accounts_finance.phase5_models import (
    ScholarshipApplicationReview,
    ScholarshipAwardHistory,
    ScholarshipEligibilityRule,
    ScholarshipFundingAllocation,
    ScholarshipRenewalRecord,
    StudentScholarshipAward,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_scholarship_approve,
    authorize_finance_scholarship_manage,
    authorize_finance_scholarship_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import ScholarshipApplicationStatus
from app.modules.finance.finance_models import OfficialScholarshipApplication, ScholarshipProgram
from app.modules.students.integrations.student_finance_reader import scholarship_eligibility_rows, student_programme_code
from app.modules.students.models import StudentProfile
from app.modules.students.student_finance_models import StudentScholarshipApplication


async def _program_read(prog: ScholarshipProgram) -> dict[str, Any]:
    return {
        "programme_id": prog.programme_id,
        "scholarship_code": prog.scholarship_code,
        "title": prog.title,
        "description": prog.description,
        "funding_source": prog.funding_source,
        "scholarship_type": prog.scholarship_type,
        "academic_year_label": prog.academic_year_label,
        "applicable_programmes": prog.applicable_programmes,
        "applicable_departments": prog.applicable_departments,
        "eligible_student_categories": prog.eligible_student_categories,
        "eligibility_conditions": prog.eligibility_conditions,
        "max_award_amount": prog.max_award_amount,
        "award_calculation_method": prog.award_calculation_method,
        "fund_budget_reference": prog.fund_budget_reference,
        "max_awards": prog.max_awards,
        "application_start": prog.application_start,
        "application_deadline": prog.application_deadline,
        "approval_requirements": prog.approval_requirements,
        "renewal_rules": prog.renewal_rules,
        "effective_from": prog.effective_from,
        "effective_to": prog.effective_to,
        "program_status": prog.program_status,
        "applications_open": prog.applications_open,
    }


async def list_programs(scope: AccessScope, pagination: Pagination) -> Page[dict[str, Any]]:
    authorize_finance_scholarship_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    total = await ScholarshipProgram.find(Eq(ScholarshipProgram.tenant_id, tenant_id)).count()
    rows = (
        await ScholarshipProgram.find(Eq(ScholarshipProgram.tenant_id, tenant_id))
        .sort("-updated_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [await _program_read(r) for r in rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def upsert_program(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_scholarship_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    programme_id = payload.get("programme_id") or f"schprog_{uuid4().hex[:12]}"
    existing = await ScholarshipProgram.find_one(
        Eq(ScholarshipProgram.tenant_id, tenant_id),
        Eq(ScholarshipProgram.programme_id, programme_id),
    )
    fields = {
        "scholarship_code": payload.get("scholarship_code"),
        "title": payload["title"],
        "description": payload.get("description"),
        "funding_source": payload.get("funding_source"),
        "scholarship_type": payload.get("scholarship_type"),
        "academic_year_label": payload.get("academic_year_label"),
        "applicable_programmes": payload.get("applicable_programmes") or [],
        "applicable_departments": payload.get("applicable_departments") or [],
        "eligible_student_categories": payload.get("eligible_student_categories") or [],
        "eligibility_conditions": payload.get("eligibility_conditions") or {},
        "max_award_amount": payload.get("max_award_amount"),
        "award_calculation_method": payload.get("award_calculation_method"),
        "fund_budget_reference": payload.get("fund_budget_reference"),
        "max_awards": payload.get("max_awards"),
        "application_start": payload.get("application_start"),
        "application_deadline": payload.get("application_deadline"),
        "approval_requirements": payload.get("approval_requirements") or [],
        "renewal_rules": payload.get("renewal_rules") or {},
        "effective_from": payload.get("effective_from"),
        "effective_to": payload.get("effective_to"),
        "program_status": payload.get("program_status", ScholarshipProgramStatus.DRAFT.value),
        "applications_open": bool(payload.get("applications_open", False)),
        "updated_at": utcnow(),
    }
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        await existing.save()
        prog = existing
    else:
        prog = await ScholarshipProgram(tenant_id=tenant_id, programme_id=programme_id, created_at=utcnow(), **fields).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="scholarship_program_upsert",
        module="accounts_finance",
        resource_type="scholarship_program",
        resource_id=programme_id,
    )
    return await _program_read(prog)


async def upsert_eligibility_rule(scope: AccessScope, programme_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_scholarship_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rule_id = payload.get("rule_id") or f"rule_{uuid4().hex[:10]}"
    row = await ScholarshipEligibilityRule.find_one(
        Eq(ScholarshipEligibilityRule.tenant_id, tenant_id),
        Eq(ScholarshipEligibilityRule.rule_id, rule_id),
    )
    data = {
        "programme_id": programme_id,
        "rule_name": payload["rule_name"],
        "field_path": payload["field_path"],
        "operator": payload["operator"],
        "value": payload.get("value"),
        "required": bool(payload.get("required", True)),
        "active": bool(payload.get("active", True)),
    }
    if row:
        for k, v in data.items():
            setattr(row, k, v)
        await row.save()
    else:
        row = await ScholarshipEligibilityRule(tenant_id=tenant_id, rule_id=rule_id, **data).insert()
    return {
        "rule_id": row.rule_id,
        "programme_id": row.programme_id,
        "rule_name": row.rule_name,
        "field_path": row.field_path,
        "operator": row.operator,
        "value": row.value,
        "required": row.required,
        "active": row.active,
    }


async def evaluate_student_eligibility(scope: AccessScope, programme_id: str, student_user_id: str) -> dict[str, Any]:
    authorize_finance_scholarship_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    sid = to_object_id(student_user_id, "student_user_id")
    prog = await ScholarshipProgram.find_one(
        Eq(ScholarshipProgram.tenant_id, tenant_id),
        Eq(ScholarshipProgram.programme_id, programme_id),
    )
    if prog is None:
        raise AppError(code="NOT_FOUND", message="Scholarship program not found", status_code=404)
    profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": sid})
    prog_code = await student_programme_code(tenant_id, sid)
    reasons: list[str] = []
    eligible = True

    if prog.applicable_programmes and prog_code and prog_code not in prog.applicable_programmes:
        eligible = False
        reasons.append("Programme not in applicable list")
    if prog.applicable_departments and profile and profile.department_id:
        if str(profile.department_id) not in prog.applicable_departments:
            eligible = False
            reasons.append("Department not eligible")

    rules = await ScholarshipEligibilityRule.find(
        Eq(ScholarshipEligibilityRule.tenant_id, tenant_id),
        Eq(ScholarshipEligibilityRule.programme_id, programme_id),
        Eq(ScholarshipEligibilityRule.active, True),
    ).to_list()
    ctx = {
        "programme_code": prog_code,
        "department_id": str(profile.department_id) if profile and profile.department_id else None,
    }
    for rule in rules:
        actual = ctx.get(rule.field_path.replace("student.", ""))
        if rule.field_path == "published_eligibility":
            rows = await scholarship_eligibility_rows(tenant_id, sid)
            pub = next((r for r in rows if r.programme_id == programme_id), None)
            if pub is None or not pub.eligible:
                if rule.required:
                    eligible = False
                    reasons.append(f"Rule failed: {rule.rule_name}")
            continue
        if rule.operator == "gte" and actual is not None and rule.value is not None:
            if float(actual) < float(rule.value):
                eligible = False
                reasons.append(f"Rule failed: {rule.rule_name}")
        if rule.operator == "in" and actual is not None and rule.value is not None:
            if actual not in rule.value:
                eligible = False
                reasons.append(f"Rule failed: {rule.rule_name}")

    return {"programme_id": programme_id, "student_user_id": student_user_id, "eligible": eligible, "reasons": reasons}


async def list_applications(scope: AccessScope, pagination: Pagination, programme_id: str | None = None) -> Page[dict[str, Any]]:
    authorize_finance_scholarship_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query: dict[str, Any] = {"tenant_id": tenant_id}
    if programme_id:
        query["programme_id"] = programme_id
    total = await OfficialScholarshipApplication.find(query).count()
    rows = (
        await OfficialScholarshipApplication.find(query)
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [
        {
            "application_id": r.application_id,
            "student_user_id": str(r.student_user_id),
            "programme_id": r.programme_id,
            "status": r.status.value if hasattr(r.status, "value") else r.status,
            "workflow_status": r.workflow_status,
            "requested_award_amount": r.requested_award_amount,
            "academic_year_label": r.academic_year_label,
            "semester_label": r.semester_label,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def review_application(scope: AccessScope, application_id: str, recommendation: str, comments: str | None) -> dict[str, Any]:
    authorize_finance_scholarship_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    app = await OfficialScholarshipApplication.find_one(
        Eq(OfficialScholarshipApplication.tenant_id, tenant_id),
        Eq(OfficialScholarshipApplication.application_id, application_id),
    )
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    review_id = f"rev_{uuid4().hex[:10]}"
    await ScholarshipApplicationReview(
        tenant_id=tenant_id,
        review_id=review_id,
        application_id=application_id,
        reviewer_role="finance",
        reviewer_id=scope.user_id,
        recommendation=recommendation,
        comments=comments,
    ).insert()
    app.workflow_status = ScholarshipWorkflowStatus.UNDER_REVIEW.value
    app.status = ScholarshipApplicationStatus.IN_REVIEW
    app.updated_at = utcnow()
    await app.save()
    return {"application_id": application_id, "review_id": review_id, "workflow_status": app.workflow_status}


async def _funding_remaining(tenant_id, programme_id: str, funding_source: str) -> float:
    alloc = await ScholarshipFundingAllocation.find_one(
        Eq(ScholarshipFundingAllocation.tenant_id, tenant_id),
        Eq(ScholarshipFundingAllocation.programme_id, programme_id),
        Eq(ScholarshipFundingAllocation.funding_source, funding_source),
    )
    if alloc is None:
        return float("inf")
    return round_money(alloc.total_fund - alloc.committed_total - alloc.pending_total)


async def _commit_funding(tenant_id, programme_id: str, funding_source: str, amount: float, *, pending: bool = False) -> None:
    alloc = await ScholarshipFundingAllocation.find_one(
        Eq(ScholarshipFundingAllocation.tenant_id, tenant_id),
        Eq(ScholarshipFundingAllocation.programme_id, programme_id),
        Eq(ScholarshipFundingAllocation.funding_source, funding_source),
    )
    if alloc is None:
        return
    if pending:
        alloc.pending_total = round_money(alloc.pending_total + amount)
    else:
        alloc.committed_total = round_money(alloc.committed_total + amount)
        alloc.approved_total = round_money(alloc.approved_total + amount)
        alloc.pending_total = max(0.0, round_money(alloc.pending_total - amount))
    alloc.updated_at = utcnow()
    await alloc.save()


async def approve_application(
    scope: AccessScope,
    application_id: str,
    *,
    approved_amount: float,
    invoice_id: str | None = None,
    allow_over_budget: bool = False,
) -> dict[str, Any]:
    authorize_finance_scholarship_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    app = await OfficialScholarshipApplication.find_one(
        Eq(OfficialScholarshipApplication.tenant_id, tenant_id),
        Eq(OfficialScholarshipApplication.application_id, application_id),
    )
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    existing_award = await StudentScholarshipAward.find_one(
        Eq(StudentScholarshipAward.tenant_id, tenant_id),
        Eq(StudentScholarshipAward.application_id, application_id),
        Eq(StudentScholarshipAward.status, ScholarshipAwardStatus.ACTIVE),
    )
    if existing_award is not None:
        raise AppError(code="CONFLICT", message="Award already posted for application", status_code=409)
    prog = await ScholarshipProgram.find_one(
        Eq(ScholarshipProgram.tenant_id, tenant_id),
        Eq(ScholarshipProgram.programme_id, app.programme_id),
    )
    amount = round_money(approved_amount)
    if prog and prog.max_award_amount is not None and amount > prog.max_award_amount:
        raise AppError(code="VALIDATION_ERROR", message="Award exceeds program maximum", status_code=422)
    funding_source = (prog.funding_source if prog else None) or "institution"
    remaining = await _funding_remaining(tenant_id, app.programme_id, funding_source)
    if amount > remaining and not allow_over_budget:
        raise AppError(code="CONFLICT", message="Insufficient scholarship funding", status_code=409)

    award_id = f"swd_{uuid4().hex[:12]}"
    award = await StudentScholarshipAward(
        tenant_id=tenant_id,
        award_id=award_id,
        student_user_id=app.student_user_id,
        programme_id=app.programme_id,
        application_id=application_id,
        approved_amount=amount,
        funding_source=funding_source,
        academic_year_label=app.academic_year_label,
        semester_label=app.semester_label,
        invoice_id=invoice_id,
        status=ScholarshipAwardStatus.APPROVED,
        approval_reference=application_id,
        approved_by=scope.user_id,
    ).insert()

    if not award.ledger_posted:
        await post_scholarship_credit(
            tenant_id=tenant_id,
            student_user_id=app.student_user_id,
            amount=amount,
            award_id=award_id,
            invoice_id=invoice_id,
            academic_year_label=app.academic_year_label,
            semester_label=app.semester_label,
            posted_by=scope.user_id,
        )
        award.ledger_posted = True
        award.status = ScholarshipAwardStatus.ACTIVE
        award.disbursement_status = "posted"
        award.updated_at = utcnow()
        await award.save()

    await _commit_funding(tenant_id, app.programme_id, funding_source, amount)
    app.status = ScholarshipApplicationStatus.APPROVED
    app.workflow_status = ScholarshipWorkflowStatus.AWARDED.value
    app.updated_at = utcnow()
    await app.save()

    portal = await StudentScholarshipApplication.find_one(
        {"tenant_id": tenant_id, "application_id": application_id, "user_id": app.student_user_id}
    )
    if portal:
        portal.status = ScholarshipApplicationStatus.APPROVED.value
        portal.updated_at = utcnow()
        await portal.save()

    await ScholarshipAwardHistory(
        tenant_id=tenant_id,
        history_id=f"hist_{uuid4().hex[:10]}",
        award_id=award_id,
        action="approve",
        to_status=award.status.value,
        actor_id=scope.user_id,
        note=f"application={application_id}",
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="scholarship_award_approved",
        module="accounts_finance",
        resource_type="student_scholarship_award",
        resource_id=award_id,
        metadata={"amount": amount},
    )
    return {"award_id": award_id, "approved_amount": amount, "status": award.status.value}


async def reject_application(scope: AccessScope, application_id: str, reason: str) -> dict[str, Any]:
    authorize_finance_scholarship_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    app = await OfficialScholarshipApplication.find_one(
        Eq(OfficialScholarshipApplication.tenant_id, tenant_id),
        Eq(OfficialScholarshipApplication.application_id, application_id),
    )
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    app.status = ScholarshipApplicationStatus.REJECTED
    app.workflow_status = ScholarshipWorkflowStatus.REJECTED.value
    app.updated_at = utcnow()
    await app.save()
    return {"application_id": application_id, "status": app.workflow_status, "reason": reason}


async def record_staff_award(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_scholarship_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    student_user_id = to_object_id(payload["student_user_id"], "student_user_id")
    programme_id = payload["programme_id"]
    amount = round_money(payload["approved_amount"])
    award_id = f"swd_{uuid4().hex[:12]}"
    award = await StudentScholarshipAward(
        tenant_id=tenant_id,
        award_id=award_id,
        student_user_id=student_user_id,
        programme_id=programme_id,
        approved_amount=amount,
        funding_source=payload.get("funding_source"),
        invoice_id=payload.get("invoice_id"),
        academic_year_label=payload.get("academic_year_label"),
        semester_label=payload.get("semester_label"),
        status=ScholarshipAwardStatus.APPROVED,
        approved_by=scope.user_id,
    ).insert()
    await post_scholarship_credit(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        amount=amount,
        award_id=award_id,
        invoice_id=payload.get("invoice_id"),
        academic_year_label=payload.get("academic_year_label"),
        semester_label=payload.get("semester_label"),
        posted_by=scope.user_id,
    )
    award.ledger_posted = True
    award.status = ScholarshipAwardStatus.ACTIVE
    await award.save()
    return {"award_id": award_id, "approved_amount": amount}


async def upsert_funding(scope: AccessScope, programme_id: str, funding_source: str, total_fund: float) -> dict[str, Any]:
    authorize_finance_scholarship_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    allocation_id = f"fund_{uuid4().hex[:10]}"
    row = await ScholarshipFundingAllocation.find_one(
        Eq(ScholarshipFundingAllocation.tenant_id, tenant_id),
        Eq(ScholarshipFundingAllocation.programme_id, programme_id),
        Eq(ScholarshipFundingAllocation.funding_source, funding_source),
    )
    if row is None:
        row = await ScholarshipFundingAllocation(
            tenant_id=tenant_id,
            allocation_id=allocation_id,
            programme_id=programme_id,
            funding_source=funding_source,
            total_fund=round_money(total_fund),
        ).insert()
    else:
        row.total_fund = round_money(total_fund)
        row.updated_at = utcnow()
        await row.save()
    remaining = round_money(row.total_fund - row.committed_total - row.pending_total)
    return {
        "allocation_id": row.allocation_id,
        "total_fund": row.total_fund,
        "committed_total": row.committed_total,
        "pending_total": row.pending_total,
        "remaining": remaining,
    }


async def funding_summary(scope: AccessScope, programme_id: str) -> list[dict[str, Any]]:
    authorize_finance_scholarship_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await ScholarshipFundingAllocation.find(
        Eq(ScholarshipFundingAllocation.tenant_id, tenant_id),
        Eq(ScholarshipFundingAllocation.programme_id, programme_id),
    ).to_list()
    return [
        {
            "funding_source": r.funding_source,
            "total_fund": r.total_fund,
            "approved_total": r.approved_total,
            "committed_total": r.committed_total,
            "pending_total": r.pending_total,
            "remaining": round_money(r.total_fund - r.committed_total - r.pending_total),
        }
        for r in rows
    ]


async def submit_renewal(scope: AccessScope, award_id: str, academic_year_label: str) -> dict[str, Any]:
    authorize_finance_scholarship_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    award = await StudentScholarshipAward.find_one(
        Eq(StudentScholarshipAward.tenant_id, tenant_id),
        Eq(StudentScholarshipAward.award_id, award_id),
    )
    if award is None:
        raise AppError(code="NOT_FOUND", message="Award not found", status_code=404)
    renewal_id = f"ren_{uuid4().hex[:10]}"
    row = await ScholarshipRenewalRecord(
        tenant_id=tenant_id,
        renewal_id=renewal_id,
        award_id=award_id,
        student_user_id=award.student_user_id,
        academic_year_label=academic_year_label,
        status="submitted",
    ).insert()
    return {"renewal_id": row.renewal_id, "award_id": award_id, "status": row.status}


async def decide_renewal(scope: AccessScope, renewal_id: str, *, approved: bool, approved_amount: float | None = None) -> dict[str, Any]:
    authorize_finance_scholarship_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    ren = await ScholarshipRenewalRecord.find_one(
        Eq(ScholarshipRenewalRecord.tenant_id, tenant_id),
        Eq(ScholarshipRenewalRecord.renewal_id, renewal_id),
    )
    if ren is None:
        raise AppError(code="NOT_FOUND", message="Renewal not found", status_code=404)
    award = await StudentScholarshipAward.find_one(
        Eq(StudentScholarshipAward.tenant_id, tenant_id),
        Eq(StudentScholarshipAward.award_id, ren.award_id),
    )
    if award is None:
        raise AppError(code="NOT_FOUND", message="Award not found", status_code=404)
    if approved:
        amt = round_money(approved_amount if approved_amount is not None else award.approved_amount)
        new_award_id = f"swd_{uuid4().hex[:12]}"
        await StudentScholarshipAward(
            tenant_id=tenant_id,
            award_id=new_award_id,
            student_user_id=award.student_user_id,
            programme_id=award.programme_id,
            application_id=award.application_id,
            approved_amount=amt,
            funding_source=award.funding_source,
            academic_year_label=ren.academic_year_label,
            semester_label=award.semester_label,
            invoice_id=award.invoice_id,
            status=ScholarshipAwardStatus.ACTIVE,
            approved_by=scope.user_id,
            ledger_posted=False,
        ).insert()
        await post_scholarship_credit(
            tenant_id=tenant_id,
            student_user_id=award.student_user_id,
            amount=amt,
            award_id=new_award_id,
            invoice_id=award.invoice_id,
            academic_year_label=ren.academic_year_label,
            semester_label=award.semester_label,
            posted_by=scope.user_id,
        )
        ren.decision = "approved"
        ren.approved_amount = amt
        ren.status = "approved"
        award.status = ScholarshipAwardStatus.EXPIRED
        await award.save()
    else:
        ren.decision = "rejected"
        ren.status = "rejected"
        award.status = ScholarshipAwardStatus.TERMINATED
        await award.save()
    ren.actor_id = scope.user_id
    await ren.save()
    return {"renewal_id": renewal_id, "decision": ren.decision, "status": ren.status}