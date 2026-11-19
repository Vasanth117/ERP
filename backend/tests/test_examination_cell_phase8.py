"""Examination cell phase 8 — notifications and analytics."""

from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_notification_enums import ExamNotificationEvent
from app.modules.examinations.exam_cell_notification_models import (
    ExamNotificationDeliveryLog,
    ExamNotificationEventRecord,
)
from app.modules.examinations.exam_cell_notification_schemas import ExamManualNotificationRequest
from app.modules.examinations.exam_cell_notification_service import (
    emit_exam_notification,
    run_notification_batch,
    send_manual_notification,
)
from app.modules.examinations.exam_cell_report_schemas import ExamReportFilters, ExamReportGenerateBody
from app.modules.examinations.exam_cell_report_service import (
    generate_report_export,
    get_report_job,
    get_report_snapshot,
    list_report_catalog,
)
from app.modules.messaging.outbox_models import DomainOutboxEvent
from app.modules.tenants.models import Tenant
from test_examination_cell_phase6 import _seed_published_session


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


def _scope(user: User) -> AccessScope:
    return AccessScope(
        role=user.role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(user.role),
    )


@pytest.mark.asyncio
async def test_phase8_permissions(db_ready):
    perms = permissions_for_role(Role.EXAMINATION_CELL)
    assert Permission.EXAMINATION_CELL_NOTIFICATION_MANAGE in perms
    assert Permission.EXAMINATION_CELL_REPORT_EXPORT in perms


@pytest.mark.asyncio
async def test_notification_dedupe_and_delivery(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, session_id, _ = await _seed_published_session(suffix)
    dedupe = f"test_dup_{suffix}"
    record = await emit_exam_notification(
        exam_user.tenant_id,
        event_type=ExamNotificationEvent.RESULT_PUBLISHED,
        recipient_user_id=student.id,
        dedupe_key=dedupe,
        template_kwargs={"session_name": "Mid Exam"},
    )
    assert record is not None
    dup = await emit_exam_notification(
        exam_user.tenant_id,
        event_type=ExamNotificationEvent.RESULT_PUBLISHED,
        recipient_user_id=student.id,
        dedupe_key=dedupe,
        template_kwargs={"session_name": "Mid Exam"},
    )
    assert dup is None
    stats = await run_notification_batch(scope)
    assert stats["processed"] >= 1
    deliveries = await ExamNotificationDeliveryLog.find(
        ExamNotificationDeliveryLog.tenant_id == exam_user.tenant_id,
        ExamNotificationDeliveryLog.event_record_id == record.event_record_id,
    ).to_list()
    assert any(d.status == "sent" for d in deliveries)
    outbox = await DomainOutboxEvent.find(DomainOutboxEvent.tenant_id == exam_user.tenant_id).to_list()
    assert outbox


@pytest.mark.asyncio
async def test_restricted_incident_notification_recipient(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, _, _ = await _seed_published_session(suffix)
    with pytest.raises(AppError) as exc:
        await send_manual_notification(
            scope,
            exam_user,
            ExamManualNotificationRequest(
                event_type=ExamNotificationEvent.INCIDENT_WORKFLOW,
                recipient_user_id=str(student.id),
                template_kwargs={"summary": "Investigation opened"},
                restricted=True,
            ),
        )
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.asyncio
async def test_report_snapshot_and_export(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, _, session_id, _ = await _seed_published_session(suffix)
    catalog = await list_report_catalog(scope)
    assert any(c.report_type == "registration_statistics" for c in catalog)
    filters = ExamReportFilters(exam_session_id=session_id)
    snap = await get_report_snapshot(scope, "registration_statistics", filters)
    assert snap.row_count >= 0
    job = await generate_report_export(
        scope,
        exam_user,
        ExamReportGenerateBody(
            report_type="session_summary",
            filters=filters,
            output_format="json",
            idempotency_key=f"export_{suffix}",
        ),
    )
    assert job.status == "completed"
    job2 = await generate_report_export(
        scope,
        exam_user,
        ExamReportGenerateBody(
            report_type="session_summary",
            filters=filters,
            output_format="json",
            idempotency_key=f"export_{suffix}",
        ),
    )
    assert job2.job_id == job.job_id


@pytest.mark.asyncio
async def test_cross_tenant_report_isolation(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, _, session_id, _ = await _seed_published_session(suffix)
    job = await generate_report_export(
        scope,
        exam_user,
        ExamReportGenerateBody(report_type="session_summary", filters=ExamReportFilters(exam_session_id=session_id)),
    )
    other = Tenant(name=f"Other {suffix}", code=f"oth_{suffix}")
    await other.insert()
    outsider = User(
        email=f"outsider+p8+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Outsider",
        role=Role.EXAMINATION_CELL,
        tenant_id=other.id,
    )
    await outsider.insert()
    with pytest.raises(AppError) as exc:
        await get_report_job(_scope(outsider), job.job_id)
    assert exc.value.code == "NOT_FOUND"