"""College Admin phase 1 — dashboard and institution settings."""

from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.college_admin.dashboard_service import get_dashboard_overview, get_institutional_statistics
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.institution_overview_service import get_institutional_overview
from app.modules.college_admin.academic_performance_overview_service import get_academic_performance_overview
from app.modules.college_admin.attendance_overview_service import get_attendance_overview
from app.modules.college_admin.examination_overview_service import get_examination_overview
from app.modules.college_admin.finance_overview_service import get_finance_overview
from app.modules.college_admin.pending_approvals_overview_service import get_pending_approvals_overview
from app.modules.college_admin.recent_activities_overview_service import get_recent_activities_overview
from app.modules.college_admin.alerts_overview_service import get_alerts_overview
from app.modules.college_admin.department_performance_overview_service import get_department_performance_overview
from app.modules.college_admin.faculty_statistics_overview_service import get_faculty_statistics_overview
from app.modules.college_admin.student_statistics_overview_service import get_student_statistics_overview
from app.modules.college_admin.institution_branding_page_service import (
    get_institution_branding_page,
    publish_institution_branding,
    save_institution_branding_draft,
)
from app.modules.college_admin.institution_information_page_service import (
    get_institution_information_page,
    publish_institution_information,
    save_institution_profile_draft,
)
from app.modules.college_admin.institution_academic_year_page_service import (
    create_blank_academic_year,
    get_academic_year_configuration_page,
)
from app.modules.college_admin.institution_policies_page_service import get_institution_policies_page
from app.modules.college_admin.institution_academic_settings_page_service import (
    get_academic_institution_settings_page,
    reset_academic_institution_settings_page,
    save_academic_institution_settings_page,
)
from app.modules.college_admin.institution_calendar_page_service import (
    get_institution_calendar_settings_page,
    save_institution_calendar_settings_page,
)
from app.modules.college_admin.institution_configuration_history_page_service import (
    get_institution_configuration_history_page,
)
from app.modules.college_admin.institution_calendar_models import InstitutionHoliday
from app.modules.college_admin.campus_contact_page_service import get_campus_contact_page, save_campus_contact_page
from app.modules.college_admin.campus_detail_page_service import get_campus_detail_page
from app.modules.college_admin.campus_management_dashboard_service import get_campus_management_dashboard
from app.modules.college_admin.institution_profile_page_service import get_institution_profile_page
from app.modules.college_admin.institution_service import (
    create_campus,
    get_institution_profile,
    get_institution_settings,
    update_institution_profile,
    update_institution_settings,
)
from app.modules.college_admin.schemas import (
    AcademicInstitutionFormValues,
    AcademicInstitutionSettingsSave,
    CampusContactPageSave,
    CampusCreate,
    InstitutionProfileUpdate,
)
from app.modules.college_admin.settings_registry import InstitutionSettingsUpdate, merge_institution_settings
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department, Tenant
from app.modules.tenants.platform_models import InstitutionAddress


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    try:
        await connect_redis()
    except Exception:
        pass
    from app.core.database import document_models

    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed_admin(suffix: str) -> tuple[Tenant, Department, User, AccessScope]:
    tenant = Tenant(
        name=f"College {suffix}",
        code=f"ca_{suffix}",
        institution_email=f"info+{suffix}@example.com",
        institution_type="university",
    )
    await tenant.insert()
    department = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await department.insert()
    user = User(
        email=f"admin+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, department, user, scope


@pytest.mark.anyio
async def test_dashboard_aggregation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, department, user, scope = await _seed_admin(suffix)
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    student_user = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student One",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=department.id,
        is_active=True,
    )
    await student_user.insert()
    await StudentProfile(
        tenant_id=tenant.id,
        user_id=student_user.id,
        roll_number="21CSE001",
        programme_code="BTECH-CSE",
        department_id=department.id,
    ).insert()

    overview = await get_dashboard_overview(scope, user, date_range=DashboardDateRange.WEEK)
    assert overview.academic_term.academic_year_label == "2025-26"
    assert overview.statistics.total_students == 1
    assert overview.statistics.active_students == 1
    assert overview.statistics.department_count == 1
    assert overview.statistics.programme_count == 1

    stats = await get_institutional_statistics(scope)
    assert stats.statistics.faculty_count == 0

    overview_data = await get_institutional_overview(scope)
    assert overview_data.profile.tenant_id == str(tenant.id)
    assert overview_data.statistics.total_students == 1
    assert len(overview_data.programme_mix) >= 1
    assert overview_data.compliance_items

    student_stats = await get_student_statistics_overview(scope)
    assert student_stats.kpis.total_enrolled >= 1
    assert student_stats.programme_year_matrix

    faculty_stats = await get_faculty_statistics_overview(scope)
    assert faculty_stats.kpis is not None
    assert isinstance(faculty_stats.faculty_by_department, list)

    dept_perf = await get_department_performance_overview(scope)
    assert dept_perf.scorecard_total >= 0
    assert dept_perf.kpis is not None

    academic = await get_academic_performance_overview(scope)
    assert academic.kpis is not None
    assert academic.academic_risk

    attendance = await get_attendance_overview(scope, date_range=DashboardDateRange.MONTH)
    assert attendance.kpis is not None
    assert attendance.correction_requests

    examinations = await get_examination_overview(scope)
    assert examinations.kpis is not None
    assert examinations.readiness_checklist is not None

    finance = await get_finance_overview(scope)
    assert finance.kpis is not None
    assert finance.payment_modes

    approvals = await get_pending_approvals_overview(scope, date_range=DashboardDateRange.MONTH)
    assert approvals.kpis is not None
    assert approvals.queue_rows is not None
    assert approvals.pending_by_module is not None

    activities = await get_recent_activities_overview(scope, date_range=DashboardDateRange.TODAY)
    assert activities.kpis is not None
    assert activities.feed_rows is not None
    assert activities.activity_by_module is not None

    alerts = await get_alerts_overview(scope, user)
    assert alerts.kpis is not None
    assert alerts.delivery_channels is not None
    assert alerts.alert_rules is not None


@pytest.mark.anyio
async def test_institution_profile_and_campus(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _department, _user, scope = await _seed_admin(suffix)
    profile = await get_institution_profile(scope)
    assert profile.tenant_code == tenant.code
    assert profile.legal_name == tenant.name

    updated = await update_institution_profile(
        scope,
        InstitutionProfileUpdate(display_name="Updated College", institution_code="INST001"),
    )
    assert updated.display_name == "Updated College"
    assert updated.institution_code == "INST001"

    page = await get_institution_profile_page(scope)
    assert page.display_name == "Updated College"
    assert len(page.about_fields) == 8
    assert page.profile_completeness

    info = await get_institution_information_page(scope)
    assert info.form.legal_name
    assert info.approval_notice.title
    assert len(info.usage_contexts) == 4

    await save_institution_profile_draft(scope, {"description": "Draft description"})
    info_draft = await get_institution_information_page(scope)
    assert info_draft.has_draft
    assert info_draft.form.description == "Draft description"

    await publish_institution_information(
        scope,
        {
            **info_draft.form.model_dump(mode="json"),
            "description": "Published description",
        },
    )
    info_saved = await get_institution_information_page(scope)
    assert info_saved.form.description == "Published description"
    assert not info_saved.has_draft

    await publish_institution_information(
        scope,
        {
            **info_saved.form.model_dump(mode="json"),
            "institution_code": "",
            "affiliation_id": "",
            "aishe_code": "",
            "contact_fax": "",
        },
    )
    after_empty_optional = await get_institution_information_page(scope)
    # Blank optional codes are ignored (do not clear existing stored values).
    assert after_empty_optional.form.institution_code == "INST001"

    branding = await get_institution_branding_page(scope)
    assert branding.primary_logo.upload_hint
    assert len(branding.brand_assets) == 5
    assert len(branding.document_templates) == 4

    await save_institution_branding_draft(scope, {"primary_color": "#1E4FA8"})
    branding_draft = await get_institution_branding_page(scope)
    assert branding_draft.has_draft
    assert branding_draft.form.primary_color == "#1E4FA8"

    await publish_institution_branding(scope, {"primary_color": "#1E4FA8", "secondary_color": "#F2A93B"})
    branding_pub = await get_institution_branding_page(scope)
    assert branding_pub.form.primary_color == "#1E4FA8"
    assert not branding_pub.has_draft

    main = await create_campus(
        scope,
        CampusCreate(campus_code="main", name="Main Campus", is_main=True, address=InstitutionAddress(city="City")),
    )
    assert main.campus_code == "MAIN"

    campus_dashboard = await get_campus_management_dashboard(scope)
    assert campus_dashboard.page_title
    assert len(campus_dashboard.kpis) == 4
    assert any(row.name == "Main Campus" for row in campus_dashboard.campuses)

    from app.common.ids import to_object_id

    campus_oid = to_object_id(main.campus_id, "campus id")
    detail = await get_campus_detail_page(scope, campus_oid)
    assert detail.campus_id == main.campus_id
    assert len(detail.summary_stats) == 6

    contact = await get_campus_contact_page(scope, campus_oid)
    assert contact.page_title
    assert len(contact.usage_contexts) == 3

    saved = await save_campus_contact_page(
        scope,
        campus_oid,
        CampusContactPageSave(
            address=InstitutionAddress(city="City", state="TN", line1="Line 1", postal_code="600001"),
            official_contacts=[],
            emergency_contacts=[],
        ),
    )
    assert saved.address.line1 == "Line 1"

    academic = await get_academic_institution_settings_page(scope)
    assert academic.page_title
    assert academic.form.academic_pattern
    assert len(academic.field_groups) == 3
    assert len(academic.toggle_rules) == 4

    saved_academic = await save_academic_institution_settings_page(
        scope,
        AcademicInstitutionSettingsSave(
            form=academic.form.model_copy(update={"working_days_per_semester": "95"}),
        ),
    )
    assert saved_academic.form.working_days_per_semester == "95"

    reset_academic = await reset_academic_institution_settings_page(scope)
    assert reset_academic.form.working_days_per_semester == "90"

    policies_page = await get_institution_policies_page(scope)
    assert policies_page.page_title
    assert policies_page.pagination.total == 0

    ay_page = await get_academic_year_configuration_page(scope)
    assert ay_page.page_title
    assert "0 academic year" in ay_page.academic_year_count_label

    created_ay = await create_blank_academic_year(scope)
    assert created_ay.selected_year_id
    assert len(created_ay.academic_years) == 1

    from datetime import date

    from beanie import PydanticObjectId

    calendar_page = await get_institution_calendar_settings_page(scope)
    assert calendar_page.page_title == "Institutional Calendar Settings"
    assert len(calendar_page.publishing_toggles) == 4

    await InstitutionHoliday(
        tenant_id=scope.tenant_id,
        academic_year_id=PydanticObjectId(created_ay.selected_year_id),
        holiday_id=f"holiday-{suffix}",
        title="Republic Day",
        start_date=date(2027, 1, 26),
        holiday_type="national",
        applies_to="all",
    ).insert()

    calendar_with_rows = await get_institution_calendar_settings_page(scope)
    assert len(calendar_with_rows.holidays) == 1
    assert calendar_with_rows.holidays[0].type_label == "National"

    from app.modules.college_admin.schemas import InstitutionCalendarSettingsSave

    saved_calendar = await save_institution_calendar_settings_page(
        scope,
        InstitutionCalendarSettingsSave(form=calendar_page.form.model_copy(update={"day_end": "17:00"})),
    )
    assert saved_calendar.form.day_end == "17:00"

    history_page = await get_institution_configuration_history_page(scope)
    assert history_page.page_title == "Campus Configuration History"
    assert history_page.pagination.total >= 1

    duplicate_scope = scope
    with pytest.raises(AppError) as dup_exc:
        await create_campus(duplicate_scope, CampusCreate(campus_code="main", name="Duplicate"))
    assert dup_exc.value.status_code == 409


@pytest.mark.anyio
async def test_settings_validation_and_tenant_isolation(db_ready) -> None:
    settings = await get_institution_settings(scope_a)
    assert settings.tenant_id == str(tenant_a.id)

    await update_institution_settings(
        scope_a,
        InstitutionSettingsUpdate(timezone="Asia/Kolkata", locale="en-IN"),
    )
    with pytest.raises(ValueError):
        merge_institution_settings({}, {"tenant_code": "hacked"})

    scope_b_wrong = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=scope_b.user_id,
        tenant_id=tenant_b.id,
        department_id=None,
        effective_permissions=frozenset({Permission.INSTITUTION_PROFILE_READ}),
    )
    profile_b = await get_institution_profile(scope_b_wrong)
    assert profile_b.tenant_id == str(tenant_b.id)
    assert profile_b.tenant_id != str(tenant_a.id)


@pytest.mark.anyio
async def test_unauthorized_settings_permission(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, user, _scope = await _seed_admin(suffix)
    student = User(
        email=f"st+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    student_scope = AccessScope(
        role=Role.STUDENT,
        user_id=student.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    with pytest.raises(AppError) as exc:
        await get_dashboard_overview(student_scope, student)
    assert exc.value.status_code == 403
