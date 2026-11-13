"""Student library portal."""

from datetime import date

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.library.library_enums import LibraryCirculationStatus
from app.modules.students.integrations import library_reader
from app.modules.students.policy import require_student_scope
from app.modules.students.student_portal_models import StudentLibraryActivityView
from app.modules.students.student_portal_schemas import (
    DigitalResourceRead,
    LibraryCatalogRead,
    LibraryFineRead,
    LibraryIssuedBookRead,
)


async def search_catalogue(
    scope: AccessScope,
    user: User,
    *,
    q: str | None = None,
    limit: int = 50,
) -> list[LibraryCatalogRead]:
    authorize(scope, Permission.STUDENT_LIBRARY_READ)
    tenant_id = require_student_scope(scope)
    items = await library_reader.catalogue(tenant_id, q=q, limit=limit)
    counts = await library_reader.availability_counts(tenant_id, [i.book_id for i in items])
    return [
        LibraryCatalogRead(
            book_id=i.book_id,
            title=i.title,
            authors=i.authors,
            isbn=i.isbn,
            category=i.category,
            available_copies=counts.get(i.book_id, 0),
        )
        for i in items
    ]


async def book_availability(scope: AccessScope, user: User, book_id: str) -> dict:
    authorize(scope, Permission.STUDENT_LIBRARY_READ)
    tenant_id = require_student_scope(scope)
    counts = await library_reader.availability_counts(tenant_id, [book_id])
    return {"book_id": book_id, "available_copies": counts.get(book_id, 0)}


async def issued_books(scope: AccessScope, user: User) -> list[LibraryIssuedBookRead]:
    authorize(scope, Permission.STUDENT_LIBRARY_READ)
    tenant_id = require_student_scope(scope)
    rows = await library_reader.active_circulations(tenant_id, user.id)
    today = date.today()
    return [
        LibraryIssuedBookRead(
            circulation_id=r.circulation_id,
            book_id=r.book_id,
            title=r.title,
            issued_at=r.issued_at,
            due_at=r.due_at,
            status=r.status.value,
            overdue=r.status == LibraryCirculationStatus.OVERDUE or r.due_at < today,
        )
        for r in rows
    ]


async def due_dates(scope: AccessScope, user: User) -> list[dict]:
    authorize(scope, Permission.STUDENT_LIBRARY_READ)
    tenant_id = require_student_scope(scope)
    rows = await library_reader.active_circulations(tenant_id, user.id)
    return [{"circulation_id": r.circulation_id, "title": r.title, "due_at": r.due_at} for r in rows]


async def overdue_books(scope: AccessScope, user: User) -> list[LibraryIssuedBookRead]:
    issued = await issued_books(scope, user)
    return [r for r in issued if r.overdue]


async def reservations(scope: AccessScope, user: User) -> list[dict]:
    authorize(scope, Permission.STUDENT_LIBRARY_READ)
    tenant_id = require_student_scope(scope)
    rows = await library_reader.reservations_for_student(tenant_id, user.id)
    return [
        {
            "reservation_id": r.reservation_id,
            "book_id": r.book_id,
            "title": r.title,
            "status": r.status.value,
            "queue_position": r.queue_position,
        }
        for r in rows
    ]


async def fines(scope: AccessScope, user: User) -> list[LibraryFineRead]:
    authorize(scope, Permission.STUDENT_LIBRARY_READ)
    tenant_id = require_student_scope(scope)
    rows = await library_reader.fines_for_student(tenant_id, user.id)
    return [
        LibraryFineRead(fine_id=r.fine_id, amount=r.amount, reason=r.reason, status=r.status.value) for r in rows
    ]


async def digital_resources(scope: AccessScope, user: User) -> list[DigitalResourceRead]:
    authorize(scope, Permission.STUDENT_LIBRARY_READ)
    tenant_id = require_student_scope(scope)
    rows = await library_reader.digital_resources(tenant_id)
    await StudentLibraryActivityView(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type="digital_browse",
        reference_id="catalogue",
        title="Digital library",
    ).insert()
    return [
        DigitalResourceRead(resource_id=r.resource_id, title=r.title, description=r.description, url=r.url)
        for r in rows
    ]


async def borrowing_history(scope: AccessScope, user: User, limit: int = 100) -> list[dict]:
    authorize(scope, Permission.STUDENT_LIBRARY_READ)
    tenant_id = require_student_scope(scope)
    rows = await library_reader.borrowing_history(tenant_id, user.id, limit=limit)
    await record_audit(
        actor_id=scope.user_id,
        action="student.library.history_viewed",
        resource_type="library_circulation",
        resource_id=str(user.id),
        tenant_id=tenant_id,
    )
    return [
        {
            "circulation_id": r.circulation_id,
            "book_id": r.book_id,
            "title": r.title,
            "issued_at": r.issued_at,
            "due_at": r.due_at,
            "returned_at": r.returned_at,
            "status": r.status.value,
        }
        for r in rows
    ]


async def log_catalogue_view(scope: AccessScope, user: User, book_id: str, title: str) -> None:
    authorize(scope, Permission.STUDENT_LIBRARY_READ)
    tenant_id = require_student_scope(scope)
    await StudentLibraryActivityView(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type="catalogue_view",
        reference_id=book_id,
        title=title,
    ).insert()
