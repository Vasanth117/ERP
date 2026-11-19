"""Hostel Admin phase 5 — maintenance complaints and rules/incidents."""

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
from app.modules.hostel.maintenance_models import HostelComplaintStatus
from app.modules.hostel.maintenance_schemas import ComplaintAssign, ComplaintSubmit, FacilityUnavailabilityInput
from app.modules.hostel.maintenance_service import assign_complaint, set_facility_unavailability, submit_complaint, update_complaint_status
from app.modules.hostel.maintenance_schemas import ComplaintStatusUpdate
from app.modules.hostel.resident_schemas import ResidentCheckinInput
from app.modules.hostel.resident_service import check_in_resident
from app.modules.hostel.rules_incident_models import HostelIncidentStatus, HostelRuleApprovalStatus
from app.modules.hostel.rules_incident_schemas import HostelRuleUpsertPortal, IncidentReportInput, RuleAcknowledgeInput, RulePublishInput
from app.modules.hostel.rules_incident_service import acknowledge_rule, publish_rule, report_incident, upsert_rule
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
    tenant = Tenant(name=f"H P5 {suffix}", code=f"hp5_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"ha5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Hostel Admin",
        role=Role.HOSTEL_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"st5+{suffix}@example.com",
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


async def _checked_in(scope, student):
    suffix = uuid4().hex[:6]
    hcode, bcode = f"H{suffix}", f"B{suffix}"
    await create_hostel(scope, InstitutionHostelCreate(hostel_code=hcode, name="Hostel", configured_capacity=2))
    await create_building(scope, HostelBuildingCreate(hostel_code=hcode, building_code=bcode, name="Main"))
    await create_block(scope, HostelBlockCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", name="A"))
    await create_room(scope, HostelRoomCreate(hostel_code=hcode, building_code=bcode, block_code="BLK1", room_code="101", bed_capacity=1))
    bed_id = f"bed-{suffix}"
    await create_bed(scope, HostelBedPortalCreate(hostel_code=hcode, bed_id=bed_id, building_code=bcode, block_code="BLK1", room_code="101", bed_label="A"))
    alloc = await create_allocation(scope, AllocationCreate(student_user_id=str(student.id), hostel_code=hcode, bed_id=bed_id))
    await check_in_resident(scope, ResidentCheckinInput(allocation_id=alloc.allocation_id))
    return hcode, bcode, bed_id


@pytest.mark.anyio
async def test_complaint_and_bed_unavailability(db_ready) -> None:
    _, _, student, scope_admin, scope_student = await _seed("cmp")
    hcode, bcode, bed_id = await _checked_in(scope_admin, student)
    row = await submit_complaint(
        scope_student,
        ComplaintSubmit(
            building_code=bcode,
            block_code="BLK1",
            room_code="101",
            bed_id=bed_id,
            category_code="PLUMBING",
            subject="Leak",
            description="Tap leaking",
        ),
        student_user=student,
    )
    assert row.status == HostelComplaintStatus.SUBMITTED
    await assign_complaint(scope_admin, ComplaintAssign(complaint_id=row.complaint_id, department="facilities"))
    await set_facility_unavailability(
        scope_admin,
        FacilityUnavailabilityInput(
            complaint_id=row.complaint_id,
            facility_type="bed",
            building_code=bcode,
            block_code="BLK1",
            room_code="101",
            bed_id=bed_id,
            reason="Unsafe plumbing",
        ),
    )
    bed = await HostelBed.find_one(Eq(HostelBed.bed_id, bed_id))
    assert bed.status == HostelBedStatus.MAINTENANCE
    closed = await update_complaint_status(
        scope_admin,
        ComplaintStatusUpdate(complaint_id=row.complaint_id, status=HostelComplaintStatus.RESOLVED),
    )
    assert closed.status == HostelComplaintStatus.RESOLVED


@pytest.mark.anyio
async def test_rule_ack_and_incident_allegation(db_ready) -> None:
    _, _, student, scope_admin, scope_student = await _seed("inc")
    rule = await upsert_rule(
        scope_admin,
        HostelRuleUpsertPortal(rule_code="QUIET", title="Quiet hours", body="No noise after 10pm"),
    )
    published = await publish_rule(scope_admin, RulePublishInput(rule_code=rule.rule_code, approve=True))
    assert published.published is True
    ack = await acknowledge_rule(scope_student, student, RuleAcknowledgeInput(rule_code=rule.rule_code))
    assert ack["acknowledged"] is True
    inc = await report_incident(
        scope_admin,
        IncidentReportInput(category="conduct", description="Noise complaint", severity="low"),
    )
    assert inc.allegation_only is True
    assert inc.status == HostelIncidentStatus.REPORTED