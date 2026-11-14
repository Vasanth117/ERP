"""College Admin phase 8 — LMS administration and reports analytics."""

from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.lms_admin_schemas import LmsCourseMappingUpsert, LmsPublishingPolicyUpsert, LmsSettingsUpdate
from app.modules.college_admin.lms_admin_service import (
    get_lms_operational_stats,
    update_lms_settings,
    upsert_course_mapping,
    upsert_publishing_policy,
)
from app.modules.college_admin.reports_admin_schemas import ReportExportCreate, ReportGenerateRequest
from app.modules.college_admin.reports_admin_service import (
    create_report_export,
    download_report_export,
    generate_report,
    get_dashboard_analytics,
    list_report_definitions,
)
from app.modules.lms.enums import MaterialPublishState
from app.modules.lms.models import AssignmentRule, LearningMaterial
from app.modules.tenants.models import Tenant


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
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed_admin(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College P8 {suffix}", code=f"p8_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+p8+{suffix}@example.com",
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
    return tenant, user, scope


@pytest.mark.anyio
async def test_lms_settings_and_mapping(db_ready):
    _, user, scope = await _seed_admin(uuid4().hex[:6])
    updated = await update_lms_settings(scope, user, LmsSettingsUpdate(quiz_enabled=False, moderation_required=True))
    assert updated.quiz_enabled is False
    assert updated.moderation_required is True
    mapping = await upsert_course_mapping(
        scope,
        user,
        LmsCourseMappingUpsert(course_id="c1", course_code="CS101", lms_course_key="lms-cs101"),
    )
    assert mapping.course_code == "CS101"
    other_tenant = Tenant(name="Other", code="other_p8")
    await other_tenant.insert()
    isolated = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, other_tenant.id)).count()
    assert isolated == 0


@pytest.mark.anyio
async def test_lms_stats_from_authoritative_collections(db_ready):
    tenant, user, scope = await _seed_admin(uuid4().hex[:6])
    faculty = User(
        email=f"faculty+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await faculty.insert()
    await LearningMaterial(
        tenant_id=tenant.id,
        faculty_user_id=faculty.id,
        course_id="c1",
        course_code="CS101",
        title="Syllabus",
        file_id="f1",
        storage_key="k1",
        file_name="s.pdf",
        mime_type="application/pdf",
        size_bytes=100,
        publish_state=MaterialPublishState.PUBLISHED,
    ).insert()
    stats = await get_lms_operational_stats(scope)
    assert stats.materials_total == 1
    assert stats.materials_published == 1


@pytest.mark.anyio
async def test_publishing_policy_updates_assignment_rule(db_ready):
    tenant, user, scope = await _seed_admin(uuid4().hex[:6])
    await upsert_publishing_policy(
        scope,
        user,
        LmsPublishingPolicyUpsert(late_penalty_percent=5.0, allowed_extensions=[".pdf"]),
    )
    rule = await AssignmentRule.find_one(Eq(AssignmentRule.tenant_id, tenant.id))
    assert rule is not None
    assert rule.late_penalty_percent == 5.0
    assert rule.allowed_extensions == [".pdf"]


@pytest.mark.anyio
async def test_report_generation_and_export(db_ready):
    _, user, scope = await _seed_admin(uuid4().hex[:6])
    defs = await list_report_definitions(scope)
    assert any(d.report_key == "attendance" for d in defs)
    job = await generate_report(scope, user, ReportGenerateRequest(report_key="attendance"))
    assert job.status.value == "completed"
    assert job.snapshot_id is not None
    export = await create_report_export(scope, user, ReportExportCreate(job_id=job.job_id))
    if export.download_token:
        payload = await download_report_export(scope, user, export.download_token)
        assert payload["export_id"] == export.export_id
        assert "attendance" in payload["payload"] or "payload" in payload


@pytest.mark.anyio
async def test_dashboard_analytics_tenant_scoped(db_ready):
    _, user, scope = await _seed_admin(uuid4().hex[:6])
    dash = await get_dashboard_analytics(scope)
    assert dash.academic_year_label is not None
    assert dash.pending_approvals >= 0


@pytest.mark.anyio
async def test_report_permission_denied_for_restricted_role(db_ready):
    tenant = Tenant(name="Restricted", code="restr_p8")
    await tenant.insert()
    user = User(
        email=f"dept+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dept",
        role=Role.DEPARTMENT_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.DEPARTMENT_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.DEPARTMENT_ADMIN),
    )
    with pytest.raises(AppError) as exc:
        await generate_report(scope, user, ReportGenerateRequest(report_key="finance"))
    assert exc.value.status_code == 403