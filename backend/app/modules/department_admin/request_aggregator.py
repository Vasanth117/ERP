"""Aggregate canonical departmental requests into a unified inbox view."""

from __future__ import annotations

from datetime import datetime, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.attendance.enums import AttendanceCorrectionStatus
from app.modules.attendance.models import AttendanceCorrectionRequest
from app.modules.department_admin import request_categories as cat
from app.modules.department_admin.department_scope import faculty_user_ids_in_department
from app.modules.department_admin.models import (
    DepartmentCourseOfferingRequest,
    DepartmentFacultyAssignmentRequest,
    DepartmentProfileChangeRequest,
    DepartmentProfileChangeStatus,
    DepartmentResourceRequest,
    DepartmentSectionTransferRequest,
    DepartmentStudentCorrectionRequest,
    DepartmentSubstituteRequest,
    DepartmentTimetableChangeRequest,
    DepartmentTimetablePlan,
)
from app.modules.department_admin.phase7_schemas import UnifiedRequestListItem, UnifiedRequestStatus


def _map_status(raw: str) -> UnifiedRequestStatus:
    mapping = {
        "pending": UnifiedRequestStatus.PENDING,
        "submitted": UnifiedRequestStatus.PENDING,
        "approved": UnifiedRequestStatus.APPROVED,
        "rejected": UnifiedRequestStatus.REJECTED,
        "cancelled": UnifiedRequestStatus.CANCELLED,
        "completed": UnifiedRequestStatus.COMPLETED,
    }
    return mapping.get(raw.lower(), UnifiedRequestStatus.PENDING)


def _item(
    *,
    category: str,
    oid: PydanticObjectId,
    status: UnifiedRequestStatus,
    requester_id: PydanticObjectId,
    title: str,
    reason: str | None,
    created_at: datetime,
    due_date: datetime | None = None,
    subject_ref: dict | None = None,
) -> UnifiedRequestListItem:
    return UnifiedRequestListItem(
        request_id=cat.compose_request_id(category, str(oid)),
        category=category,
        status=status,
        requester_user_id=str(requester_id),
        title=title,
        reason=reason,
        submitted_at=created_at,
        due_date=due_date,
        subject_ref=subject_ref or {},
    )


async def aggregate_requests(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    institution_department_id: PydanticObjectId,
    *,
    category_filter: str | None,
    status_filter: UnifiedRequestStatus | None,
    date_from: datetime | None,
    date_to: datetime | None,
    per_category_limit: int = 80,
) -> list[UnifiedRequestListItem]:
    items: list[UnifiedRequestListItem] = []
    faculty_ids = list(await faculty_user_ids_in_department(tenant_id, central_id))

    async def include(item: UnifiedRequestListItem) -> None:
        if status_filter and item.status != status_filter:
            return
        if date_from and item.submitted_at < date_from:
            return
        if date_to and item.submitted_at > date_to:
            return
        items.append(item)

    if category_filter in (None, cat.SECTION_TRANSFER):
        for doc in (
            await DepartmentSectionTransferRequest.find(
                {
                    "tenant_id": tenant_id,
                    "$or": [
                        {"central_department_id": central_id},
                        {"destination_central_department_id": central_id},
                    ],
                }
            )
            .sort("-created_at")
            .limit(per_category_limit)
            .to_list()
        ):
            await include(
                _item(
                    category=cat.SECTION_TRANSFER,
                    oid=doc.id,
                    status=_map_status(doc.status.value),
                    requester_id=doc.requested_by,
                    title=f"Section transfer {doc.from_section_code} → {doc.to_section_code}",
                    reason=doc.reason,
                    created_at=doc.created_at,
                    subject_ref={
                        "student_user_id": str(doc.student_user_id),
                        "programme_code": doc.programme_code,
                    },
                )
            )

    if category_filter in (None, cat.STUDENT_CORRECTION):
        for doc in (
            await DepartmentStudentCorrectionRequest.find(
                Eq(DepartmentStudentCorrectionRequest.tenant_id, tenant_id),
                Eq(DepartmentStudentCorrectionRequest.central_department_id, central_id),
            )
            .sort("-created_at")
            .limit(per_category_limit)
            .to_list()
        ):
            await include(
                _item(
                    category=cat.STUDENT_CORRECTION,
                    oid=doc.id,
                    status=_map_status(doc.status.value),
                    requester_id=doc.requested_by,
                    title=f"Student record correction: {doc.field_name}",
                    reason=doc.reason,
                    created_at=doc.created_at,
                    subject_ref={"student_user_id": str(doc.student_user_id), "field_name": doc.field_name},
                )
            )

    if category_filter in (None, cat.ATTENDANCE_CORRECTION) and faculty_ids:
        for doc in (
            await AttendanceCorrectionRequest.find(
                {"tenant_id": tenant_id, "faculty_user_id": {"$in": faculty_ids}}
            )
            .sort("-created_at")
            .limit(per_category_limit)
            .to_list()
        ):
            status = UnifiedRequestStatus.PENDING
            if doc.status == AttendanceCorrectionStatus.APPROVED:
                status = UnifiedRequestStatus.APPROVED
            elif doc.status == AttendanceCorrectionStatus.REJECTED:
                status = UnifiedRequestStatus.REJECTED
            await include(
                _item(
                    category=cat.ATTENDANCE_CORRECTION,
                    oid=doc.id,
                    status=status,
                    requester_id=doc.faculty_user_id,
                    title="Attendance correction",
                    reason=doc.reason,
                    created_at=doc.created_at,
                    subject_ref={
                        "session_id": str(doc.session_id),
                        "student_user_id": str(doc.student_user_id) if doc.student_user_id else None,
                    },
                )
            )

    if category_filter in (None, cat.TIMETABLE_CHANGE):
        plan_ids = [
            p.id
            for p in await DepartmentTimetablePlan.find(
                {"tenant_id": tenant_id, "central_department_id": central_id}
            ).to_list()
        ]
        if plan_ids:
            for doc in (
                await DepartmentTimetableChangeRequest.find(
                    {"tenant_id": tenant_id, "plan_id": {"$in": plan_ids}}
                )
                .sort("-created_at")
                .limit(per_category_limit)
                .to_list()
            ):
                await include(
                    _item(
                        category=cat.TIMETABLE_CHANGE,
                        oid=doc.id,
                        status=_map_status(doc.status.value),
                        requester_id=doc.requested_by,
                        title=f"Timetable change ({doc.change_type})",
                        reason=doc.reason,
                        created_at=doc.created_at,
                        subject_ref={"plan_id": str(doc.plan_id), "slot_id": str(doc.slot_id) if doc.slot_id else None},
                    )
                )

    if category_filter in (None, cat.SUBSTITUTE_FACULTY):
        for doc in (
            await DepartmentSubstituteRequest.find(
                Eq(DepartmentSubstituteRequest.central_department_id, central_id),
                Eq(DepartmentSubstituteRequest.tenant_id, tenant_id),
            )
            .sort("-created_at")
            .limit(per_category_limit)
            .to_list()
        ):
            await include(
                _item(
                    category=cat.SUBSTITUTE_FACULTY,
                    oid=doc.id,
                    status=_map_status(doc.status.value),
                    requester_id=doc.requested_by,
                    title=f"Substitute {doc.course_code}/{doc.section}",
                    reason=doc.reason,
                    created_at=doc.created_at,
                    subject_ref={"course_code": doc.course_code, "section": doc.section},
                )
            )

    if category_filter in (None, cat.FACULTY_ASSIGNMENT):
        for doc in (
            await DepartmentFacultyAssignmentRequest.find(
                Eq(DepartmentFacultyAssignmentRequest.central_department_id, central_id),
                Eq(DepartmentFacultyAssignmentRequest.tenant_id, tenant_id),
            )
            .sort("-created_at")
            .limit(per_category_limit)
            .to_list()
        ):
            await include(
                _item(
                    category=cat.FACULTY_ASSIGNMENT,
                    oid=doc.id,
                    status=_map_status(doc.status.value),
                    requester_id=doc.requested_by,
                    title=f"Faculty {doc.request_type} request",
                    reason=doc.note,
                    created_at=doc.created_at,
                    subject_ref={"faculty_user_id": str(doc.faculty_user_id)},
                )
            )

    if category_filter in (None, cat.COURSE_OFFERING):
        for doc in (
            await DepartmentCourseOfferingRequest.find(
                Eq(DepartmentCourseOfferingRequest.central_department_id, central_id),
                Eq(DepartmentCourseOfferingRequest.tenant_id, tenant_id),
            )
            .sort("-created_at")
            .limit(per_category_limit)
            .to_list()
        ):
            await include(
                _item(
                    category=cat.COURSE_OFFERING,
                    oid=doc.id,
                    status=_map_status(doc.status.value),
                    requester_id=doc.requested_by,
                    title=f"Course offering {doc.course_code}/{doc.section_code}",
                    reason=None,
                    created_at=doc.created_at,
                    subject_ref={"course_code": doc.course_code, "section_code": doc.section_code},
                )
            )

    if category_filter in (None, cat.PROFILE_CHANGE):
        pending_statuses = [
            DepartmentProfileChangeStatus.SUBMITTED,
            DepartmentProfileChangeStatus.DRAFT,
        ]
        for doc in (
            await DepartmentProfileChangeRequest.find(
                {
                    "tenant_id": tenant_id,
                    "institution_department_id": institution_department_id,
                    "status": {"$in": [s.value for s in pending_statuses]},
                }
            )
            .sort("-created_at")
            .limit(per_category_limit)
            .to_list()
        ):
            await include(
                _item(
                    category=cat.PROFILE_CHANGE,
                    oid=doc.id,
                    status=_map_status(doc.status.value),
                    requester_id=doc.requested_by,
                    title=f"Profile change: {doc.field_name}",
                    reason=doc.proposed_value,
                    created_at=doc.created_at,
                )
            )

    if category_filter in (None, cat.RESOURCE_REQUEST):
        for doc in (
            await DepartmentResourceRequest.find(
                Eq(DepartmentResourceRequest.tenant_id, tenant_id),
                Eq(DepartmentResourceRequest.central_department_id, central_id),
            )
            .sort("-created_at")
            .limit(per_category_limit)
            .to_list()
        ):
            await include(
                _item(
                    category=cat.RESOURCE_REQUEST,
                    oid=doc.id,
                    status=_map_status(doc.status.value),
                    requester_id=doc.requested_by,
                    title=f"Resource request: {doc.resource_type.value}",
                    reason=doc.reason,
                    created_at=doc.created_at,
                    subject_ref={"resource_ref": doc.resource_ref, "resource_type": doc.resource_type.value},
                )
            )

    items.sort(key=lambda i: i.submitted_at, reverse=True)
    return items