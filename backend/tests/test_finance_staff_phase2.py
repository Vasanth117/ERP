"""Accounts / Finance Staff — Phase 2 assessments + invoices."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.accounts_finance.assessment_service import create_individual_assessment, transition_assessment
from app.modules.accounts_finance.enums import FeeCategoryClassification, FeeStructureApprovalAction
from app.modules.accounts_finance.fee_category_service import upsert_fee_category
from app.modules.accounts_finance.fee_structure_service import create_fee_structure, transition_fee_structure
from app.modules.accounts_finance.invoice_service import generate_invoices, get_invoice, issue_invoice
from app.modules.accounts_finance.phase2_enums import FeeAssessmentWorkflowStatus, StudentInvoiceStatus
from app.modules.accounts_finance.phase2_schemas import AssessmentTransition, IndividualAssessmentCreate, InvoiceGenerateScope
from app.modules.accounts_finance.schemas import FeeCategoryUpsert, FeeStructureComponentInput, FeeStructureCreate, FeeStructureTransition
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.finance_admin_models import StudentFeeAssessment
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeInvoice
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord
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


async def _seed(suffix: str) -> tuple[Tenant, AccessScope, User, str]:
    tenant = Tenant(name=f"Fin P2 {suffix}", code=f"fp2_{suffix}")
    await tenant.insert()
    staff = User(
        email=f"staff+p2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance Staff",
        role=Role.FINANCE_STAFF,
        tenant_id=tenant.id,
    )
    await staff.insert()
    scope = AccessScope(
        role=Role.FINANCE_STAFF,
        user_id=staff.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FINANCE_STAFF),
    )
    await AcademicYear(tenant_id=tenant.id, year_code="2025-26", label="2025-26", is_current=True).insert()
    await AcademicProgramme(tenant_id=tenant.id, programme_code="BSC-CS", name="BSc CS").insert()
    student = User(
        email=f"student+p2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    await StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        student_id=f"STU{suffix}",
        roll_number=f"R{suffix}",
        programme_code="BSC-CS",
        batch_label="2025",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
        enrollment_status=StudentEnrollmentStatus.ACTIVE,
    ).insert()
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        enrollment_status=StudentEnrollmentStatus.ACTIVE,
    ).insert()
    await upsert_fee_category(
        scope,
        FeeCategoryUpsert(fee_code="TUITION", name="Tuition", classification=FeeCategoryClassification.TUITION),
    )
    struct_id = f"struct_{suffix}"
    created = await create_fee_structure(
        scope,
        FeeStructureCreate(
            structure_id=struct_id,
            academic_year_label="2025-26",
            semester_label="Odd",
            programme_code="BSC-CS",
            components=[FeeStructureComponentInput(fee_category_code="TUITION", amount=25000)],
        ),
    )
    await transition_fee_structure(scope, created.structure_id, FeeStructureTransition(action=FeeStructureApprovalAction.SUBMIT))
    await transition_fee_structure(scope, created.structure_id, FeeStructureTransition(action=FeeStructureApprovalAction.APPROVE))
    await transition_fee_structure(scope, created.structure_id, FeeStructureTransition(action=FeeStructureApprovalAction.ACTIVATE))
    return tenant, scope, student, struct_id


@pytest.mark.anyio
async def test_assessment_to_invoice_flow(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, student, struct_id = await _seed(suffix)
    assessment = await create_individual_assessment(
        scope,
        IndividualAssessmentCreate(
            student_user_id=str(student.id),
            academic_year_label="2025-26",
            semester_label="Odd",
            structure_id=struct_id,
        ),
    )
    assert assessment.workflow_status == FeeAssessmentWorkflowStatus.DRAFT
    await transition_assessment(scope, assessment.assessment_id, AssessmentTransition(action="submit"))
    approved = await transition_assessment(scope, assessment.assessment_id, AssessmentTransition(action="approve"))
    assert approved.workflow_status == FeeAssessmentWorkflowStatus.APPROVED
    gen = await generate_invoices(
        scope,
        InvoiceGenerateScope(
            academic_year_label="2025-26",
            semester_label="Odd",
            assessment_ids=[assessment.assessment_id],
            due_date=date.today() + timedelta(days=30),
        ),
    )
    assert gen["count"] == 1
    refreshed = await StudentFeeAssessment.find_one(Eq(StudentFeeAssessment.assessment_id, assessment.assessment_id))
    assert refreshed and refreshed.invoice_id
    issued = await issue_invoice(scope, refreshed.invoice_id)
    assert issued.invoice_status == StudentInvoiceStatus.ISSUED
    assert issued.invoice_number


@pytest.mark.anyio
async def test_duplicate_assessment_blocked(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, student, struct_id = await _seed(suffix)
    await create_individual_assessment(
        scope,
        IndividualAssessmentCreate(
            student_user_id=str(student.id),
            academic_year_label="2025-26",
            semester_label="Odd",
            structure_id=struct_id,
        ),
    )
    with pytest.raises(AppError) as exc:
        await create_individual_assessment(
            scope,
            IndividualAssessmentCreate(
                student_user_id=str(student.id),
                academic_year_label="2025-26",
                semester_label="Odd",
                structure_id=struct_id,
            ),
        )
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_invoice_payment_status_from_verified_tx(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, scope, student, struct_id = await _seed(suffix)
    assessment = await create_individual_assessment(
        scope,
        IndividualAssessmentCreate(
            student_user_id=str(student.id),
            academic_year_label="2025-26",
            semester_label="Odd",
            structure_id=struct_id,
        ),
    )
    await transition_assessment(scope, assessment.assessment_id, AssessmentTransition(action="submit"))
    await transition_assessment(scope, assessment.assessment_id, AssessmentTransition(action="approve"))
    await generate_invoices(
        scope,
        InvoiceGenerateScope(
            academic_year_label="2025-26",
            semester_label="Odd",
            assessment_ids=[assessment.assessment_id],
            due_date=date.today() + timedelta(days=30),
        ),
    )
    row = await StudentFeeAssessment.find_one(Eq(StudentFeeAssessment.assessment_id, assessment.assessment_id))
    inv = await issue_invoice(scope, row.invoice_id)
    invoice = await StudentFeeInvoice.find_one(Eq(StudentFeeInvoice.invoice_id, inv.invoice_id))
    await PaymentTransaction(
        tenant_id=tenant.id,
        student_user_id=student.id,
        transaction_id=f"pay_{suffix}",
        idempotency_key=f"idem_{suffix}",
        demand_id=invoice.demand_id,
        amount=invoice.amount,
        status=PaymentTransactionStatus.SUCCESS,
        payment_mode="offline",
    ).insert()
    read = await get_invoice(scope, inv.invoice_id)
    assert read.payment_status_synced == StudentInvoiceStatus.PAID.value