"""Hostel Admin phase 3 — residents and visitors."""

from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus
from app.modules.hostel.allocation_schemas import AllocationCreate
from app.modules.hostel.allocation_service import create_allocation
from app.modules.hostel.infrastructure_schemas import (
    HostelBedPortalCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelRoomCreate,
    InstitutionHostelCreate,
)
from app.modules.hostel.infrastructure_service import create_bed, create_block, create_building, create_hostel, create_room
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus
from app.modules.hostel.resident_schemas import ResidentCheckinInput, ResidentCheckoutInput
from app.modules.hostel.resident_service import check_in_resident, check_out_resident
from app.modules.hostel.visitor_schemas import VisitorApprovalInput, VisitorEntryInput, VisitorExitInput, VisitorRegisterInput
from app.modules.hostel.visitor_service import approve_visitor, record_visitor_entry, record_visitor_exit, register_visitor
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord, StudentProfile
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


async def _seed(suffix: str):
    tenant = Tenant(name=f"H P3 {suffix}", code=f"hp3_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"ha3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Hostel Admin",
        role=Role.HOSTEL_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"st3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    await StudentProfile(tenant_id=tenant.id, user_id=student.id, roll_number=f"R{suffix}").insert()
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        academic_year_label="2025",
        semester_label="odd",
        enrollment_status=StudentEnrollmentStatus.ACTIVE,
    ).insert()
    scope = AccessScope(
        role=Role.HOSTEL_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.HOSTEL_ADMIN),
    )
    return tenant, scope, student


@pytest.mark.anyio
async def test_resident_checkin_checkout(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student = await _seed(suffix)
    hcode, bcode = f"H{suffix}", f"B{suffix}"
    await create_hostel(scope, InstitutionHostelCreate(hostel_code=hcode, name="Hostel", configured_capacity=3))
    await create_building(scope, HostelBuildingCreate(hostel_code=hcode, building_code=bcode, name="Main"))
    await create_block(scope, HostelBlockCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", name="A"))
    await create_room(scope, HostelRoomCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", room_code="101", bed_capacity=1))
    bed_id = f"bed-{suffix}"
    await create_bed(scope, HostelBedPortalCreate(hostel_code=hcode, bed_id=bed_id, building_code=bcode, block_code="BLK1", room_code="101", bed_label="A"))
    alloc = await create_allocation(
        scope,
        AllocationCreate(student_user_id=str(student.id), hostel_code=hcode, bed_id=bed_id),
    )
    resident = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant.id), Eq(HostelResident.allocation_id, alloc.allocation_id))
    assert resident is not None
    assert resident.status == HostelResidentStatus.AWAITING_CHECKIN
    view = await check_in_resident(scope, ResidentCheckinInput(allocation_id=alloc.allocation_id, verify_student_user_id=str(student.id)))
    assert view.status == HostelResidentStatus.CHECKED_IN
    with pytest.raises(AppError) as exc:
        await check_in_resident(scope, ResidentCheckinInput(allocation_id=alloc.allocation_id))
    assert exc.value.status_code == 409
    out = await check_out_resident(scope, ResidentCheckoutInput(allocation_id=alloc.allocation_id))
    assert out.status == HostelResidentStatus.CHECKED_OUT
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant.id), Eq(HostelBed.bed_id, bed_id))
    assert bed is not None
    assert bed.status == HostelBedStatus.AVAILABLE


@pytest.mark.anyio
async def test_visitor_entry_exit(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student = await _seed(suffix)
    hcode, bcode = f"H{suffix}", f"B{suffix}"
    await create_hostel(scope, InstitutionHostelCreate(hostel_code=hcode, name="Hostel", configured_capacity=3))
    await create_building(scope, HostelBuildingCreate(hostel_code=hcode, building_code=bcode, name="Main"))
    await create_block(scope, HostelBlockCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", name="A"))
    await create_room(scope, HostelRoomCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", room_code="101", bed_capacity=1))
    bed_id = f"bed-{suffix}"
    await create_bed(scope, HostelBedPortalCreate(hostel_code=hcode, bed_id=bed_id, building_code=bcode, block_code="BLK1", room_code="101", bed_label="A"))
    alloc = await create_allocation(scope, AllocationCreate(student_user_id=str(student.id), hostel_code=hcode, bed_id=bed_id))
    await check_in_resident(scope, ResidentCheckinInput(allocation_id=alloc.allocation_id))
    visit = await register_visitor(
        scope,
        VisitorRegisterInput(resident_user_id=str(student.id), visitor_name="Parent Guest", purpose="Visit", walk_in=True),
    )
    if visit.status.value not in ("approved", "expected"):
        await approve_visitor(scope, VisitorApprovalInput(visit_id=visit.visit_id, approved=True))
    inside = await record_visitor_entry(scope, VisitorEntryInput(visit_id=visit.visit_id))
    assert inside.actual_entry_at is not None
    exited = await record_visitor_exit(scope, VisitorExitInput(visit_id=visit.visit_id))
    assert exited.status.value == "exited"
    with pytest.raises(AppError) as exc:
        await record_visitor_exit(scope, VisitorExitInput(visit_id=visit.visit_id))
    assert exc.value.status_code == 409