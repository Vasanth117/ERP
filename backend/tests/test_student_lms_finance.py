"""Student phase 9 — LMS study materials and finance portal."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import hmac
import hashlib
import json
import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.config import get_settings
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import StudentFeeDemand, StudentScholarshipEligibility, ScholarshipProgram
from app.modules.finance.payment_verification import apply_verified_payment, verify_webhook_signature
from app.modules.lms.enums import LmsAssignmentStatus, MaterialPublishState
from app.modules.lms.models import AssignmentRule, CourseAssignment, LearningMaterial
from app.modules.lms.storage import write_bytes
from app.modules.students.integrations.student_lms_reader import authorized_material
from app.modules.students.student_finance_schemas import PaymentInitiateInput
from app.modules.students.student_finance_service import get_payment_status, initiate_payment
from app.modules.students.student_lms_service import issue_material_download, list_course_materials, submit_assignment_file
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
        await connect_redis()
    except Exception as exc:
        pytest.skip(f"Dependencies not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name="College", code=f"s9_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    user = User(
        email=f"s9+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await user.insert()
    other = User(
        email=f"s9other+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await other.insert()
    scope = AccessScope(
        role=Role.STUDENT,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    return tenant, user, scope, other


async def _academic_seed(tenant: Tenant, user: User) -> None:
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id="c101",
        course_code="CSE101",
        section_code="A",
        student_user_id=user.id,
        roll_number="R900",
        display_name="Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()


def test_payment_webhook_signature_unit() -> None:
    secret = "test-webhook-secret-32chars-minimum"
    payload = b'{"transaction_id":"pay_x","gateway_reference":"gw_1"}'
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    settings = get_settings()
    object.__setattr__(settings, "payment_webhook_secret", secret)
    assert verify_webhook_signature(payload, sig) is True
    assert verify_webhook_signature(payload, "bad") is False


@pytest.mark.anyio
async def test_material_authorization_and_list(db_ready) -> None:
    tenant, user, scope, other = await _seed("mat")
    await _academic_seed(tenant, user)
    storage_key, _ = write_bytes(f"{tenant.id}/materials/notes.pdf", b"%PDF-1.4 test")
    mat = LearningMaterial(
        tenant_id=tenant.id,
        faculty_user_id=user.id,
        course_id="c101",
        course_code="CSE101",
        section="A",
        title="Unit 1 Notes",
        file_id="f1",
        storage_key=storage_key,
        file_name="notes.pdf",
        mime_type="application/pdf",
        size_bytes=14,
        publish_state=MaterialPublishState.PUBLISHED,
        unit_no=1,
    )
    await mat.insert()
    other_mat = LearningMaterial(
        tenant_id=tenant.id,
        faculty_user_id=user.id,
        course_id="c999",
        course_code="ECE999",
        section="A",
        title="Foreign",
        file_id="f2",
        storage_key=storage_key,
        file_name="x.pdf",
        mime_type="application/pdf",
        size_bytes=14,
        publish_state=MaterialPublishState.PUBLISHED,
    )
    await other_mat.insert()
    items = await list_course_materials(scope, user)
    assert len(items) == 1
    assert items[0].title == "Unit 1 Notes"
    ok = await authorized_material(tenant.id, user.id, mat.id, year="2025-26", semester="Odd")
    assert ok is not None
    denied = await authorized_material(tenant.id, user.id, other_mat.id, year="2025-26", semester="Odd")
    assert denied is None
    token = await issue_material_download(scope, user, str(mat.id))
    assert token.download_token
    assert token.material_id == str(mat.id)


@pytest.mark.anyio
async def test_assignment_submission(db_ready) -> None:
    tenant, user, scope, _ = await _seed("asg")
    await _academic_seed(tenant, user)
    rule = AssignmentRule(tenant_id=tenant.id)
    await rule.insert()
    assignment = CourseAssignment(
        tenant_id=tenant.id,
        faculty_user_id=user.id,
        course_id="c101",
        course_code="CSE101",
        section="A",
        title="Lab 1",
        instructions="Submit PDF",
        max_marks=10,
        deadline_at=datetime.now(timezone.utc) + timedelta(days=1),
        rule_id=rule.id,
        status=LmsAssignmentStatus.PUBLISHED,
        academic_year_label="2025-26",
        semester_label="Odd",
    )
    await assignment.insert()
    status = await submit_assignment_file(
        scope,
        user,
        str(assignment.id),
        "work.pdf",
        "application/pdf",
        b"%PDF sample",
    )
    assert status.value in {"submitted", "late"}
    with pytest.raises(AppError) as exc:
        await submit_assignment_file(
            scope,
            user,
            str(assignment.id),
            "work.pdf",
            "application/pdf",
            b"%PDF sample",
        )
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_payment_idempotency_and_verification(db_ready) -> None:
    tenant, user, scope, _ = await _seed("pay")
    await _academic_seed(tenant, user)
    demand_id = f"dem_{uuid4().hex[:8]}"
    await StudentFeeDemand(
        tenant_id=tenant.id,
        student_user_id=user.id,
        demand_id=demand_id,
        academic_year_label="2025-26",
        semester_label="Odd",
        description="Semester fee",
        amount=5000,
        due_date=date.today() + timedelta(days=30),
        status=FeeDemandStatus.OPEN,
    ).insert()
    key = "idem_" + uuid4().hex
    payload = PaymentInitiateInput(demand_id=demand_id, idempotency_key=key)
    first = await initiate_payment(scope, user, payload)
    second = await initiate_payment(scope, user, payload)
    assert first.transaction_id == second.transaction_id
    status = await get_payment_status(scope, user, first.transaction_id)
    assert status.status == PaymentTransactionStatus.INITIATED.value
    tx = await apply_verified_payment(first.transaction_id, gateway_reference="gw_ref_1")
    assert tx.webhook_verified is True
    status2 = await get_payment_status(scope, user, first.transaction_id)
    assert status2.webhook_verified is True
    assert status2.status == PaymentTransactionStatus.SUCCESS.value


@pytest.mark.anyio
async def test_scholarship_eligibility_gate(db_ready) -> None:
    tenant, user, scope, _ = await _seed("sch")
    await _academic_seed(tenant, user)
    programme_id = "merit_2025"
    await ScholarshipProgram(
        tenant_id=tenant.id,
        programme_id=programme_id,
        title="Merit",
        applications_open=True,
    ).insert()
    await StudentScholarshipEligibility(
        tenant_id=tenant.id,
        student_user_id=user.id,
        programme_id=programme_id,
        eligible=True,
        reasons=["CGPA"],
        published=True,
    ).insert()
    from app.modules.students.student_finance_schemas import ScholarshipApplicationInput
    from app.modules.students.student_finance_service import submit_scholarship

    app = await submit_scholarship(
        scope,
        user,
        ScholarshipApplicationInput(programme_id=programme_id, statement="Need support"),
    )
    assert app.application_id.startswith("sch_")
