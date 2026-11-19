"""Accounts / Finance Staff — Phase 12 settings, access and audit."""

from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.modules.accounts_finance.finance_access_service import assign_finance_scope, list_active_access
from app.modules.accounts_finance.finance_audit_service import audit_dashboard, export_finance_audit_csv, search_finance_audit, trace_transaction
from app.modules.accounts_finance.finance_settings_service import (
    activate_settings_version,
    approve_settings_version,
    create_settings_draft,
    get_active_settings,
    settings_dashboard,
    submit_settings_version,
)
from app.modules.accounts_finance.finance_trace_service import register_finance_relationship
from app.modules.accounts_finance.phase12_enums import FinanceSettingsDomain
from app.modules.accounts_finance.phase12_models import FinanceSettingHistory
from app.modules.accounts_finance.phase2_models import StudentInvoiceHistory
from app.modules.auth.models import User
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.tenants.models import Tenant
from app.core.security import hash_password


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
    tenant = Tenant(name=f"Fin P12 {suffix}", code=f"fp12_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p12+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    scope = AccessScope(
        role=Role.FINANCE_STAFF,
        user_id=staff.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FINANCE_STAFF),
    )
    return tenant, staff, scope


@pytest.mark.asyncio
async def test_settings_versioning_lifecycle(db_ready):
    _, staff, scope = await _seed(uuid4().hex[:6])
    domain = FinanceSettingsDomain.PAYMENT.value
    draft = await create_settings_draft(scope, domain, {"allow_online": True, "partial_payments_allowed": False})
    version_id = draft["version_id"]
    await submit_settings_version(scope, domain, version_id)
    await approve_settings_version(scope, domain, version_id)
    active = await activate_settings_version(scope, domain, version_id)
    assert active["status"] == "active"
    loaded = await get_active_settings(scope, domain)
    assert loaded["payload"]["partial_payments_allowed"] is False
    hist = await FinanceSettingHistory.find(Eq(FinanceSettingHistory.tenant_id, scope.tenant_id)).to_list()
    assert len(hist) >= 3


@pytest.mark.asyncio
async def test_audit_trace_and_export(db_ready):
    tenant, staff, scope = await _seed(uuid4().hex[:6])
    invoice_id = f"inv_{uuid4().hex[:8]}"
    payment_id = f"pay_{uuid4().hex[:8]}"
    await StudentInvoiceHistory(
        tenant_id=tenant.id,
        invoice_id=invoice_id,
        action="created",
        actor_id=staff.id,
    ).insert()
    await register_finance_relationship(
        tenant.id,
        link_type="invoice_to_payment",
        from_type="invoice",
        from_id=invoice_id,
        to_type="payment",
        to_id=payment_id,
    )
    await append_institution_audit(
        tenant.id,
        actor_id=staff.id,
        action="finance.invoice.issue",
        module="accounts_finance",
        resource_type="invoice",
        resource_id=invoice_id,
    )
    dash = await audit_dashboard(scope)
    assert dash["total_finance_activities"] >= 1
    trace = await trace_transaction(scope, "invoice", invoice_id)
    assert any(r["to_id"] == payment_id for r in trace["relationships"])
    rows = await search_finance_audit(scope, resource_id=invoice_id)
    assert rows
    _name, csv_body = await export_finance_audit_csv(scope, {"resource_id": invoice_id})
    assert "finance.invoice.issue" in csv_body or invoice_id in csv_body


@pytest.mark.asyncio
async def test_finance_scope_assignment(db_ready):
    tenant, staff, scope = await _seed(uuid4().hex[:6])
    await assign_finance_scope(scope, {"user_id": str(staff.id), "scope_type": "campus", "scope_ref": "main"})
    listed = await list_active_access(scope, str(staff.id))
    assert len(listed["assignments"]) == 1


@pytest.mark.asyncio
async def test_settings_dashboard(db_ready):
    _, _, scope = await _seed(uuid4().hex[:6])
    dash = await settings_dashboard(scope)
    assert "finance_role_catalog" in dash
    assert dash["operating_status"] == "active"