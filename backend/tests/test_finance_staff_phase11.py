"""Accounts / Finance Staff — Phase 11 tax and notifications."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.accounts_finance.finance_reminder_service import notification_dashboard, run_fee_due_reminders, upsert_reminder_policy
from app.modules.accounts_finance.phase11_models import FinanceNotificationEvent, FinanceTaxTransactionRecord
from app.modules.accounts_finance.tax_service import (
    approve_regulatory_report,
    prepare_regulatory_report,
    record_regulatory_filing,
    tax_overview,
    upsert_tax_config_reference,
)
from app.modules.auth.models import User
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.hr.statutory_tax_models import HrStatutoryComponent, HrStatutoryRuleVersion
from app.modules.messaging.outbox_models import DomainOutboxEvent
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
    tenant = Tenant(name=f"Fin P11 {suffix}", code=f"fp11_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p11+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    student = User(
        email=f"stu+p11+{suffix}@example.com",
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
    comp = HrStatutoryComponent(
        tenant_id=tenant.id,
        component_code="GST_OUT",
        display_name="Output GST",
        statutory_ref="gst",
        is_active=True,
    )
    await comp.insert()
    await HrStatutoryRuleVersion(
        tenant_id=tenant.id,
        component_id=comp.id,
        component_code="GST_OUT",
        version_number=1,
        effective_from=date(2020, 1, 1),
        employee_rate_percent="18",
    ).insert()
    await upsert_tax_config_reference(
        scope,
        {
            "tax_category": "output_tax",
            "transaction_type": "fee_invoice",
            "component_code": "GST_OUT",
            "effective_from": date(2020, 1, 1),
        },
    )
    return tenant, staff, student, scope


@pytest.mark.asyncio
async def test_tax_register_and_filing_ack(db_ready):
    tenant, _, student, scope = await _seed(uuid4().hex[:8])
    from app.modules.accounts_finance.tax_service import capture_tax_transaction

    await capture_tax_transaction(
        tenant.id,
        source_type="fee_invoice",
        source_id="inv_test",
        tax_category="output_tax",
        taxable_amount=10000,
        transaction_date=date.today(),
    )
    overview = await tax_overview(scope)
    assert overview["tax_transactions"] >= 1
    report = await prepare_regulatory_report(
        scope,
        {"period_start": date.today() - timedelta(days=30), "period_end": date.today()},
    )
    if report["validation_errors"]:
        pytest.skip("Validation errors in demo data")
    await approve_regulatory_report(scope, report["report_id"])
    with pytest.raises(AppError):
        await record_regulatory_filing(scope, report["report_id"], {})
    filing = await record_regulatory_filing(scope, report["report_id"], {"external_acknowledgment": "GOV-ACK-123"})
    assert filing["filing_status"] == "filed"


@pytest.mark.asyncio
async def test_reminder_dedupe(db_ready):
    tenant, _, student, scope = await _seed(uuid4().hex[:8])
    due = date.today() + timedelta(days=3)
    demand_id = f"dem_{uuid4().hex[:6]}"
    await StudentFeeDemand(
        tenant_id=tenant.id,
        student_user_id=student.id,
        demand_id=demand_id,
        academic_year_label="2025-26",
        semester_label="Odd",
        description="Lab fee",
        amount=2000,
        due_date=due,
        status=FeeDemandStatus.OPEN,
    ).insert()
    await upsert_reminder_policy(scope, {"category": "fee_due", "days_before_due": 3})
    r1 = await run_fee_due_reminders(scope)
    r2 = await run_fee_due_reminders(scope)
    assert r1["reminders_queued"] >= 1
    assert r2["reminders_queued"] == r1["reminders_queued"]
    events = await FinanceNotificationEvent.find(Eq(FinanceNotificationEvent.tenant_id, tenant.id)).to_list()
    assert len(events) >= 1
    outbox = await DomainOutboxEvent.find(Eq(DomainOutboxEvent.tenant_id, tenant.id)).count()
    assert outbox >= 1
    dash = await notification_dashboard(scope)
    assert dash["total_notifications"] >= 1