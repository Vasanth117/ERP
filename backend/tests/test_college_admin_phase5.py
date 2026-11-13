"""College Admin phase 5 — examination and finance administration."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.examination_admin_schemas import (
    EligibilityUpsert,
    ExaminationConfigUpsert,
    ExaminationSeasonCreate,
    ExaminationSessionCreate,
    HallTicketGenerate,
    MarksBatchDecision,
    ResultPublishRequest,
)
from app.modules.college_admin.examination_admin_service import (
    create_examination_season,
    create_examination_session,
    generate_hall_ticket,
    publish_results,
    review_marks_batch,
    set_eligibility,
    upsert_examination_config,
)
from app.modules.college_admin.finance_admin_schemas import FeeAssessmentCreate, FeeStructureUpsert, OfflineCollectionCreate
from app.modules.college_admin.finance_admin_service import (
    create_fee_assessment,
    record_offline_collection,
    upsert_fee_structure,
)
from app.modules.examinations.enums import MarksBatchStatus
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.examinations.models import MarksSubmissionBatch
from app.modules.examinations.result_publication_models import SemesterResultPublication
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand, StudentFeeStructure
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


async def _seed_admin(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College P5 {suffix}", code=f"p5_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+p5+{suffix}@example.com",
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
    return tenant, user, scope


@pytest.mark.anyio
async def test_examination_session_and_eligibility_hall_ticket(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    season_id = f"season_{suffix}"
    now = datetime.now(timezone.utc)
    await create_examination_season(
        scope,
        ExaminationSeasonCreate(
            season_id=season_id,
            title="End Semester",
            academic_year_label="2025",
            semester_label="Odd",
            starts_at=now,
            ends_at=now + timedelta(days=30),
        ),
    )
    await upsert_examination_config(
        scope,
        ExaminationConfigUpsert(
            season_id=season_id,
            title="Config",
            academic_year_label="2025",
            semester_label="Odd",
            component_definitions=[{"component_id": "final", "name": "Final", "max_marks": 100}],
        ),
    )
    await create_examination_session(
        scope,
        ExaminationSessionCreate(
            season_id=season_id,
            session_code="S1",
            course_code="CS101",
            course_name="Programming",
            scheduled_start=now + timedelta(days=5),
        ),
    )
    student = User(
        email=f"stu+p5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    await set_eligibility(
        scope,
        EligibilityUpsert(student_user_id=str(student.id), season_id=season_id, eligible=True, reasons=[]),
    )
    ticket = await generate_hall_ticket(
        scope,
        HallTicketGenerate(student_user_id=str(student.id), season_id=season_id, student_name="Student"),
    )
    assert ticket["ticket_number"]


@pytest.mark.anyio
async def test_marks_review_and_result_publication(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    faculty = User(
        email=f"fac+p5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty Marks",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await faculty.insert()
    student = User(
        email=f"stu2+p5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student Two",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    batch = MarksSubmissionBatch(
        tenant_id=tenant.id,
        faculty_user_id=faculty.id,
        assessment_id="asm1",
        component_id="final",
        course_code="CS101",
        section="A",
        status=MarksBatchStatus.PENDING_APPROVAL,
    )
    await batch.insert()
    reviewed = await review_marks_batch(
        scope,
        MarksBatchDecision(batch_id=str(batch.id), decision=MarksBatchStatus.APPROVED, note="OK"),
    )
    assert reviewed["status"] == MarksBatchStatus.APPROVED.value
    season_id = f"res_{suffix}"
    published = await publish_results(
        scope,
        ResultPublishRequest(
            student_user_id=str(student.id),
            season_id=season_id,
            academic_year_label="2025",
            semester_label="Odd",
        ),
    )
    pub = await SemesterResultPublication.get(to_object_id(published["publication_id"], "publication_id"))
    assert pub is not None
    assert pub.status == SemesterResultPublicationStatus.PUBLISHED


@pytest.mark.anyio
async def test_fee_structure_assessment_offline_payment_duplicate(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    structure_id = f"struct_{suffix}"
    await upsert_fee_structure(
        scope,
        FeeStructureUpsert(
            structure_id=structure_id,
            programme_code="BTECH",
            academic_year_label="2025",
            semester_label="Odd",
            line_items=[{"code": "tuition", "amount": 50000}],
            total_amount=50000,
        ),
    )
    synced = await StudentFeeStructure.find_one(Eq(StudentFeeStructure.tenant_id, tenant.id), Eq(StudentFeeStructure.structure_id, structure_id))
    assert synced is not None
    student = User(
        email=f"fin+p5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    assessment = await create_fee_assessment(
        scope,
        FeeAssessmentCreate(
            student_user_id=str(student.id),
            structure_id=structure_id,
            academic_year_label="2025",
            semester_label="Odd",
        ),
    )
    demand = await StudentFeeDemand.find_one(Eq(StudentFeeDemand.tenant_id, tenant.id), Eq(StudentFeeDemand.demand_id, assessment["demand_id"]))
    assert demand is not None
    idem = f"idem_{suffix}"
    first = await record_offline_collection(
        scope,
        OfflineCollectionCreate(
            student_user_id=str(student.id),
            demand_id=assessment["demand_id"],
            amount=assessment["net_amount"],
            idempotency_key=idem,
            offline_reference="CASH-001",
        ),
    )
    assert first["status"] == PaymentTransactionStatus.SUCCESS.value
    second = await record_offline_collection(
        scope,
        OfflineCollectionCreate(
            student_user_id=str(student.id),
            demand_id=assessment["demand_id"],
            amount=assessment["net_amount"],
            idempotency_key=idem,
            offline_reference="CASH-001",
        ),
    )
    assert second.get("duplicate") is True
    count = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant.id)).count()
    assert count == 1


@pytest.mark.anyio
async def test_examination_permission_denied(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, _ = await _seed_admin(suffix)
    faculty = User(
        email=f"facdeny+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await faculty.insert()
    scope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    with pytest.raises(AppError) as exc:
        await upsert_examination_config(
            scope,
            ExaminationConfigUpsert(season_id="x", title="X", academic_year_label="2025", semester_label="Odd"),
        )
    assert exc.value.status_code == 403
    assert Permission.EXAMINATION_ADMIN_CONFIG not in scope.effective_permissions
