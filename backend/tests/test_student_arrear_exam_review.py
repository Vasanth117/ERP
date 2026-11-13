"""Student phase 8 — arrear/backlog and exam review."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.examinations.arrear_examination_models import ArrearEligibilityRecord, SupplementaryExaminationSeason
from app.modules.examinations.exam_review_models import ExaminationReviewWindow
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus
from app.modules.examinations.examination_registration_models import ExaminationFeePayment
from app.modules.examinations.result_publication_models import SemesterResultSubjectMark
from app.modules.students.arrear_backlog_schemas import SupplementaryRegistrationInput
from app.modules.students.arrear_backlog_service import (
    get_arrear_subjects,
    get_backlog_summary,
    register_supplementary,
)
from app.modules.students.exam_review_schemas import ReviewRequestSubmitInput
from app.modules.students.exam_review_service import submit_revaluation
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
        await connect_redis()
    except Exception as exc:
        pytest.skip(f"Dependencies not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed(suffix: str) -> tuple[Tenant, User, AccessScope, str, str]:
    tenant = Tenant(name="College", code=f"s8_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    user = User(
        email=f"s8+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.STUDENT,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    now = datetime.now(timezone.utc)
    sup_id = f"sup-{uuid4().hex[:8]}"
    season_id = f"season-{uuid4().hex[:8]}"
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    await SemesterResultSubjectMark(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        course_code="CSE101",
        pass_fail="fail",
        published=True,
        published_at=now,
    ).insert()
    await SupplementaryExaminationSeason(
        tenant_id=tenant.id,
        supplementary_season_id=sup_id,
        title="Supplementary",
        academic_year_label="2025-26",
        semester_label="Odd",
        registration_open_at=now - timedelta(hours=1),
        registration_close_at=now + timedelta(days=3),
        fee_required=True,
        fee_amount=200,
        fee_code="supplementary_exam_fee",
    ).insert()
    await ArrearEligibilityRecord(
        tenant_id=tenant.id,
        student_user_id=user.id,
        supplementary_season_id=sup_id,
        eligible=True,
        arrear_course_codes=["CSE101"],
        published=True,
        published_at=now,
    ).insert()
    await ExaminationFeePayment(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=sup_id,
        fee_code="supplementary_exam_fee",
        amount=200,
        status=ExaminationFeePaymentStatus.PAID,
        verified_at=now,
    ).insert()
    await ExaminationReviewWindow(
        tenant_id=tenant.id,
        season_id=season_id,
        review_type="revaluation",
        application_open_at=now - timedelta(hours=1),
        application_close_at=now + timedelta(days=2),
        fee_code="revaluation_fee",
        fee_amount=100,
    ).insert()
    await SemesterResultSubjectMark(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        course_code="CSE101",
        pass_fail="fail",
        total_obtained=30,
        total_max=100,
        published=True,
        published_at=now,
    ).insert()
    return tenant, user, scope, sup_id, season_id


@pytest.mark.asyncio
async def test_arrear_and_registration(db_ready):
    _, user, scope, sup_id, _ = await _seed("a")
    subjects = await get_arrear_subjects(scope, user)
    assert subjects[0].course_code == "CSE101"
    summary = await get_backlog_summary(scope, user)
    assert summary.pending_count >= 1
    reg = await register_supplementary(
        scope, user, SupplementaryRegistrationInput(supplementary_season_id=sup_id, course_code="CSE101")
    )
    assert reg.status == "submitted"
    with pytest.raises(AppError) as exc:
        await register_supplementary(
            scope, user, SupplementaryRegistrationInput(supplementary_season_id=sup_id, course_code="CSE101")
        )
    assert exc.value.code == "DUPLICATE_REGISTRATION"


@pytest.mark.asyncio
async def test_revaluation_submit(db_ready):
    _, user, scope, _, season_id = await _seed("b")
    req = await submit_revaluation(
        scope,
        user,
        ReviewRequestSubmitInput(season_id=season_id, course_code="CSE101", reason="Requesting revaluation of paper"),
    )
    assert req.request_type == "revaluation"
