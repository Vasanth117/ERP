"""Hostel Admin phase 4 — mess billing and leave/outpass."""

from datetime import date, datetime, timedelta, timezone
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
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
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
from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus, HostelOutpassType
from app.modules.hostel.leave_outpass_schemas import ApprovalDecision, GateMovementInput, OutpassSubmit
from app.modules.hostel.leave_outpass_service import record_gate_movement, review_request, submit_outpass_student
from app.modules.hostel.mess_models import HostelMessBillingRecord, MessBillingRecordStatus, MessEnrollmentStatus, MessPlanStatus
from app.modules.hostel.mess_schemas import BillingCalculateInput, BillingPeriodCreate, BillingSendFinanceInput, MessEnrollmentCreate, MessPlanUpsertPortal
from app.modules.hostel.mess_service import (
    calculate_billing_period,
    create_billing_period,
    create_enrollment,
    send_billing_to_finance,
    sync_billing_payments,
    upsert_plan,
)
from app.modules.hostel.resident_models import HostelResident
from app.modules.hostel.resident_schemas import ResidentCheckinInput
from app.modules.hostel.resident_service import check_in_resident
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
    tenant = Tenant(name=f"H P4 {suffix}", code=f"hp4_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"ha4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Hostel Admin",
        role=Role.HOSTEL_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"st4+{suffix}@example.com",
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
    scope_admin = AccessScope(
        user_id=admin.id,
        tenant_id=tenant.id,
        role=Role.HOSTEL_ADMIN,
        effective_permissions=permissions_for_role(Role.HOSTEL_ADMIN),
    )
    scope_student = AccessScope(user_id=student.id, tenant_id=tenant.id, role=Role.STUDENT, effective_permissions=permissions_for_role(Role.STUDENT))
    return tenant, admin, student, scope_admin, scope_student


async def _infra(scope):
    suffix = uuid4().hex[:6]
    await create_hostel(scope, InstitutionHostelCreate(hostel_code=f"H{suffix}", name="Main Hostel"))
    await create_building(scope, HostelBuildingCreate(hostel_code=f"H{suffix}", building_code="B1", name="Block 1"))
    await create_block(scope, HostelBlockCreate(hostel_code=f"H{suffix}", building_code="B1", block_code="BLK1", name="Block A"))
    await create_room(
        scope,
        HostelRoomCreate(hostel_code=f"H{suffix}", building_code="B1", block_code="BLK1", room_code="101", capacity=2),
    )
    bed = await create_bed(
        scope,
        HostelBedPortalCreate(hostel_code=f"H{suffix}", building_code="B1", block_code="BLK1", room_code="101", bed_label="A"),
    )
    return f"H{suffix}", bed.bed_id


@pytest.mark.asyncio
async def test_mess_billing_finance_handoff(db_ready):
    tenant, admin, student, scope, _ = await _seed("mess")
    hostel_code, bed_id = await _infra(scope)
    alloc = await create_allocation(
        scope,
        AllocationCreate(student_user_id=str(student.id), hostel_code=hostel_code, building_code="B1", block_code="BLK1", room_code="101", bed_id=bed_id),
    )
    await check_in_resident(scope, ResidentCheckinInput(allocation_id=alloc.allocation_id, keys_issued=["k1"], room_condition_ack=True))
    resident = await HostelResident.find_one(Eq(HostelResident.tenant_id, tenant.id))
    plan = await upsert_plan(
        scope,
        MessPlanUpsertPortal(plan_code="FULL", title="Full Board", mess_code="M1", monthly_amount=3000, published=True, status=MessPlanStatus.ACTIVE, requires_approval=False),
    )
    enr = await create_enrollment(
        scope,
        MessEnrollmentCreate(resident_id=resident.resident_id, plan_code=plan.plan_code, mess_code="M1", start_date=date.today().replace(day=1)),
    )
    assert enr.status == MessEnrollmentStatus.ACTIVE
    period_start = date.today().replace(day=1)
    period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    created = await create_billing_period(scope, BillingPeriodCreate(label="Month", period_start=period_start, period_end=period_end))
    calc = await calculate_billing_period(scope, BillingCalculateInput(period_id=created["period_id"]))
    assert calc["records_created"] >= 1
    record = await HostelMessBillingRecord.find_one(Eq(HostelMessBillingRecord.tenant_id, tenant.id))
    record.status = MessBillingRecordStatus.APPROVED
    await record.save()
    sent = await send_billing_to_finance(scope, BillingSendFinanceInput(period_id=created["period_id"]))
    assert sent["demands_created"] >= 1
    demand = await StudentFeeDemand.find_one(Eq(StudentFeeDemand.tenant_id, tenant.id))
    assert demand is not None
    demand.status = FeeDemandStatus.PAID
    await demand.save()
    sync = await sync_billing_payments(scope, created["period_id"])
    assert sync["records_updated"] >= 1


@pytest.mark.asyncio
async def test_outpass_gate_requires_approval(db_ready):
    tenant, admin, student, scope_admin, scope_student = await _seed("out")
    hostel_code, bed_id = await _infra(scope_admin)
    alloc = await create_allocation(
        scope_admin,
        AllocationCreate(student_user_id=str(student.id), hostel_code=hostel_code, building_code="B1", block_code="BLK1", room_code="101", bed_id=bed_id),
    )
    await check_in_resident(scope_admin, ResidentCheckinInput(allocation_id=alloc.allocation_id, keys_issued=[], room_condition_ack=True))
    now = datetime.now(timezone.utc)
    row = await submit_outpass_student(
        scope_student,
        student,
        OutpassSubmit(outpass_type=HostelOutpassType.DAY, reason="Family", from_at=now, to_at=now + timedelta(hours=4)),
    )
    assert row.status == HostelLeaveOutpassStatus.PENDING_APPROVAL
    with pytest.raises(AppError):
        await record_gate_movement(
            scope_admin,
            GateMovementInput(request_id=row.request_id, kind="outpass", movement_type="departure"),
        )
    await review_request(scope_admin, ApprovalDecision(request_id=row.request_id, kind="outpass", approve=True))
    moved = await record_gate_movement(
        scope_admin,
        GateMovementInput(request_id=row.request_id, kind="outpass", movement_type="departure"),
    )
    assert moved["request_id"] == row.request_id