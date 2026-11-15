"""Department Admin — faculty directory, assignments, workload, substitutes."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.models import TimetableEntry
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicRegulation
from app.modules.college_admin.faculty_admin_models import FacultyDepartmentAssignment, FacultyRecord, FacultyTeachingAssignment
from app.modules.department_admin.department_scope import (
    assert_course_in_department,
    assert_faculty_visible_to_department,
    department_course_codes,
    faculty_user_ids_in_department,
)
from app.modules.department_admin.models import (
    DepartmentFacultyAssignmentRequest,
    DepartmentSubstituteRequest,
)
from app.modules.department_admin.phase2_schemas import (
    FacultyAssignmentRequestCreate,
    FacultyAvailabilityRead,
    FacultyDirectoryFilters,
    FacultyDirectoryItem,
    FacultyProfileDetailRead,
    FacultyWorkloadRead,
    SubstituteRequestCreate,
    SubstituteRequestRead,
    TeachingAssignmentCreate,
    TeachingAssignmentRead,
    TeachingAssignmentUpdate,
    UnassignedSubjectItem,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment, FacultyProfile, FacultyWorkload
from app.modules.faculty.repositories import FacultyAssignmentRepository, FacultyWorkloadRepository
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.models import LeaveRequest

_assignment_repo = FacultyAssignmentRepository()
_workload_repo = FacultyWorkloadRepository()


async def _workload_limit(tenant_id: PydanticObjectId) -> float | None:
    reg = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, "faculty_workload"),
    )
    if reg is None:
        return None
    value = reg.rules.get("max_total_hours")
    return float(value) if isinstance(value, (int, float)) else None


def _assignment_read(doc: FacultyAssignment) -> TeachingAssignmentRead:
    return TeachingAssignmentRead(
        assignment_id=str(doc.id),
        faculty_user_id=str(doc.user_id),
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        course_code=doc.course_code,
        course_name=doc.course_name,
        section=doc.section,
        assignment_role=doc.assignment_role,
        status=doc.status,
        updated_at=doc.updated_at,
    )


async def list_faculty_directory(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
    filters: FacultyDirectoryFilters,
) -> Page[FacultyDirectoryItem]:
    authorize(scope, Permission.DEPARTMENT_FACULTY_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    allowed_ids = list(await faculty_user_ids_in_department(tenant_id, central_id))
    if not allowed_ids:
        return Page(items=[], total=0, limit=pagination.limit, offset=pagination.offset)
    users = await User.find(In(User.id, allowed_ids), Eq(User.tenant_id, tenant_id)).to_list()
    if filters.search:
        needle = filters.search.lower()
        users = [u for u in users if needle in u.full_name.lower() or needle in u.email.lower()]
    total = len(users)
    users = users[pagination.offset : pagination.offset + pagination.limit]
    year = filters.academic_year_label
    semester = filters.semester_label
    items: list[FacultyDirectoryItem] = []
    for u in users:
        profile = await FacultyProfile.find_one(Eq(FacultyProfile.tenant_id, tenant_id), Eq(FacultyProfile.user_id, u.id))
        record = await FacultyRecord.find_one(Eq(FacultyRecord.tenant_id, tenant_id), Eq(FacultyRecord.user_id, u.id))
        if filters.designation and (not profile or profile.designation != filters.designation):
            continue
        if filters.employment_status and record and record.employment_status.value != filters.employment_status:
            continue
        assignments = await _assignment_repo.list_active_for_user(tenant_id, u.id, academic_year_label=year, semester_label=semester)
        if filters.subject_code and not any(a.subject_code == filters.subject_code for a in assignments):
            continue
        subjects = sorted({a.subject_code or a.course_code for a in assignments if a.subject_code or a.course_code})
        sections = sorted({a.section for a in assignments})
        workload_hours = None
        if year and semester:
            wl = await _workload_repo.get_for_term(tenant_id, u.id, year, semester)
            if wl:
                workload_hours = wl.total_hours
        items.append(
            FacultyDirectoryItem(
                faculty_user_id=str(u.id),
                full_name=u.full_name,
                email=u.email,
                employee_id=profile.employee_id if profile else None,
                faculty_code=profile.faculty_code if profile else None,
                designation=profile.designation if profile else None,
                employment_status=record.employment_status.value if record else "active",
                department_id=str(profile.department_id) if profile and profile.department_id else None,
                specialization=profile.specialization if profile else None,
                assigned_subjects=subjects,
                assigned_sections=sections,
                workload_total_hours=workload_hours,
            )
        )
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_faculty_profile_detail(scope: AccessScope, user: User, faculty_id: str) -> FacultyProfileDetailRead:
    authorize(scope, Permission.DEPARTMENT_FACULTY_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_user_id = to_object_id(faculty_id, "faculty_id")
    profile = await assert_faculty_visible_to_department(tenant_id, central_id, faculty_user_id)
    faculty_user = await User.get(faculty_user_id)
    if faculty_user is None:
        raise AppError(code="NOT_FOUND", message="Faculty not found", status_code=404)
    assignments = await _assignment_repo.list_active_for_user(tenant_id, faculty_user_id)
    assignment_payload = [
        {
            "course_code": a.course_code,
            "section": a.section,
            "academic_year_label": a.academic_year_label,
            "semester_label": a.semester_label,
        }
        for a in assignments
    ]
    workload_doc = None
    if assignments:
        a0 = assignments[0]
        workload_doc = await _workload_repo.get_for_term(tenant_id, faculty_user_id, a0.academic_year_label, a0.semester_label)
    leave_count = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.employee_user_id, faculty_user_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
    ).count()
    return FacultyProfileDetailRead(
        faculty_user_id=str(faculty_user_id),
        full_name=faculty_user.full_name,
        email=faculty_user.email,
        employee_id=profile.employee_id,
        faculty_code=profile.faculty_code,
        designation=profile.designation,
        department_id=str(profile.department_id) if profile.department_id else None,
        qualifications=profile.qualifications,
        specialization=profile.specialization,
        contact_phone=profile.contact_phone,
        office_location=profile.office_location,
        bio=profile.bio,
        assignments=assignment_payload,
        workload=workload_doc.model_dump() if workload_doc else None,
        approved_leave_count=leave_count,
    )


async def get_faculty_availability(scope: AccessScope, user: User, faculty_id: str, *, anchor: date | None = None) -> FacultyAvailabilityRead:
    authorize(scope, Permission.DEPARTMENT_FACULTY_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_user_id = to_object_id(faculty_id, "faculty_id")
    await assert_faculty_visible_to_department(tenant_id, central_id, faculty_user_id)
    anchor = anchor or date.today()
    weekday = anchor.weekday()
    entries = await TimetableEntry.find(
        Eq(TimetableEntry.tenant_id, tenant_id),
        Eq(TimetableEntry.faculty_user_id, faculty_user_id),
        Eq(TimetableEntry.day_of_week, weekday),
    ).count()
    on_leave = await LeaveRequest.find_one(
        {
            "tenant_id": tenant_id,
            "employee_user_id": faculty_user_id,
            "status": LeaveRequestStatus.APPROVED.value,
            "start_date": {"$lte": anchor},
            "end_date": {"$gte": anchor},
        }
    )
    note = "Missing timetable does not imply availability."
    if on_leave:
        note = "Faculty has approved leave for this date."
    return FacultyAvailabilityRead(
        faculty_user_id=faculty_id,
        has_timetable_data=entries > 0,
        scheduled_sessions_today=entries,
        on_approved_leave=on_leave is not None,
        availability_note=note,
    )


async def get_faculty_workload(
    scope: AccessScope,
    user: User,
    faculty_id: str,
    *,
    academic_year_label: str,
    semester_label: str,
) -> FacultyWorkloadRead:
    authorize(scope, Permission.DEPARTMENT_FACULTY_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_user_id = to_object_id(faculty_id, "faculty_id")
    await assert_faculty_visible_to_department(tenant_id, central_id, faculty_user_id)
    wl = await _workload_repo.get_for_term(tenant_id, faculty_user_id, academic_year_label, semester_label)
    active = await _assignment_repo.list_active_for_user(
        tenant_id, faculty_user_id, academic_year_label=academic_year_label, semester_label=semester_label
    )
    max_hours = await _workload_limit(tenant_id)
    total = wl.total_hours if wl else sum(2.0 for _ in active)
    exceeds = (total > max_hours) if max_hours is not None else None
    return FacultyWorkloadRead(
        faculty_user_id=faculty_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        lecture_hours=wl.lecture_hours if wl else 0,
        lab_hours=wl.lab_hours if wl else 0,
        tutorial_hours=wl.tutorial_hours if wl else 0,
        total_hours=total,
        credit_units=wl.credit_units if wl else 0,
        active_course_count=len(active),
        institutional_max_hours=max_hours,
        exceeds_limit=exceeds,
    )


async def list_teaching_assignments(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> Page[TeachingAssignmentRead]:
    authorize(scope, Permission.DEPARTMENT_FACULTY_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    course_codes = list(await department_course_codes(tenant_id, central_id))
    if not course_codes:
        return Page(items=[], total=0, limit=pagination.limit, offset=pagination.offset)
    filters: dict = {"tenant_id": tenant_id, "course_code": {"$in": course_codes}}
    if academic_year_label:
        filters["academic_year_label"] = academic_year_label
    if semester_label:
        filters["semester_label"] = semester_label
    query = FacultyAssignment.find(filters).sort("-updated_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_assignment_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def create_teaching_assignment(scope: AccessScope, user: User, payload: TeachingAssignmentCreate) -> TeachingAssignmentRead:
    authorize(scope, Permission.DEPARTMENT_FACULTY_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_user_id = to_object_id(payload.faculty_user_id, "faculty_user_id")
    await assert_faculty_visible_to_department(tenant_id, central_id, faculty_user_id)
    faculty_user = await User.get(faculty_user_id)
    if faculty_user is None or not faculty_user.is_active:
        raise AppError(code="VALIDATION_ERROR", message="Faculty account is inactive", status_code=422)
    course = await assert_course_in_department(tenant_id, central_id, payload.course_code)
    if payload.idempotency_key:
        existing = await FacultyAssignment.find_one(
            {"tenant_id": tenant_id, "change_note": f"idempotency:{payload.idempotency_key}"}
        )
        if existing:
            return _assignment_read(existing)
    dup = await FacultyAssignment.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": faculty_user_id,
            "course_code": payload.course_code.upper(),
            "section": payload.section.upper(),
            "academic_year_label": payload.academic_year_label,
            "semester_label": payload.semester_label,
            "status": AssignmentStatus.ACTIVE,
        }
    )
    if dup:
        raise AppError(code="CONFLICT", message="Duplicate active assignment exists", status_code=409)
    assignment = FacultyAssignment(
        tenant_id=tenant_id,
        user_id=faculty_user_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        course_id=payload.course_id or course.course_id,
        course_code=payload.course_code.upper(),
        course_name=payload.course_name,
        subject_code=payload.subject_code,
        subject_name=payload.subject_name,
        section=payload.section.upper(),
        assignment_role=payload.assignment_role,
        allocation_locked=False,
        change_note=f"department_admin:{payload.idempotency_key or user.id}",
    )
    await assignment.insert()
    await FacultyTeachingAssignment(
        tenant_id=tenant_id,
        user_id=faculty_user_id,
        faculty_assignment_id=assignment.id,
        academic_year_label=assignment.academic_year_label,
        semester_label=assignment.semester_label,
        course_code=assignment.course_code,
        section=assignment.section,
        actor_id=user.id,
    ).insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.faculty.assignment.create",
        resource_type="faculty_assignment",
        resource_id=str(assignment.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata={"department_id": str(central_id)},
    )
    return _assignment_read(assignment)


async def update_teaching_assignment(
    scope: AccessScope,
    user: User,
    assignment_id: str,
    payload: TeachingAssignmentUpdate,
) -> TeachingAssignmentRead:
    authorize(scope, Permission.DEPARTMENT_FACULTY_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await FacultyAssignment.get(to_object_id(assignment_id, "assignment_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    await assert_course_in_department(tenant_id, central_id, doc.course_code)
    if payload.section is not None:
        doc.section = payload.section.upper()
    if payload.status is not None:
        doc.status = payload.status
    if payload.change_note:
        doc.change_note = payload.change_note
    doc.updated_at = utcnow()
    await doc.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.faculty.assignment.update",
        resource_type="faculty_assignment",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _assignment_read(doc)


async def list_unassigned_subjects(
    scope: AccessScope,
    user: User,
    *,
    academic_year_label: str | None,
    semester_label: str | None,
) -> list[UnassignedSubjectItem]:
    authorize(scope, Permission.DEPARTMENT_FACULTY_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    from app.modules.academics.curriculum_models import CourseRecord

    courses = await CourseRecord.find(
        Eq(CourseRecord.tenant_id, tenant_id),
        Eq(CourseRecord.department_id, central_id),
        Eq(CourseRecord.is_active, True),
    ).to_list()
    active_filters = {
        "tenant_id": tenant_id,
        "status": AssignmentStatus.ACTIVE,
    }
    if academic_year_label:
        active_filters["academic_year_label"] = academic_year_label
    if semester_label:
        active_filters["semester_label"] = semester_label
    assigned_codes = {
        a.course_code
        for a in await FacultyAssignment.find(active_filters).to_list()
    }
    return [
        UnassignedSubjectItem(
            course_code=c.course_code,
            course_name=c.name,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
        )
        for c in courses
        if c.course_code not in assigned_codes
    ]


async def create_substitute_request(scope: AccessScope, user: User, payload: SubstituteRequestCreate) -> SubstituteRequestRead:
    authorize(scope, Permission.DEPARTMENT_FACULTY_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    original_id = to_object_id(payload.original_faculty_user_id, "original_faculty_user_id")
    await assert_faculty_visible_to_department(tenant_id, central_id, original_id)
    sub_id = (
        to_object_id(payload.substitute_faculty_user_id, "substitute_faculty_user_id")
        if payload.substitute_faculty_user_id
        else None
    )
    if sub_id:
        await assert_faculty_visible_to_department(tenant_id, central_id, sub_id)
    if payload.idempotency_key:
        existing = await DepartmentSubstituteRequest.find_one(
            Eq(DepartmentSubstituteRequest.tenant_id, tenant_id),
            Eq(DepartmentSubstituteRequest.idempotency_key, payload.idempotency_key),
        )
        if existing:
            return _substitute_read(existing)
    await assert_course_in_department(tenant_id, central_id, payload.course_code)
    doc = DepartmentSubstituteRequest(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        central_department_id=central_id,
        original_faculty_user_id=original_id,
        substitute_faculty_user_id=sub_id,
        course_code=payload.course_code.upper(),
        section=payload.section.upper(),
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        session_date=payload.session_date,
        reason=payload.reason,
        requested_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.substitute.request",
        resource_type="department_substitute_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _substitute_read(doc)


def _substitute_read(doc: DepartmentSubstituteRequest) -> SubstituteRequestRead:
    return SubstituteRequestRead(
        request_id=str(doc.id),
        original_faculty_user_id=str(doc.original_faculty_user_id),
        substitute_faculty_user_id=str(doc.substitute_faculty_user_id) if doc.substitute_faculty_user_id else None,
        course_code=doc.course_code,
        section=doc.section,
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        session_date=doc.session_date,
        reason=doc.reason,
        status=doc.status,
        created_at=doc.created_at,
    )


async def list_substitute_requests(
    scope: AccessScope,
    user: User,
    *,
    pagination: Pagination,
) -> Page[SubstituteRequestRead]:
    authorize(scope, Permission.DEPARTMENT_FACULTY_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    query = DepartmentSubstituteRequest.find(
        Eq(DepartmentSubstituteRequest.tenant_id, tenant_id),
        Eq(DepartmentSubstituteRequest.institution_department_id, institution.id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_substitute_read(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def create_faculty_assignment_request(
    scope: AccessScope,
    user: User,
    payload: FacultyAssignmentRequestCreate,
) -> dict:
    authorize(scope, Permission.DEPARTMENT_FACULTY_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    faculty_user_id = to_object_id(payload.faculty_user_id, "faculty_user_id")
    await assert_faculty_visible_to_department(tenant_id, central_id, faculty_user_id)
    if payload.idempotency_key:
        existing = await DepartmentFacultyAssignmentRequest.find_one(
            Eq(DepartmentFacultyAssignmentRequest.tenant_id, tenant_id),
            Eq(DepartmentFacultyAssignmentRequest.idempotency_key, payload.idempotency_key),
        )
        if existing:
            return {"request_id": str(existing.id), "status": existing.status.value}
    target = to_object_id(payload.target_department_id, "target_department_id") if payload.target_department_id else None
    if payload.request_type == "transfer" and target is None:
        raise AppError(code="VALIDATION_ERROR", message="target_department_id required for transfer", status_code=422)
    doc = DepartmentFacultyAssignmentRequest(
        tenant_id=tenant_id,
        institution_department_id=institution.id,
        central_department_id=central_id,
        faculty_user_id=faculty_user_id,
        request_type=payload.request_type,
        target_department_id=target,
        note=payload.note,
        requested_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    rows = await FacultyDepartmentAssignment.find(
        Eq(FacultyDepartmentAssignment.tenant_id, tenant_id),
        Eq(FacultyDepartmentAssignment.user_id, faculty_user_id),
    ).to_list()
    await record_department_audit(
        actor_id=user.id,
        action="department.faculty.assignment_request",
        resource_type="department_faculty_assignment_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return {"request_id": str(doc.id), "status": doc.status.value, "existing_assignments": len(rows)}