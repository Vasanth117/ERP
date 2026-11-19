"""Department Admin phase 3 — class structure and student administration."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.identity_schemas import InstitutionDepartmentCreate
from app.modules.college_admin.organization_service import create_institution_department
from app.modules.college_admin.student_admin_schemas import StudentRecordCreate
from app.modules.college_admin.student_admin_service import create_student_record
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.department_admin.class_management_service import (
    create_batch,
    create_section,
    update_section,
)
from app.modules.department_admin.models import DepartmentSetting, SectionTransferInitiator
from app.modules.department_admin.section_transfer_service import (
    review_section_transfer,
    submit_section_transfer,
)
from app.modules.department_admin.models import DepartmentSectionStatus
from app.modules.department_admin.phase3_schemas import (
    BatchCreate,
    SectionCreate,
    SectionTransferCreate,
    SectionTransferReview,
    SectionUpdate,
    StudentCorrectionCreate,
    StudentCorrectionReview,
    StudentDirectoryFilters,
)
from app.modules.department_admin.student_administration_service import (
    create_correction_request,
    list_students,
    review_correction_request,
)
from app.modules.tenants.models import Department, Tenant
from beanie.odm.operators.find.comparison import Eq


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


async def _seed(suffix: str) -> tuple[Tenant, Department, User, AccessScope, User, AccessScope]:
    tenant = Tenant(name=f"C {suffix}", code=f"p3_{suffix}", institution_email=f"i+{suffix}@ex.com")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    admin = User(
        email=f"ca+{suffix}@ex.com",
        hashed_password=hash_password("password1234567890"),
        full_name="CA",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    admin_scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    await create_institution_department(
        admin_scope,
        InstitutionDepartmentCreate(department_code="CSE", name="CSE", programme_codes=["BTECH-CSE"]),
    )
    dept_admin = User(
        email=f"da+{suffix}@ex.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dept Admin",
        role=Role.DEPARTMENT_ADMIN,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await dept_admin.insert()
    scope = AccessScope(
        role=Role.DEPARTMENT_ADMIN,
        user_id=dept_admin.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.DEPARTMENT_ADMIN),
    )
    student = await create_student_record(
        admin_scope,
        StudentRecordCreate(
            email=f"stu+{suffix}@ex.com",
            password="password1234567890",
            full_name="Student A",
            roll_number=f"R-{suffix}",
            department_id=str(dept.id),
            programme_code="BTECH-CSE",
            batch_label="2024",
            section_code="A",
        ),
    )
    student_user = await User.find_one(Eq(User.email, f"stu+{suffix}@ex.com"))
    assert student_user is not None
    student_scope = AccessScope(
        role=Role.STUDENT,
        user_id=student_user.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    return tenant, dept, dept_admin, scope, student_user, admin_scope, student_scope


@pytest.mark.anyio
async def test_batch_section_and_transfer(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, dept, dept_admin, scope, student_user, _, student_scope = await _seed(suffix)
    from app.modules.college_admin.identity_models import InstitutionDepartment

    institution = await InstitutionDepartment.find_one(Eq(InstitutionDepartment.central_department_id, dept.id))
    assert institution is not None
    await DepartmentSetting(
        tenant_id=tenant.id,
        institution_department_id=institution.id,
        setting_key="delegation_enabled",
        setting_value=True,
        category="governance",
    ).insert()
    batch = await create_batch(
        scope,
        dept_admin,
        BatchCreate(programme_code="BTECH-CSE", batch_label="2024", admission_year="2024"),
    )
    section_a = await create_section(
        scope,
        dept_admin,
        batch.batch_id,
        SectionCreate(section_code="A", name="Section A", capacity=2),
    )
    section_b = await create_section(
        scope,
        dept_admin,
        batch.batch_id,
        SectionCreate(section_code="B", name="Section B", capacity=2),
    )
    await update_section(
        scope,
        dept_admin,
        section_a.section_id,
        SectionUpdate(status=DepartmentSectionStatus.ACTIVE),
    )
    await update_section(
        scope,
        dept_admin,
        section_b.section_id,
        SectionUpdate(status=DepartmentSectionStatus.ACTIVE),
    )
    transfer = await submit_section_transfer(
        student_scope,
        student_user,
        SectionTransferCreate(
            student_user_id=str(student_user.id),
            from_section_code="A",
            to_section_code="B",
            batch_label="2024",
            programme_code="BTECH-CSE",
            reason="Balance sections",
        ),
        initiator=SectionTransferInitiator.STUDENT,
    )
    assert transfer.status.value == "pending"
    try:
        completed = await review_section_transfer(
            scope,
            dept_admin,
            transfer.request_id,
            SectionTransferReview(decision="approve"),
        )
    except AppError as exc:
        if exc.code == "TRANSACTIONS_UNAVAILABLE":
            pytest.skip("MongoDB replica set required for transactional transfer")
        raise
    assert completed.status.value == "completed"
    record = await StudentRecord.find_one(Eq(StudentRecord.user_id, student_user.id))
    assert record is not None
    assert record.section_code == "B"


@pytest.mark.anyio
async def test_student_directory_and_correction(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, dept_admin, scope, student_user, _, _ = await _seed(suffix)
    page = await list_students(
        scope,
        dept_admin,
        pagination=Pagination(limit=20, offset=0),
        filters=StudentDirectoryFilters(programme_code="BTECH-CSE"),
    )
    assert page.total >= 1
    req = await create_correction_request(
        scope,
        dept_admin,
        StudentCorrectionCreate(
            student_user_id=str(student_user.id),
            field_name="roll_number",
            proposed_value=f"NEW-{suffix}",
            reason="Typo in roll number",
        ),
    )
    assert req.status.value == "pending"
    done = await review_correction_request(
        scope,
        dept_admin,
        req.request_id,
        StudentCorrectionReview(decision="approve"),
    )
    assert done.status.value == "completed"
    record = await StudentRecord.find_one(Eq(StudentRecord.user_id, student_user.id))
    assert record is not None
    assert record.roll_number == f"NEW-{suffix}"


@pytest.mark.anyio
async def test_forbidden_correction_field(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, dept_admin, scope, student_user, _, _ = await _seed(suffix)
    with pytest.raises(AppError) as exc:
        await create_correction_request(
            scope,
            dept_admin,
            StudentCorrectionCreate(
                student_user_id=str(student_user.id),
                field_name="admission_number",
                proposed_value="X",
                reason="Should not work",
            ),
        )
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_duplicate_section_code(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, dept_admin, scope, _, _, _ = await _seed(suffix)
    batch = await create_batch(
        scope,
        dept_admin,
        BatchCreate(programme_code="BTECH-CSE", batch_label="2025"),
    )
    await create_section(
        scope,
        dept_admin,
        batch.batch_id,
        SectionCreate(section_code="X", name="One"),
    )
    with pytest.raises(AppError) as exc:
        await create_section(
            scope,
            dept_admin,
            batch.batch_id,
            SectionCreate(section_code="X", name="Two"),
        )
    assert exc.value.status_code == 409