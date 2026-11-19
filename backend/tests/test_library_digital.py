"""Digital library and e-resources tests."""

import base64
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.library.catalogue_schemas import CatalogueRecordCreate
from app.modules.library.catalogue_service import create_catalogue_record
from app.modules.library.digital_enums import DigitalResourceType
from app.modules.library.digital_schemas import DigitalFileUpload, DigitalResourceCreate, DigitalResourceUpdate
from app.modules.library.digital_service import (
    assert_resource_access,
    download_digital_resource,
    external_link_for_resource,
    list_patron_digital_resources,
    register_digital_resource,
    search_digital_resources,
    update_digital_resource,
    upload_digital_file,
)
from app.modules.library.member_enums import LibraryMemberCategory
from app.modules.library.member_schemas import MemberRegisterRequest
from app.modules.library.member_service import register_member
from app.modules.tenants.models import Tenant

_PDF = base64.b64encode(b"%PDF-1.4 test digital").decode("ascii")


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


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


async def _seed(suffix: str) -> tuple[AccessScope, AccessScope, User, User]:
    tenant = Tenant(name=f"Dig {suffix}", code=f"dig_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+dig+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+dig+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Lib",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"stu+dig+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await librarian.insert()
    await student.insert()
    return _scope(librarian, Role.LIBRARIAN), _scope(student, Role.STUDENT), librarian, student


@pytest.mark.anyio
async def test_register_metadata_and_search(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, _, _ = await _seed(suffix)
    book_id = f"B-{suffix}"
    await create_catalogue_record(lib_scope, CatalogueRecordCreate(book_id=book_id, title="Ref Book", authors=["A"]))
    created = await register_digital_resource(
        lib_scope,
        DigitalResourceCreate(
            title="Algorithms",
            resource_type=DigitalResourceType.REFERENCE,
            category="CS",
            book_id=book_id,
            published=True,
            requires_membership=False,
        ),
    )
    assert created.book_id == book_id
    page = await search_digital_resources(lib_scope, Pagination(offset=0, limit=20), q="Algo", category="CS")
    assert page.total >= 1
    with pytest.raises(AppError) as dup:
        await register_digital_resource(lib_scope, DigitalResourceCreate(resource_id=created.resource_id, title="Dup"))
    assert dup.value.status_code == 409


@pytest.mark.anyio
async def test_expired_license_and_secure_download(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, stu_scope, _, student = await _seed(suffix)
    rid = f"res_{suffix}"
    doc = await register_digital_resource(
        lib_scope,
        DigitalResourceCreate(
            resource_id=rid,
            title="Licensed PDF",
            published=True,
            requires_membership=False,
            license_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        ),
    )
    await upload_digital_file(
        lib_scope,
        doc.resource_id,
        DigitalFileUpload(file_name="book.pdf", mime_type="application/pdf", file_content_base64=_PDF),
    )
    with pytest.raises(AppError) as expired:
        await assert_resource_access(stu_scope, student, doc.resource_id, for_download=True)
    assert expired.value.status_code == 403
    await update_digital_resource(
        lib_scope,
        doc.resource_id,
        DigitalResourceUpdate(license_expires_at=datetime.now(timezone.utc) + timedelta(days=30)),
    )
    out = await download_digital_resource(stu_scope, student, doc.resource_id)
    assert out.content_type == "application/pdf"
    assert base64.b64decode(out.content_base64).startswith(b"%PDF")


@pytest.mark.anyio
async def test_membership_eligibility_and_download_limit(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, stu_scope, _, student = await _seed(suffix)
    await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student.id), member_category=LibraryMemberCategory.STUDENT))
    created = await register_digital_resource(
        lib_scope,
        DigitalResourceCreate(title="Members only", published=True, requires_membership=True, max_downloads_per_user=1),
    )
    await upload_digital_file(
        lib_scope,
        created.resource_id,
        DigitalFileUpload(file_name="one.pdf", mime_type="application/pdf", file_content_base64=_PDF),
    )
    outsider = User(
        email=f"out+dig+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Out",
        role=Role.STUDENT,
        tenant_id=student.tenant_id,
    )
    await outsider.insert()
    out_scope = _scope(outsider, Role.STUDENT)
    with pytest.raises(AppError) as no_member:
        await assert_resource_access(out_scope, outsider, created.resource_id)
    assert no_member.value.status_code == 403
    await download_digital_resource(stu_scope, student, created.resource_id)
    with pytest.raises(AppError) as limit:
        await download_digital_resource(stu_scope, student, created.resource_id)
    assert limit.value.status_code == 403
    patrons = await list_patron_digital_resources(stu_scope, student)
    assert any(p.resource_id == created.resource_id for p in patrons)


@pytest.mark.anyio
async def test_external_link_and_unauthorized_manage(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, stu_scope, _, student = await _seed(suffix)
    created = await register_digital_resource(
        lib_scope,
        DigitalResourceCreate(
            title="Open Journal",
            published=True,
            requires_membership=False,
            external_url="https://example.org/journal",
        ),
    )
    link = await external_link_for_resource(stu_scope, student, created.resource_id)
    assert link.url.startswith("https://")
    with pytest.raises(AppError) as denied:
        await register_digital_resource(stu_scope, DigitalResourceCreate(title="Hack", published=True))
    assert denied.value.status_code == 403