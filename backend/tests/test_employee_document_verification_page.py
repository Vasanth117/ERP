"""Employee document verification (CA 07.11)."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.employee_document_verification_page_service import (
    get_employee_document_verification_page,
    save_employee_document_decision,
    verify_all_employee_documents,
)
from app.modules.college_admin.faculty_admin_models import FacultyDocumentReference
from app.modules.college_admin.schemas import EmployeeDocumentVerificationDecisionPayload
from app.modules.hr.document_models import HrEmployeeDocument
from app.modules.hr.enums import HrEmployeeDocumentStatus
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


async def _scope(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College EDV {suffix}", code=f"edv_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+edv+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    employee = User(
        email=f"staff+edv+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dr. Nisha Varma",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await employee.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, employee, scope


@pytest.mark.anyio
async def test_employee_document_verification_page_loads(db_ready):
    tenant, employee, scope = await _scope(uuid4().hex[:8])
    now = utcnow()
    doc = HrEmployeeDocument(
        tenant_id=tenant.id,
        employee_user_id=employee.id,
        category_code="qualification",
        document_code="phd_cert",
        title="Ph.D. certificate",
        storage_key="s3/key",
        file_name="Ph.D. certificate.pdf",
        mime_type="application/pdf",
        file_size=1_260_000,
        status=HrEmployeeDocumentStatus.PENDING_VERIFICATION,
        submitted_at=now,
    )
    await doc.insert()
    fac = FacultyDocumentReference(
        tenant_id=tenant.id,
        user_id=employee.id,
        label="Experience letter",
        file_id="file-1",
        authorized=False,
    )
    await fac.insert()

    page = await get_employee_document_verification_page(scope)
    assert page.page_title == "Employee Document Verification"
    assert len(page.kpis) == 4
    assert page.table_headers == ["Employee", "Document", "Uploaded", "Status"]
    assert len(page.document_rows) >= 2
    assert page.document_rows[0].employee_name == "Dr. Nisha Varma"
    key = page.document_rows[0].document_id
    page2 = await get_employee_document_verification_page(scope, document_id=key)
    assert page2.selected_document_id == key
    assert page2.preview_file_name is not None


@pytest.mark.anyio
async def test_employee_document_verification_decide_and_verify_all(db_ready):
    tenant, employee, scope = await _scope(uuid4().hex[:8])
    doc = HrEmployeeDocument(
        tenant_id=tenant.id,
        employee_user_id=employee.id,
        category_code="joining",
        document_code="contract",
        title="Contract copy",
        storage_key="s3/key2",
        file_name="contract.pdf",
        mime_type="application/pdf",
        file_size=2048,
        status=HrEmployeeDocumentStatus.PENDING_VERIFICATION,
    )
    await doc.insert()
    row_key = f"hr:{doc.id}"

    updated = await save_employee_document_decision(
        scope,
        EmployeeDocumentVerificationDecisionPayload(document_id=row_key, result="verified"),
    )
    assert any(r.document_id == row_key and r.status_label == "Verified" for r in updated.document_rows)

    pending = HrEmployeeDocument(
        tenant_id=tenant.id,
        employee_user_id=employee.id,
        category_code="id",
        document_code="id_proof",
        title="ID proof",
        storage_key="s3/key3",
        file_name="id.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status=HrEmployeeDocumentStatus.PENDING_VERIFICATION,
    )
    await pending.insert()

    bulk = await verify_all_employee_documents(scope, None)
    assert bulk.kpis[0].value == "0"