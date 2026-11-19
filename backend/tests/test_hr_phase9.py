"""HR staff portal phase 9 — communications and reports."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.employee_profile_schemas import EmployeeRegister
from app.modules.hr.employee_profile_service import register_employee
from app.modules.hr.hr_audience_resolver import resolve_hr_audience
from app.modules.hr.hr_communication_models import HrNotificationDeliveryHistory
from app.modules.hr.hr_communication_schemas import AnnouncementCreate, AnnouncementTransition, AudiencePreview
from app.modules.hr.hr_communication_service import (
    create_announcement,
    mark_notification_read,
    my_inbox,
    preview_audience,
    transition_announcement,
)
from app.modules.hr.hr_reports_schemas import ReportExportRequest, ReportRunRequest
from app.modules.hr.hr_reports_service import analytics_dashboard, export_report, list_report_catalog, run_report
from app.modules.tenants.models import Department, Tenant


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


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


async def _seed(suffix: str):
    tenant = Tenant(name=f"HR9 {suffix}", code=f"hr9_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="HR", code=f"HR-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"C{suffix}", name="Main", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hr9+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    emp_user = User(
        email=f"emp9+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Employee",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await emp_user.insert()
    hr_scope = _scope(hr_user, Role.HR_STAFF)
    emp_scope = _scope(emp_user, Role.FACULTY)
    await register_employee(
        hr_scope,
        EmployeeRegister(
            employee_code=f"EMP9-{suffix}",
            first_name="Test",
            last_name="Employee",
            official_email=f"official9+{suffix}@college.edu",
            mobile_number="9999999999",
            joining_date=date.today() - timedelta(days=100),
            employee_category="faculty",
            employment_type="permanent",
            department_id=str(dept.id),
            designation="Assistant Professor",
            campus_id=str(campus.id),
            link_existing_user_id=str(emp_user.id),
            institution_role=Role.FACULTY,
        ),
    )
    return tenant, hr_scope, emp_scope, emp_user, dept


@pytest.mark.asyncio
async def test_announcement_and_inbox(db_ready):
    suffix = uuid4().hex[:6]
    tenant, hr_scope, emp_scope, emp_user, dept = await _seed(suffix)
    users = await resolve_hr_audience(tenant.id, {"all_employees": True})
    assert str(emp_user.id) in [str(u) for u in users]
    preview = await preview_audience(hr_scope, {"all_employees": True})
    assert isinstance(preview, AudiencePreview)
    assert preview.recipient_count >= 1
    ann = await create_announcement(
        hr_scope,
        AnnouncementCreate(
            announcement_code=f"ANN-{suffix}",
            title="Holiday notice",
            body="Campus closed tomorrow",
            category="general",
            audience={"all_employees": True},
        ),
    )
    published = await transition_announcement(hr_scope, ann.id, AnnouncementTransition(action="publish"))
    assert published.status.value == "published"
    inbox = await my_inbox(emp_scope)
    assert len(inbox) >= 1
    await mark_notification_read(emp_scope, inbox[0].id)
    row = await HrNotificationDeliveryHistory.get(inbox[0].id)
    assert row.status.value == "read"


@pytest.mark.asyncio
async def test_reports_catalog_and_export(db_ready):
    suffix = uuid4().hex[:6]
    _, hr_scope, _, _, _ = await _seed(suffix)
    catalog = await list_report_catalog(hr_scope)
    assert any(c.report_key == "employee_master" for c in catalog)
    dash = await analytics_dashboard(hr_scope)
    assert dash.workforce_size >= 1
    data = await run_report(hr_scope, ReportRunRequest(report_key="employee_master", filters={}))
    assert data.row_count >= 1
    export = await export_report(
        hr_scope,
        ReportExportRequest(report_key="employee_master", filters={}, export_format="csv"),
    )
    assert export.row_count >= 1
    assert export.has_download