"""HR staff portal phase 4 — employment changes, offboarding, leave."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.hr_admin_models import EmployeeLeavePolicy
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.employee_profile_schemas import EmployeeRegister
from app.modules.hr.employee_profile_service import register_employee
from app.modules.hr.employment_change_schemas import EmploymentChangeCreate, EmploymentChangeReview
from app.modules.hr.employment_change_service import create_employment_change, employment_change_overview, review_employment_change
from app.modules.hr.enums import HrEmploymentChangeType, HrOffboardingTaskStatus, HrResignationStatus, LeaveRequestStatus
from app.modules.hr.leave_schemas import LeaveApplicationCreate, LeaveApplicationReview, LeaveTypeConfigUpsert
from app.modules.hr.leave_service import create_leave_application, leave_overview, review_leave_application, upsert_leave_type
from app.modules.hr.models import LeaveRequest
from app.modules.hr.offboarding_schemas import OffboardingInitiate, OffboardingTaskUpdate, OffboardingTemplateUpsert, ResignationCreate, ResignationReview
from app.modules.hr.offboarding_service import (
    complete_offboarding,
    create_resignation,
    initiate_offboarding,
    review_resignation,
    update_offboarding_task,
    upsert_offboarding_template,
)
from app.modules.hr.offboarding_models import HrOffboardingTask
from app.modules.messaging.outbox_models import DomainOutboxEvent
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_mongo()


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


async def _seed(suffix: str):
    tenant = Tenant(name=f"HR4 {suffix}", code=f"hr4_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="HR", code=f"HR-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"C{suffix}", name="Main", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hr4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    scope = _scope(hr_user, Role.HR_STAFF)
    profile = await register_employee(
        scope,
        EmployeeRegister(
            employee_code=f"EMP-{suffix}",
            first_name="Sam",
            last_name="Lee",
            official_email=f"sam.{suffix}@example.com",
            password="password1234567890",
            mobile_number="9000000002",
            joining_date=date.today() - timedelta(days=120),
            employee_category="administrative",
            employment_type="full_time",
            employment_status=FacultyEmploymentStatus.ACTIVE,
            department_id=str(dept.id),
            designation="Analyst",
            campus_id=str(campus.id),
            probation_end_date=date.today() + timedelta(days=60),
        ),
    )
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.employee_id, profile.employee_code))
    assert employee is not None
    return tenant, hr_user, scope, dept, employee


@pytest.mark.asyncio
async def test_employment_change_and_resignation_offboarding(db_ready):
    suffix = uuid4().hex[:8]
    _, _, scope, dept, employee = await _seed(suffix)

    change = await create_employment_change(
        scope,
        EmploymentChangeCreate(
            employee_user_id=str(employee.user_id),
            change_type=HrEmploymentChangeType.DESIGNATION_CHANGE,
            proposed_details={"designation": "Senior Analyst"},
            effective_date=date.today(),
            reason="Performance",
            requires_manager_approval=False,
        ),
    )
    await review_employment_change(scope, change.id, EmploymentChangeReview(decision="hr_validate", note="Validated"))
    await review_employment_change(scope, change.id, EmploymentChangeReview(decision="approve", note="OK"))
    employee_refreshed = await EmployeeRecord.find_one(Eq(EmployeeRecord.user_id, employee.user_id))
    assert employee_refreshed is not None
    assert employee_refreshed.designation == "Senior Analyst"

    overview = await employment_change_overview(scope)
    assert overview.approved >= 1

    resignation = await create_resignation(
        scope,
        ResignationCreate(
            employee_user_id=str(employee.user_id),
            proposed_last_working_date=date.today() + timedelta(days=30),
            reason="Personal",
            notice_days=30,
        ),
    )
    assert resignation.status == HrResignationStatus.AWAITING_MANAGER_APPROVAL

    await review_resignation(scope, resignation.id, ResignationReview(decision="manager_approve", note="Noted"))
    accepted = await review_resignation(scope, resignation.id, ResignationReview(decision="accept", note="Approved"))
    assert accepted.status == HrResignationStatus.NOTICE_PERIOD

    template = await upsert_offboarding_template(
        scope,
        OffboardingTemplateUpsert(
            template_code=f"STD-{suffix}",
            title="Standard exit",
            tasks=[
                {"task_key": "it_clearance", "title": "IT clearance", "clearance_department": "it"},
                {"task_key": "hr_clearance", "title": "HR clearance", "clearance_department": "hr"},
            ],
        ),
    )
    process = await initiate_offboarding(
        scope,
        OffboardingInitiate(resignation_id=resignation.id, template_id=template["template_id"]),
    )
    pid = to_object_id(process.id, "process_id")
    tasks = await HrOffboardingTask.find(Eq(HrOffboardingTask.process_id, pid)).to_list()
    for task in tasks:
        await update_offboarding_task(scope, str(task.id), OffboardingTaskUpdate(status=HrOffboardingTaskStatus.COMPLETED))
    done = await complete_offboarding(scope, process.id)
    assert done.status.value == "completed"
    payroll_events = await DomainOutboxEvent.find(
        Eq(DomainOutboxEvent.event_type, "hr.payroll.final_settlement_requested"),
    ).count()
    assert payroll_events >= 1
    employee_refreshed = await EmployeeRecord.find_one(Eq(EmployeeRecord.user_id, employee.user_id))
    assert employee_refreshed.employment_status == FacultyEmploymentStatus.RESIGNED


@pytest.mark.asyncio
async def test_leave_workflow_with_balance(db_ready):
    suffix = uuid4().hex[:8]
    tenant, _, scope, _, employee = await _seed(suffix)

    await upsert_leave_type(scope, LeaveTypeConfigUpsert(leave_type_code="casual", title="Casual Leave", rules={"annual_entitlement": 12}))
    await EmployeeLeavePolicy(tenant_id=tenant.id, leave_type="casual", annual_quota_days=12, requires_approval=True).insert()

    leave = await create_leave_application(
        scope,
        LeaveApplicationCreate(
            employee_user_id=str(employee.user_id),
            leave_type="casual",
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=8),
            reason="Family commitment",
        ),
    )
    assert leave.status == LeaveRequestStatus.PENDING_MANAGER

    approved = await review_leave_application(
        scope,
        leave.id,
        LeaveApplicationReview(decision="manager_approve"),
    )
    assert approved.status == LeaveRequestStatus.PENDING_HR

    final = await review_leave_application(
        scope,
        leave.id,
        LeaveApplicationReview(decision="hr_approve", note="Enjoy"),
    )
    assert final.status == LeaveRequestStatus.APPROVED
    stored = await LeaveRequest.get(leave.id)
    assert stored is not None
    assert stored.balance_days_deducted == stored.working_days

    stats = await leave_overview(scope)
    assert stats.approved >= 1