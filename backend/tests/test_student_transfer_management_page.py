"""Student transfer management page."""

from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.student_admin_models import StudentRecord, StudentLifecycleStatus, StudentTransfer, TransferStatus
from app.modules.college_admin.schemas import StudentTransferRequestCreate
from app.modules.college_admin.student_transfer_management_page_service import (
    create_student_transfer_request,
    get_student_transfer_create_page,
    get_student_transfer_management_page,
)
from app.modules.department_admin.models import (
    DepartmentRequestStatus,
    DepartmentSectionTransferRequest,
    SectionTransferScenario,
)
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


@pytest.mark.anyio
async def test_transfer_management_page_merges_requests(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College TRF {suffix}", code=f"trf_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+trf+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    dept = InstitutionDepartment(tenant_id=tenant.id, name="Civil", department_code="CIV")
    await dept.insert()
    central_id = dept.central_department_id or dept.id

    student = User(
        email=f"student+trf+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Meera Das",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number="23CE0225",
        programme_code="CIV",
        section_code="A",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
        department_id=dept.id,
    )
    await record.insert()

    section_req = DepartmentSectionTransferRequest(
        tenant_id=tenant.id,
        institution_department_id=dept.id,
        central_department_id=central_id,
        student_user_id=student.id,
        from_section_code="A",
        to_section_code="B",
        from_batch_label="2023 batch",
        to_batch_label="2023 batch",
        programme_code="CIV",
        to_programme_code="MECH",
        reason="Interest change",
        status=DepartmentRequestStatus.PENDING,
        requested_by=admin.id,
        transfer_scenario=SectionTransferScenario.CROSS_DEPARTMENT,
    )
    await section_req.insert()

    programme_transfer = StudentTransfer(
        tenant_id=tenant.id,
        user_id=student.id,
        from_programme_code="CIV",
        to_programme_code="MECH",
        reason="Interest change",
        status=TransferStatus.REQUESTED,
        metadata={"transfer_kind": "programme", "from_section_code": "A", "to_section_code": "A"},
    )
    await programme_transfer.insert()

    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    page = await get_student_transfer_management_page(scope)
    assert page.page_title == "Student Transfer Management"
    assert len(page.transfer_rows) >= 2
    assert any("Meera" in row.student_name for row in page.transfer_rows)
    key = page.transfer_rows[0].request_key
    detail = await get_student_transfer_management_page(scope, selected_request_key=key)
    assert detail.review_reason
    assert detail.approval_steps
    assert page.new_transfer_href.endswith("/student-transfer-create")


@pytest.mark.anyio
async def test_create_student_transfer_request(db_ready):
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"College TRF2 {suffix}", code=f"trf2_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+trf2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"student2+trf+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Arjun Rao",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number="23ME0199",
        programme_code="MECH",
        section_code="B",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    await record.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )

    create_page = await get_student_transfer_create_page(scope)
    assert any(opt.value == str(record.id) for opt in create_page.student_options)

    result = await create_student_transfer_request(
        scope,
        StudentTransferRequestCreate(
            student_record_id=str(record.id),
            transfer_type="programme",
            to_programme_code="CIV",
            reason="Branch change request",
            effective_semester="Semester 3",
        ),
    )
    assert result.request_key.startswith("student:")
    page = await get_student_transfer_management_page(scope, selected_request_key=result.request_key)
    assert any(row.student_name == "Arjun Rao" for row in page.transfer_rows)