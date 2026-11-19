"""Examination cell phase 2 — assessment configuration and timetables."""

from datetime import timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.operations_ext_models import InstitutionFacility
from app.modules.examinations.exam_cell_assessment_enums import ExamAssessmentComponentKind
from app.modules.examinations.exam_cell_assessment_schemas import ExamAssessmentComponentInput, ExamAssessmentConfigCreate
from app.modules.examinations.exam_cell_assessment_service import create_assessment_config
from app.modules.examinations.exam_cell_assessment_validation import validate_assessment_components
from app.modules.examinations.exam_cell_enums import ExamSessionType
from app.modules.examinations.exam_cell_schemas import ExamSessionAcademicScopeInput, ExamSessionCreate
from app.modules.examinations.exam_cell_session_service import create_exam_session
from app.modules.examinations.exam_cell_timetable_schemas import ExamTimetableCreate, ExamTimetableEntryCreate
from app.modules.examinations.exam_cell_timetable_service import (
    add_timetable_entry,
    create_exam_timetable,
    publish_exam_timetable,
    submit_exam_timetable,
    validate_exam_timetable,
)
from app.modules.examinations.semester_examination_models import ExaminationCentre
from app.modules.students.curriculum_models import CourseCatalogReference
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


def _scope(user: User) -> AccessScope:
    return AccessScope(
        role=user.role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(user.role),
    )


def _components(weight_cia: float = 20, weight_end: float = 80) -> list[ExamAssessmentComponentInput]:
    return [
        ExamAssessmentComponentInput(
            code="CIA",
            name="Continuous Internal Assessment",
            assessment_type=ExamAssessmentComponentKind.CIA,
            max_marks=50,
            weight_percent=weight_cia,
            passing_marks=20,
        ),
        ExamAssessmentComponentInput(
            code="ESE",
            name="End Semester Examination",
            assessment_type=ExamAssessmentComponentKind.END_SEMESTER,
            max_marks=100,
            weight_percent=weight_end,
            passing_marks=40,
        ),
    ]


async def _seed(suffix: str) -> tuple[User, AccessScope, str]:
    tenant = Tenant(name=f"ExamP2 {suffix}", code=f"exp2_{suffix}")
    await tenant.insert()
    user = User(
        email=f"examcell+p2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Examination Officer",
        role=Role.EXAMINATION_CELL,
        tenant_id=tenant.id,
    )
    student_role = User(
        email=f"student+p2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await user.insert()
    await student_role.insert()
    scope = _scope(user)

    await CourseCatalogReference(
        tenant_id=tenant.id,
        programme_code="BTECH",
        academic_year_label="2025-26",
        semester_label="Odd",
        course_id=f"c_{suffix}",
        course_code="CSE101",
        credit_units=4,
    ).insert()
    await ExaminationCentre(
        tenant_id=tenant.id,
        centre_code="MAIN",
        name="Main Block",
        room_labels=["HALL-A", "HALL-B"],
    ).insert()
    await InstitutionFacility(
        tenant_id=tenant.id,
        facility_id=f"lab_{suffix}",
        name="CS Lab",
        facility_type="laboratory",
        capacity=60,
    ).insert()

    now = utcnow()
    session = await create_exam_session(
        scope,
        user,
        ExamSessionCreate(
            session_code=f"P2-{suffix}",
            name="Phase 2 Session",
            examination_type=ExamSessionType.REGULAR,
            academic_year_label="2025-26",
            semester_label="Odd",
            season_id=f"season_{suffix}",
            registration_start_at=now,
            registration_end_at=now + timedelta(days=5),
            examination_start_at=now + timedelta(days=10),
            examination_end_at=now + timedelta(days=20),
            academic_scope=ExamSessionAcademicScopeInput(department_codes=["CSE"]),
        ),
    )
    return user, scope, session.id


@pytest.mark.asyncio
async def test_phase2_permissions(db_ready):
    perms = permissions_for_role(Role.EXAMINATION_CELL)
    assert Permission.EXAMINATION_CELL_ASSESSMENT_MANAGE in perms
    assert Permission.EXAMINATION_CELL_TIMETABLE_PUBLISH in perms


@pytest.mark.asyncio
async def test_assessment_weightage_validation(db_ready):
    suffix = uuid4().hex[:8]
    user, scope, _ = await _seed(suffix)
    with pytest.raises(AppError) as bad_weight:
        await create_assessment_config(
            scope,
            user,
            ExamAssessmentConfigCreate(
                config_code=f"CFG-{suffix}",
                title="Invalid Weightage",
                programme_code="BTECH",
                semester_label="Odd",
                academic_year_label="2025-26",
                course_code="CSE101",
                components=_components(weight_cia=30, weight_end=60),
            ),
        )
    assert bad_weight.value.code == "WEIGHTAGE_MISMATCH"

    created = await create_assessment_config(
        scope,
        user,
        ExamAssessmentConfigCreate(
            config_code=f"CFG-OK-{suffix}",
            title="Valid Configuration",
            programme_code="BTECH",
            semester_label="Odd",
            academic_year_label="2025-26",
            course_code="CSE101",
            components=_components(),
        ),
    )
    assert len(created.components) == 2


@pytest.mark.asyncio
async def test_invalid_marks_component(db_ready):
    with pytest.raises(AppError):
        validate_assessment_components(
            [
                ExamAssessmentComponentInput(
                    code="BAD",
                    name="Bad",
                    assessment_type=ExamAssessmentComponentKind.THEORY,
                    max_marks=10,
                    weight_percent=100,
                    passing_marks=20,
                )
            ]
        )


@pytest.mark.asyncio
async def test_timetable_conflicts_and_publish_flow(db_ready):
    suffix = uuid4().hex[:8]
    user, scope, session_id = await _seed(suffix)
    timetable = await create_exam_timetable(
        scope,
        user,
        ExamTimetableCreate(exam_session_id=session_id, title="November Exams"),
    )
    timetable_oid = timetable.id
    from app.common.ids import to_object_id

    t_oid = to_object_id(timetable_oid, "timetable")
    start = utcnow() + timedelta(days=11)
    end = start + timedelta(hours=3)
    entry_base = {
        "course_code": "CSE101",
        "programme_code": "BTECH",
        "batch_label": "2023",
        "section": "A",
        "scheduled_start": start,
        "scheduled_end": end,
        "centre_code": "MAIN",
        "room_label": "HALL-A",
    }
    await add_timetable_entry(
        scope,
        user,
        t_oid,
        ExamTimetableEntryCreate(entry_code=f"E1-{suffix}", **entry_base),
    )
    with pytest.raises(AppError) as room_conflict:
        await add_timetable_entry(
            scope,
            user,
            t_oid,
            ExamTimetableEntryCreate(
                entry_code=f"E2-{suffix}",
                **{**entry_base, "scheduled_start": start + timedelta(minutes=30), "section": "B"},
            ),
        )
    assert room_conflict.value.code == "TIMETABLE_CONFLICT"

    validation = await validate_exam_timetable(scope, t_oid)
    assert validation.conflict_count == 0

    await submit_exam_timetable(scope, user, t_oid)
    from app.modules.examinations.exam_cell_timetable_service import approve_exam_timetable
    from app.modules.examinations.exam_cell_timetable_schemas import ExamTimetableApprovalRequest

    await approve_exam_timetable(scope, user, t_oid, ExamTimetableApprovalRequest(note="ok"))
    published = await publish_exam_timetable(scope, user, t_oid)
    assert published.published_version == 1


@pytest.mark.asyncio
async def test_unauthorized_student_cannot_create_assessment(db_ready):
    suffix = uuid4().hex[:8]
    user, _, _ = await _seed(suffix)
    student = await User.find_one({"email": f"student+p2+{suffix}@example.com"})
    assert student is not None
    student_scope = _scope(student)
    with pytest.raises(AppError):
        await create_assessment_config(
            student_scope,
            student,
            ExamAssessmentConfigCreate(
                config_code=f"STU-{suffix}",
                title="Should fail",
                semester_label="Odd",
                academic_year_label="2025-26",
                components=_components(),
            ),
        )