"""Accounts / Finance Staff — Phase 1 (dashboard + fee structures)."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.accounts_finance.dashboard_service import get_finance_dashboard
from app.modules.accounts_finance.enums import FeeCategoryClassification, FeeStructureApprovalAction, FeeStructureLifecycleStatus
from app.modules.accounts_finance.fee_category_service import get_fee_category, list_fee_categories, upsert_fee_category
from app.modules.accounts_finance.fee_structure_service import create_fee_structure, get_fee_structure, transition_fee_structure
from app.modules.accounts_finance.schemas import FeeCategoryUpsert, FeeStructureComponentInput, FeeStructureCreate, FeeStructureTransition
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.finance_admin_models import StudentFeeAssessment
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand, StudentFeeInvoice, StudentFeeStructure
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


async def _seed_finance_staff(suffix: str, *, role: Role = Role.FINANCE_STAFF) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"Finance Staff {suffix}", code=f"fin_{suffix}")
    await tenant.insert()
    user = User(
        email=f"finance+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Finance Staff",
        role=role,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )
    await AcademicYear(
        tenant_id=tenant.id,
        year_code="2025-26",
        label="2025-26",
        start_date=date(2025, 6, 1),
        end_date=date(2026, 5, 31),
        is_current=True,
    ).insert()
    await AcademicProgramme(tenant_id=tenant.id, programme_code="BSC-CS", name="BSc Computer Science").insert()
    return tenant, user, scope


@pytest.mark.anyio
async def test_fee_category_duplicate_prevention(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, scope = await _seed_finance_staff(suffix)
    payload = FeeCategoryUpsert(fee_code="TUITION", name="Tuition Fees", classification=FeeCategoryClassification.TUITION)
    await upsert_fee_category(scope, payload)
    read = await get_fee_category(scope, "TUITION")
    assert read.fee_code == "TUITION"
    page = await list_fee_categories(scope, Pagination(offset=0, limit=20))
    assert page.total == 1


@pytest.mark.anyio
async def test_fee_structure_lifecycle_and_sync(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_finance_staff(suffix)
    await upsert_fee_category(
        scope,
        FeeCategoryUpsert(fee_code="TUITION", name="Tuition", classification=FeeCategoryClassification.TUITION),
    )
    struct = FeeStructureCreate(
        structure_id=f"struct_{suffix}",
        academic_year_label="2025-26",
        semester_label="Odd",
        programme_code="BSC-CS",
        components=[FeeStructureComponentInput(fee_category_code="TUITION", amount=50000)],
    )
    created = await create_fee_structure(scope, struct)
    assert created.status == FeeStructureLifecycleStatus.DRAFT
    await transition_fee_structure(
        scope,
        created.structure_id,
        FeeStructureTransition(action=FeeStructureApprovalAction.SUBMIT),
    )
    await transition_fee_structure(
        scope,
        created.structure_id,
        FeeStructureTransition(action=FeeStructureApprovalAction.APPROVE),
    )
    active = await transition_fee_structure(
        scope,
        created.structure_id,
        FeeStructureTransition(action=FeeStructureApprovalAction.ACTIVATE),
    )
    assert active.status == FeeStructureLifecycleStatus.ACTIVE
    synced = await StudentFeeStructure.find_one(
        Eq(StudentFeeStructure.tenant_id, tenant.id),
        Eq(StudentFeeStructure.structure_id, created.structure_id),
    )
    assert synced is not None
    assert synced.total_amount == 50000


@pytest.mark.anyio
async def test_accounts_staff_cannot_approve(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, scope = await _seed_finance_staff(suffix, role=Role.ACCOUNTS_STAFF)
    await upsert_fee_category(scope, FeeCategoryUpsert(fee_code="TUITION", name="Tuition", classification=FeeCategoryClassification.TUITION))
    created = await create_fee_structure(
        scope,
        FeeStructureCreate(
            structure_id=f"struct_{suffix}",
            academic_year_label="2025-26",
            semester_label="Odd",
            programme_code="BSC-CS",
            components=[FeeStructureComponentInput(fee_category_code="TUITION", amount=1000)],
        ),
    )
    await transition_fee_structure(scope, created.structure_id, FeeStructureTransition(action=FeeStructureApprovalAction.SUBMIT))
    with pytest.raises(AppError) as exc:
        await transition_fee_structure(
            scope,
            created.structure_id,
            FeeStructureTransition(action=FeeStructureApprovalAction.APPROVE),
        )
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_dashboard_verified_collections_exclude_pending(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_finance_staff(suffix)
    student = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    student_id = student.id
    await StudentFeeAssessment(
        tenant_id=tenant.id,
        student_user_id=student_id,
        assessment_id=f"assess_{suffix}",
        structure_id="s1",
        academic_year_label="2025-26",
        semester_label="Odd",
        assessed_amount=10000,
        concession_amount=0,
        net_amount=10000,
    ).insert()
    await StudentFeeInvoice(
        tenant_id=tenant.id,
        student_user_id=student_id,
        invoice_id=f"inv_{suffix}",
        amount=10000,
        issued_at=date.today(),
        due_date=date.today() + timedelta(days=30),
        published=True,
    ).insert()
    await StudentFeeDemand(
        tenant_id=tenant.id,
        student_user_id=student_id,
        demand_id=f"dem_{suffix}",
        academic_year_label="2025-26",
        semester_label="Odd",
        description="Fee",
        amount=10000,
        due_date=date.today() + timedelta(days=30),
        status=FeeDemandStatus.OPEN,
    ).insert()
    await PaymentTransaction(
        tenant_id=tenant.id,
        student_user_id=student_id,
        transaction_id=f"tx_ok_{suffix}",
        idempotency_key=f"idem_ok_{suffix}",
        amount=5000,
        status=PaymentTransactionStatus.SUCCESS,
        payment_mode="offline",
        webhook_verified=False,
    ).insert()
    await PaymentTransaction(
        tenant_id=tenant.id,
        student_user_id=student_id,
        transaction_id=f"tx_pending_{suffix}",
        idempotency_key=f"idem_p_{suffix}",
        amount=3000,
        status=PaymentTransactionStatus.PENDING,
        payment_mode="online",
    ).insert()
    dashboard = await get_finance_dashboard(scope)
    assert dashboard.financial.total_verified_collections.value == 5000
    assert dashboard.financial.total_pending_payments.value >= 1


@pytest.mark.anyio
async def test_cross_tenant_isolation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant_a, _, scope_a = await _seed_finance_staff(f"{suffix}a")
    _, _, scope_b = await _seed_finance_staff(f"{suffix}b")
    await upsert_fee_category(scope_a, FeeCategoryUpsert(fee_code="TUITION", name="Tuition", classification=FeeCategoryClassification.TUITION))
    with pytest.raises(AppError) as exc:
        await get_fee_category(scope_b, "TUITION")
    assert exc.value.status_code == 404
    _ = tenant_a