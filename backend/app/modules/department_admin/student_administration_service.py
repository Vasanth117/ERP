"""Department Admin — student directory, corrections, follow-ups."""

import re

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.attendance.models import AttendanceRecord
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.department_admin.department_scope import assert_faculty_visible_to_department
from app.modules.department_admin.models import (
    DepartmentRequestStatus,
    DepartmentStudentCorrectionRequest,
    DepartmentStudentFollowUp,
    DepartmentStudentFollowUpStatus,
)
from app.modules.department_admin.phase3_schemas import (
    EnrollmentSummaryRead,
    StudentAcademicProfileRead,
    StudentCorrectionCreate,
    StudentCorrectionRead,
    StudentCorrectionReview,
    StudentDirectoryFilters,
    StudentDirectoryItem,
    StudentFollowUpCreate,
    StudentFollowUpRead,
    StudentFollowUpUpdate,
)
from app.modules.department_admin.performance_monitoring_logic import PERFORMANCE_FOLLOW_UP_CATEGORIES
from app.modules.department_admin.policy import resolve_authorized_department

_GENERAL_FOLLOW_UP_CATEGORIES = frozenset({"general", "academic", "enrollment", "attendance", "disciplinary"})
ALLOWED_STUDENT_FOLLOW_UP_CATEGORIES = PERFORMANCE_FOLLOW_UP_CATEGORIES | _GENERAL_FOLLOW_UP_CATEGORIES
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord, StudentEnrollment, StudentProfile

_DEPT_CORRECTION_FIELDS = frozenset({"roll_number", "section_code", "batch_label", "programme_code"})


def _record_field_value(record: StudentRecord, field_name: str) -> str | None:
    value = getattr(record, field_name, None)
    if value is None:
        return None
    return str(value)


async def _assert_student_in_department(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
) -> StudentRecord:
    record = await StudentRecord.find_one(Eq(StudentRecord.tenant_id, tenant_id), Eq(StudentRecord.user_id, student_user_id))
    if record is None or record.department_id != central_id:
        raise AppError(code="FORBIDDEN", message="Student outside department", status_code=403)
    return record


def _correction_read(doc: DepartmentStudentCorrectionRequest) -> StudentCorrectionRead:
    return StudentCorrectionRead(
        request_id=str(doc.id),
        student_user_id=str(doc.student_user_id),
        field_name=doc.field_name,
        current_value=doc.current_value,
        proposed_value=doc.proposed_value,
        status=doc.status,
        reason=doc.reason,
        created_at=doc.created_at,
    )


def _follow_up_read(doc: DepartmentStudentFollowUp) -> StudentFollowUpRead:
    return StudentFollowUpRead(
        follow_up_id=str(doc.id),
        student_user_id=str(doc.student_user_id),
        category=doc.category,
        description=doc.description,
        assigned_faculty_user_id=str(doc.assigned_faculty_user_id) if doc.assigned_faculty_user_id else None,
        due_date=doc.due_date,
        status=doc.status,
        resolution_notes=doc.resolution_notes,
        created_at=doc.created_at,
    )


async def list_students(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
    filters: StudentDirectoryFilters,
) -> Page[StudentDirectoryItem]:
    authorize(scope, Permission.DEPARTMENT_STUDENT_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    query: dict = {"tenant_id": tenant_id, "department_id": central_id}
    if filters.programme_code:
        query["programme_code"] = filters.programme_code.upper()
    if filters.batch_label:
        query["batch_label"] = filters.batch_label
    if filters.section_code:
        query["section_code"] = filters.section_code.upper()
    if filters.enrollment_status:
        query["enrollment_status"] = filters.enrollment_status
    if filters.search:
        pattern = re.escape(filters.search.strip())
        users = await User.find(
            {"tenant_id": tenant_id, "full_name": {"$regex": pattern, "$options": "i"}},
        ).to_list()
        search_user_ids = [u.id for u in users]
        if not search_user_ids:
            return Page(items=[], total=0, limit=pagination.limit, offset=pagination.offset)
        query["user_id"] = {"$in": search_user_ids}
    motor_query = StudentRecord.find(query)
    total = await motor_query.count()
    records = await motor_query.sort("+roll_number").skip(pagination.offset).limit(pagination.limit).to_list()
    user_ids = [r.user_id for r in records]
    users = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    user_map = {u.id: u for u in users}
    items: list[StudentDirectoryItem] = []
    for record in records:
        student_user = user_map.get(record.user_id)
        if student_user is None:
            continue
        profile = await StudentProfile.find_one(
            Eq(StudentProfile.tenant_id, tenant_id),
            Eq(StudentProfile.user_id, record.user_id),
        )
        semester_label = None
        if profile and filters.semester_label:
            acad = await StudentAcademicRecord.find_one(
                Eq(StudentAcademicRecord.tenant_id, tenant_id),
                Eq(StudentAcademicRecord.user_id, record.user_id),
                Eq(StudentAcademicRecord.semester_label, filters.semester_label),
            )
            if acad is None:
                continue
            semester_label = acad.semester_label
        elif profile:
            acad = (
                await StudentAcademicRecord.find(
                    Eq(StudentAcademicRecord.tenant_id, tenant_id),
                    Eq(StudentAcademicRecord.user_id, record.user_id),
                )
                .sort("-updated_at")
                .limit(1)
                .to_list()
            )
            if acad:
                semester_label = acad[0].semester_label
        if filters.semester_label and semester_label != filters.semester_label:
            continue
        items.append(
            StudentDirectoryItem(
                student_user_id=str(record.user_id),
                full_name=student_user.full_name,
                email=student_user.email,
                roll_number=record.roll_number,
                programme_code=record.programme_code,
                batch_label=record.batch_label,
                section_code=record.section_code,
                enrollment_status=record.enrollment_status.value
                if isinstance(record.enrollment_status, StudentEnrollmentStatus)
                else str(record.enrollment_status),
                lifecycle_status=record.lifecycle_status.value,
            )
        )
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_student(scope: AccessScope, user: User, student_id: str) -> StudentDirectoryItem:
    student_oid = to_object_id(student_id, "student_id")
    authorize(scope, Permission.DEPARTMENT_STUDENT_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    record = await _assert_student_in_department(tenant_id, central_id, student_oid)
    student_user = await User.get(record.user_id)
    if student_user is None:
        raise AppError(code="NOT_FOUND", message="Student not found", status_code=404)
    return StudentDirectoryItem(
        student_user_id=str(record.user_id),
        full_name=student_user.full_name,
        email=student_user.email,
        roll_number=record.roll_number,
        programme_code=record.programme_code,
        batch_label=record.batch_label,
        section_code=record.section_code,
        enrollment_status=record.enrollment_status.value,
        lifecycle_status=record.lifecycle_status.value,
    )


async def get_student_academic_profile(scope: AccessScope, user: User, student_id: str) -> StudentAcademicProfileRead:
    authorize(scope, Permission.DEPARTMENT_STUDENT_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    student_oid = to_object_id(student_id, "student_id")
    record = await _assert_student_in_department(tenant_id, central_id, student_oid)
    acad_rows = (
        await StudentAcademicRecord.find(
            Eq(StudentAcademicRecord.tenant_id, tenant_id),
            Eq(StudentAcademicRecord.user_id, student_oid),
        )
        .sort("-updated_at")
        .limit(1)
        .to_list()
    )
    acad = acad_rows[0] if acad_rows else None
    enroll_count = await StudentEnrollment.find(
        Eq(StudentEnrollment.tenant_id, tenant_id),
        Eq(StudentEnrollment.user_id, student_oid),
    ).count()
    attendance_count = await AttendanceRecord.find(
        {"tenant_id": tenant_id, "student_user_id": student_oid},
    ).count()
    return StudentAcademicProfileRead(
        student_user_id=str(student_oid),
        roll_number=record.roll_number,
        programme_code=record.programme_code,
        batch_label=record.batch_label,
        section_code=record.section_code,
        academic_year_label=acad.academic_year_label if acad else None,
        semester_label=acad.semester_label if acad else None,
        enrollment_lines=enroll_count,
        academic_standing=acad.academic_standing.value if acad else None,
        attendance_sessions_recorded=attendance_count or None,
    )


async def enrollment_summary(scope: AccessScope, user: User) -> EnrollmentSummaryRead:
    authorize(scope, Permission.DEPARTMENT_STUDENT_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    base = {"tenant_id": tenant_id, "department_id": central_id}
    active = await StudentRecord.find({**base, "enrollment_status": StudentEnrollmentStatus.ACTIVE}).count()
    withdrawn = await StudentRecord.find({**base, "lifecycle_status": "withdrawn"}).count()
    on_leave = await StudentRecord.find({**base, "lifecycle_status": "on_leave"}).count()
    unallocated = await StudentRecord.find(
        {
            **base,
            "$or": [{"section_code": None}, {"section_code": ""}],
        }
    ).count()
    return EnrollmentSummaryRead(active=active, withdrawn=withdrawn, on_leave=on_leave, unallocated_section=unallocated)


async def list_unallocated_students(scope: AccessScope, user: User, *, pagination: Pagination) -> Page[StudentDirectoryItem]:
    authorize(scope, Permission.DEPARTMENT_STUDENT_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    query = StudentRecord.find(
        {
            "tenant_id": tenant_id,
            "department_id": central_id,
            "$or": [{"section_code": None}, {"section_code": ""}],
        }
    )
    total = await query.count()
    records = await query.sort("+roll_number").skip(pagination.offset).limit(pagination.limit).to_list()
    items: list[StudentDirectoryItem] = []
    for record in records:
        student_user = await User.get(record.user_id)
        if student_user is None:
            continue
        items.append(
            StudentDirectoryItem(
                student_user_id=str(record.user_id),
                full_name=student_user.full_name,
                email=student_user.email,
                roll_number=record.roll_number,
                programme_code=record.programme_code,
                batch_label=record.batch_label,
                section_code=record.section_code,
                enrollment_status=record.enrollment_status.value,
                lifecycle_status=record.lifecycle_status.value,
            )
        )
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def create_correction_request(
    scope: AccessScope,
    user: User,
    payload: StudentCorrectionCreate,
) -> StudentCorrectionRead:
    authorize(scope, Permission.DEPARTMENT_STUDENT_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    if payload.field_name not in _DEPT_CORRECTION_FIELDS:
        raise AppError(
            code="FORBIDDEN",
            message="Field is not eligible for department correction",
            status_code=403,
        )
    student_oid = to_object_id(payload.student_user_id, "student_user_id")
    record = await _assert_student_in_department(tenant_id, central_id, student_oid)
    if payload.idempotency_key:
        existing = await DepartmentStudentCorrectionRequest.find_one(
            Eq(DepartmentStudentCorrectionRequest.tenant_id, tenant_id),
            Eq(DepartmentStudentCorrectionRequest.idempotency_key, payload.idempotency_key),
        )
        if existing:
            return _correction_read(existing)
    pending = await DepartmentStudentCorrectionRequest.find_one(
        Eq(DepartmentStudentCorrectionRequest.tenant_id, tenant_id),
        Eq(DepartmentStudentCorrectionRequest.student_user_id, student_oid),
        Eq(DepartmentStudentCorrectionRequest.field_name, payload.field_name),
        Eq(DepartmentStudentCorrectionRequest.status, DepartmentRequestStatus.PENDING),
    )
    if pending:
        raise AppError(code="CONFLICT", message="Pending correction already exists for field", status_code=409)
    current = _record_field_value(record, payload.field_name)
    doc = DepartmentStudentCorrectionRequest(
        tenant_id=tenant_id,
        central_department_id=central_id,
        student_user_id=student_oid,
        field_name=payload.field_name,
        current_value=current,
        proposed_value=payload.proposed_value,
        reason=payload.reason,
        evidence_ref=payload.evidence_ref,
        requested_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.student_correction.request",
        resource_type="department_student_correction",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _correction_read(doc)


async def list_correction_requests(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
) -> Page[StudentCorrectionRead]:
    authorize(scope, Permission.DEPARTMENT_STUDENT_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    query = DepartmentStudentCorrectionRequest.find(
        Eq(DepartmentStudentCorrectionRequest.tenant_id, tenant_id),
        Eq(DepartmentStudentCorrectionRequest.central_department_id, central_id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_correction_read(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_correction_request(scope: AccessScope, user: User, request_id: str) -> StudentCorrectionRead:
    authorize(scope, Permission.DEPARTMENT_STUDENT_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentStudentCorrectionRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Correction request not found", status_code=404)
    return _correction_read(doc)


async def review_correction_request(
    scope: AccessScope,
    user: User,
    request_id: str,
    payload: StudentCorrectionReview,
) -> StudentCorrectionRead:
    authorize(scope, Permission.DEPARTMENT_STUDENT_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentStudentCorrectionRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Correction request not found", status_code=404)
    if doc.status != DepartmentRequestStatus.PENDING:
        return _correction_read(doc)
    if payload.decision == "reject":
        doc.status = DepartmentRequestStatus.REJECTED
        doc.decision_reason = payload.decision_reason
        doc.decided_by = user.id
        doc.decided_at = utcnow()
        await doc.save()
        return _correction_read(doc)
    record = await _assert_student_in_department(tenant_id, central_id, doc.student_user_id)
    if doc.field_name not in _DEPT_CORRECTION_FIELDS:
        raise AppError(code="FORBIDDEN", message="Field not allowed", status_code=403)
    setattr(record, doc.field_name, doc.proposed_value if doc.field_name != "programme_code" else doc.proposed_value.upper())
    record.updated_at = utcnow()
    record.updated_by = user.id
    await record.save()
    from app.modules.college_admin.student_admin_service import _sync_profile

    student_user = await User.get(record.user_id)
    if student_user:
        await _sync_profile(record, student_user)
    doc.status = DepartmentRequestStatus.COMPLETED
    doc.decided_by = user.id
    doc.decided_at = utcnow()
    doc.decision_reason = payload.decision_reason
    await doc.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.student_correction.complete",
        resource_type="department_student_correction",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _correction_read(doc)


async def list_follow_ups(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
) -> Page[StudentFollowUpRead]:
    authorize(scope, Permission.DEPARTMENT_STUDENT_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    query = DepartmentStudentFollowUp.find(
        Eq(DepartmentStudentFollowUp.tenant_id, tenant_id),
        Eq(DepartmentStudentFollowUp.central_department_id, central_id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_follow_up_read(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def create_follow_up(scope: AccessScope, user: User, payload: StudentFollowUpCreate) -> StudentFollowUpRead:
    authorize(scope, Permission.DEPARTMENT_STUDENT_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    student_oid = to_object_id(payload.student_user_id, "student_user_id")
    if payload.category not in ALLOWED_STUDENT_FOLLOW_UP_CATEGORIES:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Follow-up category is not in the institutional allowlist",
            status_code=422,
        )
    await _assert_student_in_department(tenant_id, central_id, student_oid)
    faculty_id = None
    if payload.assigned_faculty_user_id:
        faculty_id = to_object_id(payload.assigned_faculty_user_id, "assigned_faculty_user_id")
        await assert_faculty_visible_to_department(tenant_id, central_id, faculty_id)
    doc = DepartmentStudentFollowUp(
        tenant_id=tenant_id,
        central_department_id=central_id,
        student_user_id=student_oid,
        category=payload.category,
        description=payload.description,
        assigned_faculty_user_id=faculty_id,
        due_date=payload.due_date,
        created_by=user.id,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.student_follow_up.create",
        resource_type="department_student_follow_up",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _follow_up_read(doc)


async def update_follow_up(
    scope: AccessScope,
    user: User,
    follow_up_id: str,
    payload: StudentFollowUpUpdate,
) -> StudentFollowUpRead:
    authorize(scope, Permission.DEPARTMENT_STUDENT_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentStudentFollowUp.get(to_object_id(follow_up_id, "follow_up_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Follow-up not found", status_code=404)
    if payload.status is not None:
        doc.status = payload.status
    if payload.resolution_notes is not None:
        doc.resolution_notes = payload.resolution_notes
    if payload.due_date is not None:
        doc.due_date = payload.due_date
    if payload.assigned_faculty_user_id is not None:
        faculty_id = to_object_id(payload.assigned_faculty_user_id, "assigned_faculty_user_id")
        await assert_faculty_visible_to_department(tenant_id, central_id, faculty_id)
        doc.assigned_faculty_user_id = faculty_id
    doc.updated_at = utcnow()
    await doc.save()
    return _follow_up_read(doc)