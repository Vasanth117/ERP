"""Accounts / Finance Staff — Phase 5 scholarships and concessions."""

from datetime import date
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.accounts_finance.concession_service import approve_concession_application, submit_concession_application, upsert_category, upsert_policy
from app.modules.accounts_finance.financial_aid_statement_service import student_financial_aid_statement
from app.modules.accounts_finance.ledger_posting_service import post_fee_invoice
from app.modules.accounts_finance.phase5_models import StudentScholarshipAward
from app.modules.accounts_finance.scholarship_service import (
    approve_application,
    record_staff_award,
    upsert_funding,
    upsert_program,
)
from app.modules.auth.models import User
from app.modules.finance.finance_enums import ScholarshipApplicationStatus
from app.modules.accounts_finance.phase2_enums import StudentInvoiceStatus
from app.modules.finance.finance_models import OfficialScholarshipApplication, StudentFeeInvoice, StudentFinancialLedgerEntry
from app.common.time import utcnow
from app.modules.tenants.models import Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_mongo()


async def _seed(suffix: str):
    tenant = Tenant(name=f"Fin P5 {suffix}", code=f"fp5_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    student = User(
        email=f"stu+p5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    scope = AccessScope(
        role=Role.FINANCE_STAFF,
        user_id=staff.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FINANCE_STAFF),
    )
    accounts_scope = AccessScope(
        role=Role.ACCOUNTS_STAFF,
        user_id=staff.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.ACCOUNTS_STAFF),
    )
    return tenant, scope, accounts_scope, student


@pytest.mark.anyio
async def test_scholarship_funding_limit(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, _, student = await _seed(suffix)
    programme_id = f"sch_{suffix}"
    await upsert_program(
        scope,
        {
            "programme_id": programme_id,
            "title": "Merit Aid",
            "funding_source": "institution",
            "max_award_amount": 10000,
            "applications_open": True,
            "program_status": "open",
        },
    )
    await upsert_funding(scope, programme_id, "institution", 5000)
    app_id = f"app_{suffix}"
    await OfficialScholarshipApplication(
        tenant_id=tenant.id,
        student_user_id=student.id,
        application_id=app_id,
        programme_id=programme_id,
        status=ScholarshipApplicationStatus.SUBMITTED,
    ).insert()
    await approve_application(scope, app_id, approved_amount=3000)
    with pytest.raises(AppError) as exc:
        await approve_application(scope, app_id, approved_amount=3000)
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_scholarship_staff_award_ledger(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, _, student = await _seed(suffix)
    programme_id = f"sch_{suffix}"
    await upsert_funding(scope, programme_id, "gov", 50000)
    result = await record_staff_award(
        scope,
        {"student_user_id": str(student.id), "programme_id": programme_id, "approved_amount": 2500},
    )
    entry = await StudentFinancialLedgerEntry.find_one(
        Eq(StudentFinancialLedgerEntry.tenant_id, tenant.id),
        Eq(StudentFinancialLedgerEntry.posting_key, f"scholarship:{result['award_id']}"),
    )
    assert entry is not None
    assert entry.credit == 2500
    dup = await record_staff_award(
        scope,
        {"student_user_id": str(student.id), "programme_id": programme_id, "approved_amount": 2500},
    )
    assert dup["award_id"] != result["award_id"]


@pytest.mark.anyio
async def test_concession_stacking_and_statement(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, _, student = await _seed(suffix)
    invoice_id = f"inv_{suffix}"
    await StudentFeeInvoice(
        tenant_id=tenant.id,
        student_user_id=student.id,
        invoice_id=invoice_id,
        amount=10000,
        original_amount=10000,
        due_date=date.today(),
        issued_at=utcnow(),
        invoice_status=StudentInvoiceStatus.ISSUED.value,
        published=True,
    ).insert()
    await post_fee_invoice(
        tenant_id=tenant.id,
        student_user_id=student.id,
        invoice_id=invoice_id,
        invoice_number=f"INV-{suffix}",
        amount=10000,
    )
    cat = await upsert_category(scope, {"code": "MERIT", "name": "Merit concession"})
    policy = await upsert_policy(
        scope,
        {
            "policy_code": f"POL_{suffix}",
            "name": "Merit 10%",
            "category_id": cat["category_id"],
            "concession_type": "fixed",
            "fixed_amount": 1000,
            "stacking_rules": {"max_combined_amount": 2000},
        },
    )
    app = await submit_concession_application(
        scope,
        {
            "student_user_id": str(student.id),
            "policy_id": policy["policy_id"],
            "reason": "Merit performance",
            "invoice_id": invoice_id,
        },
    )
    award = await approve_concession_application(scope, app["application_id"], approved_amount=1000)
    assert award["approved_amount"] == 1000
    ledger = await StudentFinancialLedgerEntry.find_one(
        Eq(StudentFinancialLedgerEntry.tenant_id, tenant.id),
        Eq(StudentFinancialLedgerEntry.posting_key, f"concession:{award['award_id']}"),
    )
    assert ledger is not None
    stmt = await student_financial_aid_statement(scope, str(student.id), invoice_id)
    assert stmt["concession_amount"] == 1000
    assert stmt["remaining_fee_obligation"] == 9000


@pytest.mark.anyio
async def test_unauthorized_scholarship_approve(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, accounts_scope, student = await _seed(suffix)
    programme_id = f"sch_{suffix}"
    app_id = f"app2_{suffix}"
    await OfficialScholarshipApplication(
        tenant_id=tenant.id,
        student_user_id=student.id,
        application_id=app_id,
        programme_id=programme_id,
        status=ScholarshipApplicationStatus.SUBMITTED,
    ).insert()
    with pytest.raises(Exception):
        await approve_application(accounts_scope, app_id, approved_amount=1000)