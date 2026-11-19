"""Hostel Admin phase 1 — dashboard and infrastructure."""

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
from app.modules.college_admin.hostel_admin_models import HostelAllocation, HostelAllocationStatus, HostelBed, HostelBedStatus
from app.modules.hostel.dashboard_service import get_hostel_dashboard_overview
from app.modules.hostel.infrastructure_schemas import (
    HostelBedPortalCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelFloorCreate,
    HostelRoomCreate,
    InstitutionHostelCreate,
)
from app.modules.hostel.infrastructure_service import create_bed, create_block, create_building, create_floor, create_hostel, create_room
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


async def _seed_hostel_admin(suffix: str) -> tuple[Tenant, AccessScope, User]:
    tenant = Tenant(name=f"Hostel P1 {suffix}", code=f"h1_{suffix}")
    await tenant.insert()
    user = User(
        email=f"hostel+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Hostel Admin",
        role=Role.HOSTEL_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.HOSTEL_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.HOSTEL_ADMIN),
    )
    return tenant, scope, user


@pytest.mark.anyio
async def test_hostel_duplicate_code_prevented(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, _ = await _seed_hostel_admin(suffix)
    code = f"H{suffix}"
    await create_hostel(scope, InstitutionHostelCreate(hostel_code=code, name="Boys Hostel", configured_capacity=10))
    with pytest.raises(AppError) as exc:
        await create_hostel(scope, InstitutionHostelCreate(hostel_code=code, name="Duplicate", configured_capacity=5))
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_room_bed_capacity_validation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, _ = await _seed_hostel_admin(suffix)
    hcode = f"H{suffix}"
    bcode = f"B{suffix}"
    await create_hostel(scope, InstitutionHostelCreate(hostel_code=hcode, name="Hostel", configured_capacity=20))
    await create_building(scope, HostelBuildingCreate(hostel_code=hcode, building_code=bcode, name="Main"))
    await create_block(scope, HostelBlockCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", name="A"))
    with pytest.raises(AppError) as exc:
        await create_room(
            scope,
            HostelRoomCreate(
                hostel_code=hcode,
                building_code=bcode,
                block_code="BLK1",
                room_code="101",
                capacity=1,
                bed_capacity=2,
            ),
        )
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_hostel_configured_capacity_enforced(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, _ = await _seed_hostel_admin(suffix)
    hcode = f"H{suffix}"
    bcode = f"B{suffix}"
    await create_hostel(scope, InstitutionHostelCreate(hostel_code=hcode, name="Small Hostel", configured_capacity=1))
    await create_building(scope, HostelBuildingCreate(hostel_code=hcode, building_code=bcode, name="Main"))
    await create_block(scope, HostelBlockCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", name="A"))
    await create_room(
        scope,
        HostelRoomCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", room_code="101", bed_capacity=2),
    )
    await create_bed(
        scope,
        HostelBedPortalCreate(hostel_code=hcode, bed_id=f"bed1-{suffix}", building_code=bcode, block_code="BLK1", room_code="101", bed_label="A"),
    )
    with pytest.raises(AppError) as exc:
        await create_bed(
            scope,
            HostelBedPortalCreate(hostel_code=hcode, bed_id=f"bed2-{suffix}", building_code=bcode, block_code="BLK1", room_code="101", bed_label="B"),
        )
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_dashboard_occupancy_from_active_allocations(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, admin = await _seed_hostel_admin(suffix)
    hcode = f"H{suffix}"
    bcode = f"B{suffix}"
    await create_hostel(scope, InstitutionHostelCreate(hostel_code=hcode, name="Hostel", configured_capacity=5))
    await create_building(scope, HostelBuildingCreate(hostel_code=hcode, building_code=bcode, name="Main"))
    await create_block(scope, HostelBlockCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", name="A"))
    await create_floor(
        scope,
        HostelFloorCreate(hostel_code=hcode, building_code=bcode, floor_id="F1", floor_number=1, name="Ground"),
    )
    await create_room(
        scope,
        HostelRoomCreate(
            hostel_code=hcode,
            building_code=bcode,
            block_code="BLK1",
            room_code="101",
            floor_id="F1",
            bed_capacity=2,
        ),
    )
    bed_id = f"bed-{suffix}"
    await create_bed(
        scope,
        HostelBedPortalCreate(hostel_code=hcode, bed_id=bed_id, building_code=bcode, block_code="BLK1", room_code="101", bed_label="A"),
    )
    student = User(
        email=f"stu+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Resident",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant.id), Eq(HostelBed.bed_id, bed_id))
    assert bed is not None
    bed.status = HostelBedStatus.ALLOCATED
    await bed.save()
    await HostelAllocation(
        tenant_id=tenant.id,
        allocation_id=f"al-{suffix}",
        student_user_id=student.id,
        bed_id=bed_id,
        building_code=bcode.upper(),
        block_code="BLK1",
        room_code="101",
        bed_label="A",
        status=HostelAllocationStatus.ACTIVE,
    ).insert()

    overview = await get_hostel_dashboard_overview(scope, admin, hostel_code=hcode)
    assert overview.hostel_overview.total_beds == 1
    assert overview.hostel_overview.occupied_beds == 1
    assert overview.hostel_overview.available_beds == 0
    assert overview.hostel_overview.occupancy_percentage == 100.0
    assert overview.resident_overview.checked_in_residents == 1


@pytest.mark.anyio
async def test_unauthorized_student_denied(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, _ = await _seed_hostel_admin(suffix)
    student = User(
        email=f"stu2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    student_scope = AccessScope(
        role=Role.STUDENT,
        user_id=student.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    with pytest.raises(AppError) as exc:
        await create_hostel(student_scope, InstitutionHostelCreate(hostel_code=f"S{suffix}", name="No Access"))
    assert exc.value.status_code in (403, 401)


@pytest.mark.anyio
async def test_cross_tenant_isolation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant_a, scope_a, _ = await _seed_hostel_admin(suffix)
    tenant_b = Tenant(name=f"Other {suffix}", code=f"oth_{suffix}")
    await tenant_b.insert()
    user_b = User(
        email=f"hostel-b+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other Admin",
        role=Role.HOSTEL_ADMIN,
        tenant_id=tenant_b.id,
    )
    await user_b.insert()
    scope_b = AccessScope(
        role=Role.HOSTEL_ADMIN,
        user_id=user_b.id,
        tenant_id=tenant_b.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.HOSTEL_ADMIN),
    )
    hcode_a = f"HA{suffix}"
    hcode_b = f"HB{suffix}"
    await create_hostel(scope_a, InstitutionHostelCreate(hostel_code=hcode_a, name="Tenant A Hostel"))
    with pytest.raises(AppError) as exc:
        await create_building(
            scope_b,
            HostelBuildingCreate(hostel_code=hcode_a, building_code=f"B{suffix}", name="Illegal"),
        )
    assert exc.value.status_code == 404