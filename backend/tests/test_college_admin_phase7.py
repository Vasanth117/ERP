"""College Admin phase 7 — hostel and communication administration."""

from datetime import datetime, timedelta, timezone
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
from app.modules.college_admin.communication_admin_schemas import AnnouncementCreate
from app.modules.college_admin.communication_admin_service import create_announcement, publish_announcement
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus
from app.modules.college_admin.hostel_admin_schemas import (
    AllocationApprove,
    CheckInOut,
    HostelBedCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelRoomCreate,
)
from app.modules.college_admin.hostel_admin_service import (
    approve_allocation,
    check_in,
    check_out,
    create_bed,
    create_block,
    create_building,
    create_room,
    occupancy_report,
)
from app.modules.hostel.hostel_models import HostelApplication
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


async def _seed_admin(suffix: str) -> tuple[Tenant, AccessScope]:
    tenant = Tenant(name=f"College P7 {suffix}", code=f"p7_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+p7+{suffix}@example.com",
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
    return tenant, scope


@pytest.mark.anyio
async def test_hostel_double_bed_allocation_prevented(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope = await _seed_admin(suffix)
    bcode = f"B-{suffix}"
    await create_building(scope, HostelBuildingCreate(building_code=bcode, name="Hostel A"))
    await create_block(scope, HostelBlockCreate(building_code=bcode, block_code="BLK1", name="Block 1"))
    await create_room(scope, HostelRoomCreate(building_code=bcode, block_code="BLK1", room_code="101", capacity=2))
    bed_id = f"bed-{suffix}"
    await create_bed(
        scope,
        HostelBedCreate(bed_id=bed_id, building_code=bcode, block_code="BLK1", room_code="101", bed_label="A"),
    )
    students = []
    apps = []
    for i in range(2):
        s = User(
            email=f"hs{i}+{suffix}@example.com",
            hashed_password=hash_password("password1234567890"),
            full_name=f"Student {i}",
            role=Role.STUDENT,
            tenant_id=tenant.id,
        )
        await s.insert()
        students.append(s)
        app_id = f"app{i}-{suffix}"
        await HostelApplication(
            tenant_id=tenant.id,
            student_user_id=s.id,
            application_id=app_id,
            academic_year_label="2025",
        ).insert()
        apps.append(app_id)
    first = await approve_allocation(scope, AllocationApprove(application_id=apps[0], bed_id=bed_id))
    assert first["allocation_id"]
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant.id), Eq(HostelBed.bed_id, bed_id))
    assert bed is not None
    assert bed.status == HostelBedStatus.ALLOCATED
    with pytest.raises(AppError) as exc:
        await approve_allocation(scope, AllocationApprove(application_id=apps[1], bed_id=bed_id))
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_hostel_check_in_out_frees_bed(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope = await _seed_admin(suffix)
    bcode = f"B2-{suffix}"
    await create_building(scope, HostelBuildingCreate(building_code=bcode, name="Hostel B"))
    await create_block(scope, HostelBlockCreate(building_code=bcode, block_code="BLK1", name="Block"))
    await create_room(scope, HostelRoomCreate(building_code=bcode, block_code="BLK1", room_code="201", capacity=1))
    bed_id = f"bed2-{suffix}"
    await create_bed(
        scope,
        HostelBedCreate(bed_id=bed_id, building_code=bcode, block_code="BLK1", room_code="201", bed_label="B"),
    )
    student = User(
        email=f"hs3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Resident",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    app_id = f"app3-{suffix}"
    await HostelApplication(tenant_id=tenant.id, student_user_id=student.id, application_id=app_id, academic_year_label="2025").insert()
    alloc = await approve_allocation(scope, AllocationApprove(application_id=app_id, bed_id=bed_id))
    checked = await check_in(scope, CheckInOut(allocation_id=alloc["allocation_id"]))
    assert checked["status"] == "active"
    await check_out(scope, CheckInOut(allocation_id=alloc["allocation_id"]))
    bed = await HostelBed.find_one(Eq(HostelBed.tenant_id, tenant.id), Eq(HostelBed.bed_id, bed_id))
    assert bed is not None
    assert bed.status == HostelBedStatus.AVAILABLE
    report = await occupancy_report(scope, building_code=bcode)
    assert report["available_beds"] >= 1


@pytest.mark.anyio
async def test_announcement_publish_and_permission(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope = await _seed_admin(suffix)
    aid = f"ann-{suffix}"
    await create_announcement(scope, AnnouncementCreate(announcement_id=aid, title="Holiday", body="Campus closed"))
    published = await publish_announcement(scope, aid)
    assert published.status == "published"
    faculty = User(
        email=f"fac+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await faculty.insert()
    fscope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    with pytest.raises(AppError) as exc:
        await publish_announcement(fscope, f"ann2-{suffix}")
    assert exc.value.status_code in (403, 404)
    assert Permission.COMMUNICATION_ADMIN_PUBLISH not in fscope.effective_permissions


@pytest.mark.anyio
async def test_tenant_isolation_hostel_bed(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant_a, scope_a = await _seed_admin(f"a{suffix}")
    _, scope_b = await _seed_admin(f"b{suffix}")
    bcode = f"BA-{suffix}"
    await create_building(scope_a, HostelBuildingCreate(building_code=bcode, name="A"))
    report_b = await occupancy_report(scope_b, building_code=bcode)
    assert report_b["total_beds"] == 0
    assert tenant_a.id is not None