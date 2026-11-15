"""Department Admin — resource directory and coordination (read-mostly)."""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.enums import TimetableEntryStatus
from app.modules.academics.models import ClassSession, TimetableEntry
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.models import InstitutionCampus
from app.modules.department_admin.calendar_conflict_detection import detect_calendar_conflicts
from app.modules.department_admin.department_scope import department_course_codes, faculty_user_ids_in_department
from app.modules.department_admin.models import (
    DepartmentRequestStatus,
    DepartmentResourceIssue,
    DepartmentResourceIssueStatus,
    DepartmentResourceRequest,
    DepartmentResourceType,
    DepartmentTimetablePlan,
    DepartmentTimetableSlot,
)
from app.modules.department_admin.phase7_schemas import (
    ResourceAvailabilityRead,
    ResourceDirectoryItemRead,
    ResourceIssueCreate,
    ResourceIssueRead,
    ResourceRequestCreate,
    ResourceRequestRead,
    ResourceUtilizationRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.library.library_models import LibraryCatalogItem
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus

UTILIZATION_ADVISORY = (
    "Utilization counts derive from timetable slots and published entries; "
    "no college facility master is configured — booking truth may be incomplete."
)


async def _campus_label(tenant_id: PydanticObjectId) -> str | None:
    campus = await InstitutionCampus.find_one(
        Eq(InstitutionCampus.tenant_id, tenant_id),
        Eq(InstitutionCampus.is_main, True),
    )
    if campus is None:
        campus = await InstitutionCampus.find_one(Eq(InstitutionCampus.tenant_id, tenant_id))
    return campus.name if campus else None


async def _collect_room_lab_resources(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
) -> list[ResourceDirectoryItemRead]:
    location = await _campus_label(tenant_id)
    rooms: dict[str, ResourceDirectoryItemRead] = {}
    labs: dict[str, ResourceDirectoryItemRead] = {}
    plan_ids = [p.id for p in await DepartmentTimetablePlan.find({"tenant_id": tenant_id, "central_department_id": central_id}).to_list()]
    if plan_ids:
        for slot in await DepartmentTimetableSlot.find({"tenant_id": tenant_id, "plan_id": {"$in": plan_ids}}).to_list():
            if slot.room:
                key = slot.room.strip().upper()
                if key not in rooms:
                    rooms[key] = ResourceDirectoryItemRead(
                        resource_id=f"classroom:{key}",
                        name=slot.room,
                        resource_type=DepartmentResourceType.CLASSROOM.value,
                        location=location,
                        source="department_timetable_slots",
                    )
            if slot.laboratory:
                key = slot.laboratory.strip().upper()
                if key not in labs:
                    labs[key] = ResourceDirectoryItemRead(
                        resource_id=f"laboratory:{key}",
                        name=slot.laboratory,
                        resource_type=DepartmentResourceType.LABORATORY.value,
                        location=location,
                        source="department_timetable_slots",
                    )
    course_codes = list(await department_course_codes(tenant_id, central_id))
    faculty_ids = list(await faculty_user_ids_in_department(tenant_id, central_id))
    if faculty_ids:
        for entry in await TimetableEntry.find(
            {
                "tenant_id": tenant_id,
                "faculty_user_id": {"$in": faculty_ids},
                "status": TimetableEntryStatus.ACTIVE,
            }
        ).to_list():
            if entry.room:
                key = entry.room.strip().upper()
                if key not in rooms:
                    rooms[key] = ResourceDirectoryItemRead(
                        resource_id=f"classroom:{key}",
                        name=entry.room,
                        resource_type=DepartmentResourceType.CLASSROOM.value,
                        location=location,
                        source="timetable_entries",
                    )
    return list(rooms.values()) + list(labs.values())


async def _collect_equipment(tenant_id: PydanticObjectId) -> list[ResourceDirectoryItemRead]:
    items: list[ResourceDirectoryItemRead] = []
    for row in await LibraryCatalogItem.find(Eq(LibraryCatalogItem.tenant_id, tenant_id)).limit(200).to_list():
        if row.category and row.category.lower() in {"equipment", "lab_equipment", "teaching_aid"}:
            items.append(
                ResourceDirectoryItemRead(
                    resource_id=f"equipment:library:{row.book_id}",
                    name=row.title,
                    resource_type=DepartmentResourceType.EQUIPMENT.value,
                    operational_status="available" if row.published else "inactive",
                    source="library_catalog_items",
                    metadata={"book_id": row.book_id, "category": row.category},
                )
            )
    return items


def _room_lab_from_resource_id(resource_id: str) -> tuple[str | None, str | None]:
    if resource_id.startswith("classroom:"):
        return resource_id.split(":", 1)[1], None
    if resource_id.startswith("laboratory:"):
        return None, resource_id.split(":", 1)[1]
    return None, None


async def list_resources(
    scope: AccessScope,
    user: User,
    *,
    resource_type: str | None,
    pagination: Pagination,
) -> Page[ResourceDirectoryItemRead]:
    authorize(scope, Permission.DEPARTMENT_RESOURCES_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    items = await _collect_room_lab_resources(tenant_id, central_id)
    items.extend(await _collect_equipment(tenant_id))
    if resource_type:
        items = [i for i in items if i.resource_type == resource_type]
    items.sort(key=lambda i: i.name)
    total = len(items)
    page = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=page, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_resource(scope: AccessScope, user: User, resource_id: str) -> ResourceDirectoryItemRead:
    authorize(scope, Permission.DEPARTMENT_RESOURCES_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    items = await _collect_room_lab_resources(tenant_id, central_id)
    items.extend(await _collect_equipment(tenant_id))
    match = next((i for i in items if i.resource_id == resource_id), None)
    if match is None:
        raise AppError(code="NOT_FOUND", message="Resource not found", status_code=404)
    return match


async def resource_availability(
    scope: AccessScope,
    user: User,
    *,
    resource_id: str,
    day: date | None,
) -> ResourceAvailabilityRead:
    authorize(scope, Permission.DEPARTMENT_RESOURCES_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    room, laboratory = _room_lab_from_resource_id(resource_id)
    if not room and not laboratory:
        return ResourceAvailabilityRead(
            resource_id=resource_id,
            available=True,
            note="Availability check applies to classrooms and laboratories only",
        )
    target_day = day or datetime.now(timezone.utc).date()
    start = datetime.combine(target_day, time(0, 0), tzinfo=timezone.utc)
    end = datetime.combine(target_day, time(23, 59, 59), tzinfo=timezone.utc)
    faculty_ids = list(await faculty_user_ids_in_department(tenant_id, central_id))
    timetable = []
    sessions = []
    if faculty_ids:
        timetable = await TimetableEntry.find(
            {
                "tenant_id": tenant_id,
                "faculty_user_id": {"$in": faculty_ids},
                "status": TimetableEntryStatus.ACTIVE,
                "day_of_week": target_day.weekday(),
            }
        ).to_list()
        sessions = await ClassSession.find(
            {
                "tenant_id": tenant_id,
                "faculty_user_id": {"$in": faculty_ids},
                "scheduled_start": {"$lt": end},
                "scheduled_end": {"$gt": start},
            }
        ).to_list()
    conflicts = detect_calendar_conflicts(
        event_id=None,
        starts_at=start,
        ends_at=end,
        room=room.upper() if room else None,
        laboratory=laboratory.upper() if laboratory else None,
        organizer_faculty_id=None,
        peer_events=[],
        timetable_rows=timetable,
        class_sessions=sessions,
    )
    available = len(conflicts) == 0
    return ResourceAvailabilityRead(
        resource_id=resource_id,
        available=available,
        conflicts=conflicts,
        note=UTILIZATION_ADVISORY,
    )


async def list_classrooms(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[ResourceDirectoryItemRead]:
    return await list_resources(scope, user, resource_type=DepartmentResourceType.CLASSROOM.value, pagination=pagination)


async def list_laboratories(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[ResourceDirectoryItemRead]:
    return await list_resources(scope, user, resource_type=DepartmentResourceType.LABORATORY.value, pagination=pagination)


async def list_equipment(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[ResourceDirectoryItemRead]:
    return await list_resources(scope, user, resource_type=DepartmentResourceType.EQUIPMENT.value, pagination=pagination)


def _resource_request_read(doc: DepartmentResourceRequest) -> ResourceRequestRead:
    return ResourceRequestRead(
        request_id=str(doc.id),
        resource_type=doc.resource_type.value,
        resource_ref=doc.resource_ref,
        resource_name=doc.resource_name,
        quantity=doc.quantity,
        needed_from=doc.needed_from,
        needed_until=doc.needed_until,
        urgency=doc.urgency,
        reason=doc.reason,
        status=doc.status,
        requested_by=str(doc.requested_by),
        created_at=doc.created_at,
    )


async def create_resource_request(scope: AccessScope, user: User, payload: ResourceRequestCreate) -> ResourceRequestRead:
    authorize(scope, Permission.DEPARTMENT_RESOURCES_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    if payload.idempotency_key:
        existing = await DepartmentResourceRequest.find_one(
            Eq(DepartmentResourceRequest.tenant_id, tenant_id),
            Eq(DepartmentResourceRequest.idempotency_key, payload.idempotency_key),
        )
        if existing and existing.central_department_id == central_id:
            return _resource_request_read(existing)
    doc = DepartmentResourceRequest(
        tenant_id=tenant_id,
        central_department_id=central_id,
        resource_type=payload.resource_type,
        resource_ref=payload.resource_ref,
        resource_name=payload.resource_name,
        quantity=payload.quantity,
        needed_from=payload.needed_from,
        needed_until=payload.needed_until,
        urgency=payload.urgency,
        reason=payload.reason.strip(),
        requested_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.resource_request.created",
        resource_type="department_resource_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _resource_request_read(doc)


async def list_resource_requests(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
) -> Page[ResourceRequestRead]:
    authorize(scope, Permission.DEPARTMENT_RESOURCES_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    q = DepartmentResourceRequest.find(
        Eq(DepartmentResourceRequest.tenant_id, tenant_id),
        Eq(DepartmentResourceRequest.central_department_id, central_id),
    ).sort("-created_at")
    total = await q.count()
    rows = await q.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_resource_request_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def report_resource_issue(scope: AccessScope, user: User, payload: ResourceIssueCreate) -> ResourceIssueRead:
    authorize(scope, Permission.DEPARTMENT_RESOURCES_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    if payload.idempotency_key:
        existing = await DepartmentResourceIssue.find_one(
            Eq(DepartmentResourceIssue.tenant_id, tenant_id),
            Eq(DepartmentResourceIssue.idempotency_key, payload.idempotency_key),
        )
        if existing and existing.central_department_id == central_id:
            return ResourceIssueRead(
                issue_id=str(existing.id),
                resource_type=existing.resource_type.value,
                resource_ref=existing.resource_ref,
                issue_type=existing.issue_type,
                description=existing.description,
                status=existing.status,
                reported_by=str(existing.reported_by),
                created_at=existing.created_at,
            )
    doc = DepartmentResourceIssue(
        tenant_id=tenant_id,
        central_department_id=central_id,
        resource_type=payload.resource_type,
        resource_ref=payload.resource_ref,
        issue_type=payload.issue_type,
        description=payload.description.strip(),
        reported_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    key = payload.idempotency_key or f"dept_resource_issue:{doc.id}"
    if not await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)
    ):
        await DomainOutboxEvent(
            tenant_id=tenant_id,
            event_type="department.resource.issue_reported",
            aggregate_type="department_resource_issue",
            aggregate_id=str(doc.id),
            payload={"issue_id": str(doc.id), "resource_ref": doc.resource_ref},
            idempotency_key=key,
            status=OutboxEventStatus.PENDING,
        ).insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.resource_issue.reported",
        resource_type="department_resource_issue",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return ResourceIssueRead(
        issue_id=str(doc.id),
        resource_type=doc.resource_type.value,
        resource_ref=doc.resource_ref,
        issue_type=doc.issue_type,
        description=doc.description,
        status=doc.status,
        reported_by=str(doc.reported_by),
        created_at=doc.created_at,
    )


async def resource_utilization(scope: AccessScope, user: User) -> ResourceUtilizationRead:
    authorize(scope, Permission.DEPARTMENT_RESOURCES_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    directory = await _collect_room_lab_resources(tenant_id, central_id)
    equipment = await _collect_equipment(tenant_id)
    classrooms = sum(1 for d in directory if d.resource_type == DepartmentResourceType.CLASSROOM.value)
    laboratories = sum(1 for d in directory if d.resource_type == DepartmentResourceType.LABORATORY.value)
    pending = await DepartmentResourceRequest.find(
        {
            "tenant_id": tenant_id,
            "central_department_id": central_id,
            "status": DepartmentRequestStatus.PENDING.value,
        }
    ).count()
    open_issues = await DepartmentResourceIssue.find(
        {
            "tenant_id": tenant_id,
            "central_department_id": central_id,
            "status": {"$in": [DepartmentResourceIssueStatus.OPEN.value, DepartmentResourceIssueStatus.IN_PROGRESS.value]},
        }
    ).count()
    booking_hints = await DepartmentTimetableSlot.find(
        {"tenant_id": tenant_id, "central_department_id": central_id}
    ).count()
    return ResourceUtilizationRead(
        classrooms_listed=classrooms,
        laboratories_listed=laboratories,
        equipment_listed=len(equipment),
        pending_resource_requests=pending,
        open_resource_issues=open_issues,
        timetable_booking_hints=booking_hints,
        advisory=UTILIZATION_ADVISORY,
    )