"""Student document verification page."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.schemas import StudentDocumentVerificationDecisionPayload
from app.modules.college_admin.student_admin_models import AdmissionStatus, StudentAdmission, StudentLifecycleStatus, StudentRecord
from app.modules.college_admin.student_document_verification_page_service import (
    get_student_document_verification_page,
    save_document_verification_decision,
)
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


async def _seed(suffix: str) -> tuple[Tenant, StudentRecord, AccessScope]:
    tenant = Tenant(name=f"College DocVer {suffix}", code=f"dv_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+dv+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admissions Office",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    student = User(
        email=f"student+dv+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Aarav Menon",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    admission = StudentAdmission(
        tenant_id=tenant.id,
        admission_number=f"ADM-{suffix[:4]}",
        applicant_name="Aarav Menon",
        applicant_email=f"student+dv+{suffix}@example.com",
        programme_code="CSE",
        academic_year_code="2026-27",
        status=AdmissionStatus.CONFIRMED,
        metadata={
            "documents": [
                {
                    "label": "Community certificate",
                    "file_name": "Community certificate.pdf",
                    "uploaded_at": "2022-07-19",
                    "size_kb": 240,
                    "status": "pending",
                }
            ]
        },
    )
    await admission.insert()
    record = StudentRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        admission_id=admission.id,
        roll_number=f"22CS{suffix[:4]}",
        programme_code="CSE",
        lifecycle_status=StudentLifecycleStatus.ACTIVE,
    )
    await record.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, record, scope


@pytest.mark.anyio
async def test_document_verification_page_lists_docs(db_ready):
    suffix = uuid4().hex[:8]
    _, record, scope = await _seed(suffix)
    page = await get_student_document_verification_page(scope, record_id=str(record.id))
    assert page.page_title == "Student Document Verification"
    assert len(page.document_rows) == 1
    assert page.document_rows[0].document_label == "Community certificate"


@pytest.mark.anyio
async def test_document_verification_decision(db_ready):
    suffix = uuid4().hex[:8]
    _, record, scope = await _seed(suffix)
    page = await get_student_document_verification_page(scope, record_id=str(record.id))
    key = page.document_rows[0].document_key
    updated = await save_document_verification_decision(
        scope,
        StudentDocumentVerificationDecisionPayload(
            record_id=str(record.id),
            document_key=key,
            result="needs_correction",
            remarks="Seal not visible",
        ),
    )
    assert updated.decision_remarks == "Seal not visible"