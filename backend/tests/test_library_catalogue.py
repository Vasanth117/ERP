"""Book catalogue management tests."""

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
from app.modules.library.catalogue_isbn import normalize_isbn10, normalize_isbn13
from app.modules.library.catalogue_schemas import CatalogueBulkImportRequest, CatalogueRecordCreate, CatalogueRecordUpdate
from app.modules.library.catalogue_service import (
    archive_catalogue_record,
    bulk_import_catalogue,
    catalogue_history,
    check_duplicates,
    create_catalogue_record,
    get_catalogue_record,
    search_catalogue_records,
    update_catalogue_record,
)
from app.modules.library.facility_schemas import InstitutionLibraryCreate
from app.modules.library.facility_service import create_library
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


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


def _valid_isbn10() -> str:
    return "0306406152"


def _valid_isbn13() -> str:
    return "9780306406157"


@pytest.mark.anyio
async def test_isbn_validation() -> None:
    assert normalize_isbn10("0-306-40615-2") == _valid_isbn10()
    assert normalize_isbn13("978-0-306-40615-7") == _valid_isbn13()
    with pytest.raises(AppError):
        normalize_isbn10("123")


@pytest.mark.anyio
async def test_catalogue_crud_and_archive(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"Cat {suffix}", code=f"cat_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+cat+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib_code = f"L{suffix}"
    await create_library(scope, InstitutionLibraryCreate(library_code=lib_code, name="Central"))
    created = await create_catalogue_record(
        scope,
        CatalogueRecordCreate(
            book_id=f"B-{suffix}",
            title="Introduction to Algorithms",
            subtitle="A modern approach",
            isbn=_valid_isbn10(),
            isbn13=_valid_isbn13(),
            authors=["Cormen", "Leiserson"],
            publisher="MIT Press",
            publication_year=2009,
            category="CS",
            subcategory="Algorithms",
            language="en",
            primary_library_code=lib_code,
        ),
    )
    assert created.isbn13 == _valid_isbn13()
    fetched = await get_catalogue_record(scope, created.book_id)
    assert fetched.title == created.title
    updated = await update_catalogue_record(
        scope,
        created.book_id,
        CatalogueRecordUpdate(description="Graduate-level text"),
    )
    assert updated.description == "Graduate-level text"
    archived = await archive_catalogue_record(scope, created.book_id)
    assert archived.archived is True
    assert archived.published is False
    history = await catalogue_history(scope, created.book_id, Pagination(limit=10, offset=0))
    assert history.total >= 3


@pytest.mark.anyio
async def test_duplicate_isbn_and_search(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"Dup {suffix}", code=f"dup_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+dup+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = _scope(admin, Role.COLLEGE_ADMIN)
    isbn13 = _valid_isbn13()
    await create_catalogue_record(
        scope,
        CatalogueRecordCreate(book_id=f"B1-{suffix}", title="Book One", isbn13=isbn13, authors=["A"]),
    )
    dup = await check_duplicates(scope, isbn13=isbn13)
    assert len(dup.duplicates) == 1
    with pytest.raises(AppError) as exc:
        await create_catalogue_record(
            scope,
            CatalogueRecordCreate(book_id=f"B2-{suffix}", title="Book Two", isbn13=isbn13, authors=["B"]),
        )
    assert exc.value.status_code == 409
    results = await search_catalogue_records(scope, Pagination(limit=20, offset=0), q="Book One")
    assert results.total == 1


@pytest.mark.anyio
async def test_bulk_import_dry_run(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"Bulk {suffix}", code=f"bulk_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+bulk+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = _scope(admin, Role.COLLEGE_ADMIN)
    result = await bulk_import_catalogue(
        scope,
        CatalogueBulkImportRequest(
            dry_run=True,
            items=[
                CatalogueRecordCreate(book_id=f"I1-{suffix}", title="Import 1", authors=["X"]),
                CatalogueRecordCreate(book_id=f"I2-{suffix}", title="Import 2", authors=["Y"], isbn="bad-isbn"),
            ],
        ),
    )
    assert result.created == 1
    assert len(result.errors) == 1


@pytest.mark.anyio
async def test_student_forbidden_and_cross_tenant(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant_a = Tenant(name=f"A {suffix}", code=f"a_{suffix}")
    tenant_b = Tenant(name=f"B {suffix}", code=f"b_{suffix}")
    await tenant_a.insert()
    await tenant_b.insert()
    student = User(
        email=f"stu+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant_a.id,
    )
    admin_b = User(
        email=f"adm+b+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin B",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant_b.id,
    )
    await student.insert()
    await admin_b.insert()
    admin_a = User(
        email=f"adm+a+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin A",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant_a.id,
    )
    await admin_a.insert()
    scope_a = _scope(admin_a, Role.COLLEGE_ADMIN)
    book_id = f"B-{suffix}"
    await create_catalogue_record(scope_a, CatalogueRecordCreate(book_id=book_id, title="Shared Title", authors=["A"]))
    with pytest.raises(AppError) as exc:
        await get_catalogue_record(_scope(student, Role.STUDENT), book_id)
    assert exc.value.status_code == 403
    with pytest.raises(AppError) as exc2:
        await get_catalogue_record(_scope(admin_b, Role.COLLEGE_ADMIN), book_id)
    assert exc2.value.status_code == 404