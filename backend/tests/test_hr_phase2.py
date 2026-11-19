"""HR staff portal phase 2 — organization and documents."""

import io
from datetime import date
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.identity_schemas import InstitutionDepartmentCreate
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.document_service import employee_document_overview, list_document_categories, upload_employee_document, verify_document
from app.modules.hr.document_schemas import DocumentUploadMeta, DocumentVerificationDecision
from app.modules.hr.employee_profile_schemas import EmployeeRegister
from app.modules.hr.employee_profile_service import register_employee
from app.modules.hr.enums import HrEmployeeDocumentStatus
from app.modules.hr.organization_schemas import EmployeeTransferCreate, HrDesignationCreate
from app.modules.hr.organization_service import (
    create_transfer_request,
    get_organization_overview,
    hr_create_department,
    review_transfer,
    upsert_designation,
)
from app.modules.hr.organization_schemas import TransferApproval
from app.modules.tenants.models import Department, Tenant


class _Upload:
    def __init__(self, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self):
        return self._content


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
    tenant = Tenant(name=f"HR2 {suffix}", code=f"hr2_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="Administration", code=f"ADM-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"C{suffix}", name="Main", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hr2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    scope = _scope(hr_user, Role.HR_STAFF)
    return tenant, hr_user, scope, dept, campus


@pytest.mark.asyncio
async def test_organization_and_transfer(db_ready):
    suffix = uuid4().hex[:8]
    tenant, hr_user, scope, dept, campus = await _seed(suffix)
    parent = await hr_create_department(
        scope,
        InstitutionDepartmentCreate(department_code=f"P{suffix}", name="Parent Dept", campus_ids=[str(campus.id)]),
    )
    child = await hr_create_department(
        scope,
        InstitutionDepartmentCreate(
            department_code=f"C{suffix}",
            name="Child Dept",
            parent_department_id=parent.department_id,
            campus_ids=[str(campus.id)],
        ),
    )
    overview = await get_organization_overview(scope)
    assert overview.department_count >= 2
    await upsert_designation(scope, HrDesignationCreate(designation_code=f"D{suffix}", name="Senior Officer", hierarchy_level=2))
    manager = await register_employee(
        scope,
        EmployeeRegister(
            employee_code=f"M-{suffix}",
            first_name="Manager",
            last_name="One",
            official_email=f"mgr.{suffix}@example.com",
            password="password1234567890",
            mobile_number="9111111111",
            joining_date=date.today(),
            employee_category="ADMIN",
            employment_type="FULL_TIME",
            department_id=str(dept.id),
            designation="Senior Officer",
            campus_id=str(campus.id),
        ),
    )
    employee = await register_employee(
        scope,
        EmployeeRegister(
            employee_code=f"E-{suffix}",
            first_name="Staff",
            last_name="Member",
            official_email=f"emp.{suffix}@example.com",
            password="password1234567890",
            mobile_number="9222222222",
            joining_date=date.today(),
            employee_category="ADMIN",
            employment_type="FULL_TIME",
            department_id=str(dept.id),
            designation="Clerk",
            campus_id=str(campus.id),
        ),
    )
    transfer = await create_transfer_request(
        scope,
        employee.user_id,
        EmployeeTransferCreate(
            to_institution_department_id=child.department_id,
            effective_date=date.today(),
            reason="Department restructuring",
            requires_approval=True,
        ),
    )
    assert transfer.status.value == "pending_approval"
    approved = await review_transfer(scope, transfer.transfer_id, TransferApproval(decision="approved", note="ok"))
    assert approved.status.value == "applied"


@pytest.mark.asyncio
async def test_document_upload_and_verify(db_ready):
    suffix = uuid4().hex[:8]
    _, hr_user, scope, dept, campus = await _seed(suffix)
    profile = await register_employee(
        scope,
        EmployeeRegister(
            employee_code=f"D-{suffix}",
            first_name="Doc",
            last_name="Owner",
            official_email=f"doc.{suffix}@example.com",
            password="password1234567890",
            mobile_number="9333333333",
            joining_date=date.today(),
            employee_category="ADMIN",
            employment_type="FULL_TIME",
            department_id=str(dept.id),
            designation="Clerk",
            campus_id=str(campus.id),
        ),
    )
    cats = await list_document_categories(scope)
    assert len(cats) >= 5
    upload = _Upload("id-proof.pdf", b"%PDF-1.4 test content", "application/pdf")
    meta = DocumentUploadMeta(
        employee_user_id=profile.user_id,
        category_code="GOV_ID",
        title="Aadhaar",
        submit_for_verification=True,
    )
    doc = await upload_employee_document(scope, hr_user, meta, upload)
    assert doc.status == HrEmployeeDocumentStatus.PENDING_VERIFICATION
    verified = await verify_document(
        scope,
        doc.document_id,
        DocumentVerificationDecision(decision=HrEmployeeDocumentStatus.VERIFIED),
    )
    assert verified.status == HrEmployeeDocumentStatus.VERIFIED
    overview = await employee_document_overview(scope, profile.user_id)
    assert overview.verified >= 1