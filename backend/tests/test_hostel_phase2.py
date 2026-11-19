"""Hostel Admin phase 2 — applications and allocations."""

from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus
from app.modules.hostel.allocation_schemas import AllocationCreate
from app.modules.hostel.allocation_service import create_allocation
from app.modules.hostel.application_schemas import AllocationOfferCreate, HostelApplicationReviewInput, HostelApplicationSubmit, OfferResponse
from app.modules.hostel.application_service import review_application, submit_application
from app.modules.hostel.hostel_enums import HostelApplicationStatus
from app.modules.hostel.infrastructure_schemas import (
    HostelBedPortalCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelRoomCreate,
    InstitutionHostelCreate,
)
from app.modules.hostel.infrastructure_service import create_bed, create_block, create_building, create_hostel, create_room
from app.modules.hostel.waiting_list_service import issue_allocation_offer, respond_to_offer
from app.modules.students.models import StudentAcademicRecord, StudentProfile
from app.modules.students.enums import StudentEnrollmentStatus
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


async def _seed(suffix: str) -> tuple[Tenant, AccessScope, User, User]:
    tenant = Tenant(name=f"H P2 {suffix}", code=f"hp2_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"ha+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Hostel Admin",
        role=Role.HOSTEL_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"st+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    await StudentProfile(tenant_id=tenant.id, user_id=student.id, student_id=f"SID{suffix}").insert()
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        academic_year_label="2025",
        semester_label="odd",
        enrollment_status=StudentEnrollmentStatus.ACTIVE,
    ).insert()
    admin_scope = AccessScope(
        role=Role.HOSTEL_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.HOSTEL_ADMIN),
    )
    student_scope = AccessScope(
        role=Role.STUDENT,
        user_id=student.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    return tenant, admin_scope, admin, student, student_scope


@pytest.mark.anyio
async def test_application_submit_and_approve_allocate(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, admin_scope, _, student, student_scope = await _seed(suffix)
    hcode = f"H{suffix}"
    bcode = f"B{suffix}"
    await create_hostel(admin_scope, InstitutionHostelCreate(hostel_code=hcode, name="Hostel", configured_capacity=5))
    await create_building(admin_scope, HostelBuildingCreate(hostel_code=hcode, building_code=bcode, name="Main"))
    await create_block(admin_scope, HostelBlockCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", name="A"))
    await create_room(
        admin_scope,
        HostelRoomCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", room_code="101", bed_capacity=2),
    )
    bed_id = f"bed-{suffix}"
    await create_bed(
        admin_scope,
        HostelBedPortalCreate(hostel_code=hcode, bed_id=bed_id, building_code=bcode, block_code="BLK1", room_code="101", bed_label="A"),
    )
    app = await submit_application(
        student_scope,
        student,
        HostelApplicationSubmit(academic_year_label="2025", preferred_hostel_code=hcode, reason="Need hostel"),
    )
    reviewed = await review_application(
        admin_scope,
        HostelApplicationReviewInput(application_id=app.application_id, decision=HostelApplicationStatus.APPROVED),
    )
    assert reviewed.status == HostelApplicationStatus.APPROVED
    alloc = await create_allocation(
        admin_scope,
        AllocationCreate(
            student_user_id=str(student.id),
            application_id=app.application_id,
            hostel_code=hcode,
            bed_id=bed_id,
        ),
    )
    assert alloc.bed_id == bed_id
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant.id), Eq(HostelBed.bed_id, bed_id))
    assert bed is not None
    assert bed.status == HostelBedStatus.ALLOCATED
    with pytest.raises(AppError) as exc:
        await create_allocation(
            admin_scope,
            AllocationCreate(
                student_user_id=str(student.id),
                application_id=app.application_id,
                hostel_code=hcode,
                bed_id=bed_id,
            ),
        )
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_duplicate_bed_allocation_prevented(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, admin_scope, _, s1, _ = await _seed(suffix)
    s2 = User(
        email=f"s2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student 2",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await s2.insert()
    await StudentProfile(tenant_id=tenant.id, user_id=s2.id).insert()
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=s2.id,
        academic_year_label="2025",
        semester_label="odd",
        enrollment_status=StudentEnrollmentStatus.ACTIVE,
    ).insert()
    hcode = f"H{suffix}"
    bcode = f"B{suffix}"
    await create_hostel(admin_scope, InstitutionHostelCreate(hostel_code=hcode, name="Hostel", configured_capacity=5))
    await create_building(admin_scope, HostelBuildingCreate(hostel_code=hcode, building_code=bcode, name="Main"))
    await create_block(admin_scope, HostelBlockCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", name="A"))
    await create_room(
        admin_scope,
        HostelRoomCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", room_code="101", bed_capacity=2),
    )
    bed_id = f"bed-{suffix}"
    await create_bed(
        admin_scope,
        HostelBedPortalCreate(hostel_code=hcode, bed_id=bed_id, building_code=bcode, block_code="BLK1", room_code="101", bed_label="A"),
    )
    await create_allocation(
        admin_scope,
        AllocationCreate(student_user_id=str(s1.id), hostel_code=hcode, bed_id=bed_id),
    )
    with pytest.raises(AppError) as exc:
        await create_allocation(
            admin_scope,
            AllocationCreate(student_user_id=str(s2.id), hostel_code=hcode, bed_id=bed_id),
        )
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_waitlist_offer_and_accept(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, admin_scope, _, student, student_scope = await _seed(suffix)
    hcode = f"H{suffix}"
    bcode = f"B{suffix}"
    await create_hostel(admin_scope, InstitutionHostelCreate(hostel_code=hcode, name="Hostel", configured_capacity=5))
    await create_building(admin_scope, HostelBuildingCreate(hostel_code=hcode, building_code=bcode, name="Main"))
    await create_block(admin_scope, HostelBlockCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", name="A"))
    await create_room(
        admin_scope,
        HostelRoomCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", room_code="101", bed_capacity=1),
    )
    bed_id = f"bed-{suffix}"
    await create_bed(
        admin_scope,
        HostelBedPortalCreate(hostel_code=hcode, bed_id=bed_id, building_code=bcode, block_code="BLK1", room_code="101", bed_label="A"),
    )
    app = await submit_application(student_scope, student, HostelApplicationSubmit(academic_year_label="2025", preferred_hostel_code=hcode))
    await review_application(
        admin_scope,
        HostelApplicationReviewInput(application_id=app.application_id, decision=HostelApplicationStatus.WAITLISTED),
    )
    offer = await issue_allocation_offer(
        admin_scope,
        AllocationOfferCreate(application_id=app.application_id, bed_id=bed_id, response_hours=24),
    )
    result = await respond_to_offer(student_scope, student, OfferResponse(offer_id=offer["offer_id"], accept=True))
    assert result["allocation_id"]