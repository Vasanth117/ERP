"""Hostel Admin phase 6 — communication and reports."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.hostel.communication_schemas import AnnouncementCreate, AnnouncementTransition, AudiencePreviewRequest
from app.modules.hostel.communication_service import create_announcement, preview_audience, transition_announcement
from app.modules.hostel.reports_schemas import ReportExportRequest, ReportRunRequest
from app.modules.hostel.reports_service import export_report, report_catalog, run_report
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


async def _seed():
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"H P6 {suffix}", code=f"hp6_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"ha6+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Hostel Admin",
        role=Role.HOSTEL_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = AccessScope(
        user_id=admin.id,
        tenant_id=tenant.id,
        role=Role.HOSTEL_ADMIN,
        effective_permissions=permissions_for_role(Role.HOSTEL_ADMIN),
    )
    return tenant, scope


@pytest.mark.anyio
async def test_announcement_publish_and_report_export(db_ready) -> None:
    _, scope = await _seed()
    preview = await preview_audience(scope, {"all_residents": True})
    assert preview.recipient_count == 0
    ann = await create_announcement(
        scope,
        AnnouncementCreate(
            announcement_code=f"ANN_{uuid4().hex[:6]}",
            title="Welcome",
            body="Hostel notice body",
            category="general",
            audience={"all_residents": True},
        ),
    )
    published = await transition_announcement(scope, ann.announcement_code, AnnouncementTransition(action="publish"))
    assert published.status.value == "published"
    catalog = await report_catalog(scope)
    assert any(c.report_key == "occupancy_overview" for c in catalog)
    data = await run_report(scope, ReportRunRequest(report_key="occupancy_overview", filters={}))
    assert data.row_count >= 0
    export = await export_report(scope, ReportExportRequest(report_key="occupancy_overview", filters={}))
    assert export.status == "completed"