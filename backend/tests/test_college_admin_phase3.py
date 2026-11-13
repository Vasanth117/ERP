"""College Admin phase 3 — academic configuration and student administration."""

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
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_schemas import (
    AcademicYearCreate,
    CourseAdminCreate,
    ProgrammeCreate,
    RegulationUpsert,
)
from app.modules.college_admin.academic_config_service import (
    create_academic_year,
    create_course,
    list_academic_years,
    publish_academic_year,
    upsert_programme,
    upsert_regulation,
)
from app.common.ids import to_object_id
from app.modules.college_admin.student_admin_models import StudentRecord as AdminStudentRecord
from app.modules.college_admin.student_admin_schemas import (
    AdmissionCreate,
    EnrollmentAssign,
    StudentRecordCreate,
    TransferCreate,
)
from app.modules.college_admin.student_admin_service import (
    create_admission,
    create_student_record,
    enroll_student,
    process_transfer,
)
from app.modules.students.models import StudentEnrollment, StudentProfile
from app.modules.tenants.models import Department, Tenant


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
    tenant = Tenant(name=f"College P3 {suffix}", code=f"p3_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+p3+{suffix}@example.com",
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
async def test_academic_year_publish_syncs_context(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, scope = await _seed_admin(suffix)
    created = await create_academic_year(
        scope,
        AcademicYearCreate(year_code=f"2025-{suffix}", label=f"AY 2025 {suffix}", is_current=True),
    )
    await publish_academic_year(scope, to_object_id(created.year_id, "year_id"))
    ctx = await AcademicYearContext.find_one(Eq(AcademicYearContext.tenant_id, scope.tenant_id))
    assert ctx is not None
    assert ctx.is_current is True
    assert ctx.academic_year_label == created.label
    history = await list_academic_years(scope)
    assert len(history) == 1
    assert history[0].status.value == "published"


@pytest.mark.anyio
async def test_duplicate_academic_year_code(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, scope = await _seed_admin(suffix)
    code = f"DUP-{suffix}"
    await create_academic_year(scope, AcademicYearCreate(year_code=code, label="First"))
    with pytest.raises(AppError) as exc:
        await create_academic_year(scope, AcademicYearCreate(year_code=code, label="Second"))
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_programme_course_and_regulation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    prog = await upsert_programme(
        scope,
        ProgrammeCreate(programme_code="BTECH", name="B.Tech", department_id=str(dept.id), duration_semesters=8),
    )
    assert prog.programme_code == "BTECH"
    course = await create_course(
        scope,
        CourseAdminCreate(course_code="CS101", name="Intro CS", credit_units=4, department_id=str(dept.id)),
    )
    assert course.course_code == "CS101"
    reg = await upsert_regulation(
        scope,
        RegulationUpsert(scope_key="grading", rules={"min_pass": 40}),
    )
    assert reg.scope_key == "grading"


@pytest.mark.anyio
async def test_student_admission_record_duplicate_identifiers(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    dept = Department(tenant_id=tenant.id, name="ECE", code="ECE")
    await dept.insert()
    admission = await create_admission(
        scope,
        AdmissionCreate(
            admission_number=f"ADM-{suffix}",
            applicant_name="Applicant One",
            applicant_email=f"app+{suffix}@example.com",
            programme_code="BTECH",
            department_id=str(dept.id),
            batch_label="2025",
            academic_year_code="2025",
        ),
    )
    student = await create_student_record(
        scope,
        StudentRecordCreate(
            email=f"student+{suffix}@example.com",
            password="password1234567890",
            full_name="Student One",
            student_id=f"SID-{suffix}",
            roll_number=f"ROLL-{suffix}",
            admission_id=admission.admission_id,
            department_id=str(dept.id),
        ),
    )
    assert student.roll_number == f"ROLL-{suffix}"
    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, scope.tenant_id),
        Eq(StudentProfile.user_id, to_object_id(student.user_id, "user_id")),
    )
    assert profile is not None
    assert profile.student_id == f"SID-{suffix}"

    with pytest.raises(AppError) as dup_roll:
        await create_student_record(
            scope,
            StudentRecordCreate(
                email=f"student2+{suffix}@example.com",
                password="password1234567890",
                full_name="Student Two",
                roll_number=f"ROLL-{suffix}",
            ),
        )
    assert dup_roll.value.status_code == 409

    with pytest.raises(AppError) as dup_sid:
        await create_student_record(
            scope,
            StudentRecordCreate(
                email=f"student3+{suffix}@example.com",
                password="password1234567890",
                full_name="Student Three",
                student_id=f"SID-{suffix}",
            ),
        )
    assert dup_sid.value.status_code == 409


@pytest.mark.anyio
async def test_enrollment_duplicate_and_transfer(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    dept_a = Department(tenant_id=tenant.id, name="MECH", code="MECH")
    dept_b = Department(tenant_id=tenant.id, name="CIVIL", code="CIVIL")
    await dept_a.insert()
    await dept_b.insert()
    record = await create_student_record(
        scope,
        StudentRecordCreate(
            email=f"enroll+{suffix}@example.com",
            password="password1234567890",
            full_name="Enroll Student",
            department_id=str(dept_a.id),
            programme_code="BTECH",
        ),
    )
    enroll_payload = EnrollmentAssign(
        academic_year_label="2025",
        semester_label="Sem-1",
        course_id=str(tenant.id),
        course_code="ME101",
        course_name="Mechanics",
        section_code="A",
    )
    first = await enroll_student(scope, to_object_id(record.record_id, "record_id"), enroll_payload)
    assert "enrollment_id" in first
    with pytest.raises(AppError) as dup:
        await enroll_student(scope, to_object_id(record.record_id, "record_id"), enroll_payload)
    assert dup.value.status_code == 409

    transfer = await process_transfer(
        scope,
        to_object_id(record.record_id, "record_id"),
        TransferCreate(to_department_id=str(dept_b.id), to_programme_code="BTECH", reason="Department change"),
    )
    assert "transfer_id" in transfer
    updated = await AdminStudentRecord.get(to_object_id(record.record_id, "record_id"))
    assert updated is not None
    assert updated.department_id == dept_b.id
    count = await StudentEnrollment.find(Eq(StudentEnrollment.user_id, to_object_id(record.user_id, "user_id"))).count()
    assert count == 1


@pytest.mark.anyio
async def test_permission_denied_without_academic_manage(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, _ = await _seed_admin(suffix)
    faculty = User(
        email=f"faculty+p3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await faculty.insert()
    scope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    with pytest.raises(AppError) as exc:
        await create_academic_year(scope, AcademicYearCreate(year_code=f"NOPE-{suffix}", label="Nope"))
    assert exc.value.status_code == 403
    assert Permission.ACADEMIC_CONFIG_MANAGE not in scope.effective_permissions


@pytest.mark.anyio
async def test_tenant_isolation_student_record(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant_a, _, scope_a = await _seed_admin(f"a{suffix}")
    tenant_b, _, scope_b = await _seed_admin(f"b{suffix}")
    created = await create_student_record(
        scope_a,
        StudentRecordCreate(
            email=f"iso+{suffix}@example.com",
            password="password1234567890",
            full_name="Tenant A Student",
        ),
    )
    from app.modules.college_admin.student_admin_service import get_student_record

    with pytest.raises(AppError) as exc:
        await get_student_record(scope_b, to_object_id(created.record_id, "record_id"))
    assert exc.value.status_code == 404
    assert tenant_a.id != tenant_b.id
