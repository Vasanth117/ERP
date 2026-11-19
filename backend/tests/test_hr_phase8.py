"""HR staff portal phase 8 — benefits, performance and training."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.benefits_schemas import BenefitClaimCreate, BenefitClaimPaymentConfirm, BenefitClaimReview, BenefitEnrollmentCreate, BenefitProgramUpsert
from app.modules.hr.benefits_service import (
    confirm_claim_payment,
    create_claim,
    create_enrollment,
    review_claim,
    submit_claim_for_payment,
    upsert_benefit_program,
)
from app.modules.hr.employee_profile_schemas import EmployeeRegister
from app.modules.hr.employee_profile_service import register_employee
from app.modules.hr.enums import HrBenefitProgramStatus, HrTrainingProgramStatus
from app.modules.hr.performance_schemas import PerformanceCycleUpsert, PerformanceSelfAssessment
from app.modules.hr.performance_service import activate_performance_cycle, submit_self_assessment, upsert_performance_cycle
from app.modules.hr.performance_models import EmployeePerformanceReview
from app.common.ids import to_object_id
from app.modules.hr.training_schemas import (
    TrainingAssessmentSubmit,
    TrainingAttendanceUpsert,
    TrainingEnrollmentCreate,
    TrainingEnrollmentReview,
    TrainingProgramUpsert,
)
from app.modules.hr.training_service import (
    complete_training_enrollment,
    create_training_enrollment,
    record_training_attendance,
    review_training_enrollment,
    submit_training_assessment,
    upsert_training_program,
)
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
    tenant = Tenant(name=f"HR8 {suffix}", code=f"hr8_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="HR", code=f"HR-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"C{suffix}", name="Main", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hr8+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    emp_user = User(
        email=f"emp8+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Employee",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await emp_user.insert()
    hr_scope = _scope(hr_user, Role.HR_STAFF)
    emp_scope = _scope(emp_user, Role.FACULTY)
    await register_employee(
        hr_scope,
        EmployeeRegister(
            employee_code=f"EMP8-{suffix}",
            first_name="Test",
            last_name="Employee",
            official_email=f"official8+{suffix}@college.edu",
            mobile_number="9999999999",
            joining_date=date.today() - timedelta(days=400),
            employee_category="faculty",
            employment_type="permanent",
            department_id=str(dept.id),
            designation="Assistant Professor",
            campus_id=str(campus.id),
            link_existing_user_id=str(emp_user.id),
            institution_role=Role.FACULTY,
        ),
    )
    return tenant, hr_scope, emp_scope, emp_user


@pytest.mark.asyncio
async def test_benefit_claim_payment_lifecycle(db_ready):
    suffix = uuid4().hex[:6]
    _, hr_scope, emp_scope, emp_user = await _seed(suffix)
    program = await upsert_benefit_program(
        hr_scope,
        BenefitProgramUpsert(
            program_code=f"MED-{suffix}",
            name="Medical",
            category="medical",
            coverage_limit="50000",
            status=HrBenefitProgramStatus.ACTIVE,
            requires_approval=False,
        ),
    )
    enroll = await create_enrollment(
        emp_scope,
        BenefitEnrollmentCreate(benefit_program_id=program.id, employee_user_id=str(emp_user.id), document_refs=["doc1"]),
        self_service=True,
    )
    assert enroll.status.value == "active"
    claim = await create_claim(
        emp_scope,
        BenefitClaimCreate(
            benefit_program_id=program.id,
            employee_user_id=str(emp_user.id),
            enrollment_id=enroll.id,
            claim_category="medical",
            claim_date=date.today(),
            description="Consultation",
            expense_amount="2000",
            requested_amount="2000",
            document_refs=["bill1"],
        ),
        self_service=True,
    )
    reviewed = await review_claim(hr_scope, claim.id, BenefitClaimReview(action="approve", approved_amount="1800"))
    assert reviewed.status.value == "awaiting_payment"
    await submit_claim_for_payment(hr_scope, claim.id)
    paid = await confirm_claim_payment(hr_scope, claim.id, BenefitClaimPaymentConfirm(payment_reference="PAY-123"))
    assert paid.status.value == "paid"
    assert paid.payment_status == "paid"


@pytest.mark.asyncio
async def test_performance_and_training(db_ready):
    suffix = uuid4().hex[:6]
    tenant, hr_scope, emp_scope, emp_user = await _seed(suffix)
    cycle = await upsert_performance_cycle(
        hr_scope,
        PerformanceCycleUpsert(
            cycle_code=f"ANN-{suffix}",
            title="Annual Review",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=30),
        ),
    )
    activation = await activate_performance_cycle(hr_scope, cycle.id)
    assert activation["reviews_created"] >= 1
    review = await EmployeePerformanceReview.find_one(
        Eq(EmployeePerformanceReview.tenant_id, tenant.id),
        Eq(EmployeePerformanceReview.employee_user_id, emp_user.id),
    )
    assert review is not None
    updated = await submit_self_assessment(
        emp_scope,
        str(review.id),
        PerformanceSelfAssessment(achievements="Delivered courses", training_needs=["communication"]),
    )
    assert updated.status.value == "manager_review"

    tprog = await upsert_training_program(
        hr_scope,
        TrainingProgramUpsert(
            program_code=f"TRN-{suffix}",
            title="Safety Training",
            category="safety",
            capacity=10,
            status=HrTrainingProgramStatus.OPEN,
            completion_criteria={"min_sessions_present": 1, "requires_passing_assessment": True, "min_score": "50"},
        ),
    )
    tenroll = await create_training_enrollment(
        emp_scope,
        TrainingEnrollmentCreate(training_program_id=tprog.id, employee_user_id=str(emp_user.id)),
        self_service=True,
    )
    confirmed = await review_training_enrollment(hr_scope, tenroll.id, TrainingEnrollmentReview(action="confirm"))
    assert confirmed.status.value == "confirmed"
    await record_training_attendance(
        hr_scope,
        tenroll.id,
        TrainingAttendanceUpsert(session_code="S1", session_date=date.today(), status="present", attended_minutes=60),
        self_service=False,
    )
    await submit_training_assessment(hr_scope, tenroll.id, TrainingAssessmentSubmit(score="80", max_score="100"))
    done = await complete_training_enrollment(hr_scope, tenroll.id)
    assert done["completed"] is True
    assert done["certificate_code"]