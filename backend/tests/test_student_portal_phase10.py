"""Student phase 10 — library, residence, services, communication, reports."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.hostel.hostel_enums import HostelApplicationStatus
from app.modules.hostel.hostel_models import HostelApplication, HostelRoomAllocation
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryCopyStatus
from app.modules.library.library_models import LibraryCatalogItem, LibraryCirculation, LibraryCopy
from app.modules.student_services.catalog_models import InstitutionalService
from app.modules.students.student_library_service import issued_books, search_catalogue
from app.modules.students.student_residence_service import hostel_room_allocation, submit_hostel_request
from app.modules.students.student_portal_schemas import HostelRequestInput
from app.modules.students.student_reports_service import generate_report
from app.modules.students.student_portal_schemas import ReportGenerateInput
from app.modules.students.student_services_hub_service import list_services, submit_service_request
from app.modules.students.student_portal_schemas import ServiceRequestInput
from app.modules.transport.transport_models import TransportAllocation, TransportRoute
from app.modules.auth.models import User
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


async def _seed(suffix: str) -> tuple[Tenant, User, User, AccessScope]:
    tenant = Tenant(name="College", code=f"s10_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    user = User(
        email=f"s10+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await user.insert()
    other = User(
        email=f"s10other+{suffix}@example.com",
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
    return tenant, user, other, scope


@pytest.mark.anyio
async def test_library_catalogue_and_issued(db_ready) -> None:
    tenant, user, other, scope = await _seed("lib")
    book_id = f"bk_{uuid4().hex[:8]}"
    await LibraryCatalogItem(
        tenant_id=tenant.id,
        book_id=book_id,
        title="Algorithms",
        authors=["CLRS"],
        published=True,
    ).insert()
    await LibraryCopy(tenant_id=tenant.id, copy_id="cp1", book_id=book_id, barcode="B1", status=LibraryCopyStatus.AVAILABLE).insert()
    await LibraryCirculation(
        tenant_id=tenant.id,
        circulation_id="circ1",
        student_user_id=user.id,
        book_id=book_id,
        copy_id="cp1",
        title="Algorithms",
        issued_at=datetime.now(timezone.utc),
        due_at=date.today() + timedelta(days=7),
        status=LibraryCirculationStatus.ACTIVE,
    ).insert()
    catalogue = await search_catalogue(scope, user)
    assert catalogue[0].available_copies == 1
    issued = await issued_books(scope, user)
    assert len(issued) == 1
    other_scope = AccessScope(
        role=Role.STUDENT,
        user_id=other.id,
        tenant_id=tenant.id,
        department_id=other.department_id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    assert len(await issued_books(other_scope, other)) == 0


@pytest.mark.anyio
async def test_hostel_allocation_and_request(db_ready) -> None:
    tenant, user, _, scope = await _seed("hst")
    await HostelRoomAllocation(
        tenant_id=tenant.id,
        student_user_id=user.id,
        allocation_id="ha1",
        hostel_name="Main",
        block="A",
        room_number="101",
        bed_label="B1",
        fee_amount=25000,
    ).insert()
    alloc = await hostel_room_allocation(scope, user)
    assert alloc is not None
    assert alloc.room_number == "101"
    result = await submit_hostel_request(
        scope,
        user,
        HostelRequestInput(request_type="maintenance", description="Fan not working"),
    )
    assert result["status"] == "submitted"


@pytest.mark.anyio
async def test_transport_allocation(db_ready) -> None:
    tenant, user, _, scope = await _seed("trn")
    route_id = f"rt_{uuid4().hex[:6]}"
    await TransportRoute(tenant_id=tenant.id, route_id=route_id, name="City", fee_amount=12000).insert()
    await TransportAllocation(
        tenant_id=tenant.id,
        student_user_id=user.id,
        allocation_id="ta1",
        route_id=route_id,
        route_name="City",
        pickup_stop="Gate",
        drop_stop="Campus",
        fee_amount=12000,
    ).insert()
    from app.modules.students.student_residence_service import transport_allocation

    data = await transport_allocation(scope, user)
    assert data is not None
    assert data.pickup_stop == "Gate"


@pytest.mark.anyio
async def test_service_request(db_ready) -> None:
    tenant, user, _, scope = await _seed("svc")
    sid = f"svc_{uuid4().hex[:6]}"
    await InstitutionalService(
        tenant_id=tenant.id,
        service_id=sid,
        title="ID Card",
        category="general",
        enabled=True,
    ).insert()
    rows = await list_services(scope, user)
    assert rows[0].service_id == sid
    created = await submit_service_request(
        scope,
        user,
        ServiceRequestInput(service_id=sid, title="Reissue ID", description="Lost card"),
    )
    assert created.status == "submitted"


@pytest.mark.anyio
async def test_personal_report_generation(db_ready) -> None:
    tenant, user, _, scope = await _seed("rpt")
    export = await generate_report(scope, user, ReportGenerateInput(report_type="course_registration"))
    assert export.export_id.startswith("rpt_")
    assert export.status in {"ready", "failed", "pending"}
