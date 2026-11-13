"""Student course registration and elective selection."""

import asyncio
from datetime import datetime, timezone

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.academics.models import TimetableEntry
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.curriculum_models import (
    CourseCatalogReference,
    CoursePrerequisite,
    CourseRegistrationRequest,
    ElectiveGroup,
    ElectiveOption,
    RegistrationHistoryEntry,
    RegistrationSelectionItem,
    StudentCourseRegistration,
    StudentElectiveSelection,
)
from app.modules.students.curriculum_repositories import (
    CourseCatalogRepository,
    RegistrationHistoryRepository,
    RegistrationPolicyRepository,
    StudentRegistrationRepository,
)
from app.modules.students.enums import StudentActivityType
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord
from app.modules.students.curriculum_schemas import (
    AvailableCourseRead,
    CourseRegistrationRead,
    ElectiveGroupRead,
    ElectiveOptionRead,
    RegistrationEligibilityRead,
    RegistrationHistoryRead,
    RegistrationRequestRead,
    RegistrationSelectionInput,
    RegistrationSubmitRead,
    RegistrationValidationRead,
)
from app.modules.students.policy import require_student_scope
from app.modules.students.profile_service import ensure_student_profile
from app.modules.students.registration_enums import (
    CourseRegistrationStatus,
    CourseRegistrationType,
    RegistrationRequestStatus,
)
from app.modules.students.repositories import StudentActivityRepository

_catalog = CourseCatalogRepository()
_policy_repo = RegistrationPolicyRepository()
_registration_repo = StudentRegistrationRepository()
_history_repo = RegistrationHistoryRepository()
_activity_repo = StudentActivityRepository()
_reader = StudentDataReader()

_ACTIVE_REGISTRATION_STATUSES = frozenset(
    {
        CourseRegistrationStatus.DRAFT,
        CourseRegistrationStatus.SUBMITTED,
        CourseRegistrationStatus.PENDING_APPROVAL,
        CourseRegistrationStatus.APPROVED,
    }
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _term_and_programme(scope: AccessScope, user: User) -> tuple[PydanticObjectId, str, str, str]:
    tenant_id = require_student_scope(scope)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    profile = await ensure_student_profile(scope, user)
    programme = profile.programme_code
    if not programme:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)
    return tenant_id, programme, context.academic_year_label, context.semester_label


async def get_registration_eligibility(scope: AccessScope, user: User) -> RegistrationEligibilityRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, semester = await _term_and_programme(scope, user)
    policy = await _policy_repo.get_policy(tenant_id, programme, year, semester)
    reasons: list[str] = []
    if policy is None:
        return RegistrationEligibilityRead(eligible=False, reasons=["Registration policy not configured"])
    now = _now()
    window_open = policy.registration_open_at <= now <= policy.registration_close_at
    if not policy.allow_self_registration:
        reasons.append("Self-registration is disabled for this programme")
    if not window_open:
        reasons.append("Outside registration window")
    record = await StudentAcademicRecord.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "academic_year_label": year, "semester_label": semester}
    )
    if record and record.academic_standing == AcademicStanding.SUSPENDED:
        reasons.append("Account is not in good academic standing")
    eligible = window_open and policy.allow_self_registration and not reasons
    return RegistrationEligibilityRead(
        eligible=eligible,
        reasons=reasons,
        min_credits=policy.min_credits,
        max_credits=policy.max_credits,
        registration_open_at=policy.registration_open_at,
        registration_close_at=policy.registration_close_at,
        modification_deadline=policy.modification_deadline,
        window_open=window_open,
    )


async def list_available_courses(scope: AccessScope, user: User) -> list[AvailableCourseRead]:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, semester = await _term_and_programme(scope, user)
    rows = await _catalog.list_for_term(tenant_id, programme, year, semester, open_only=True)
    completed = await _registration_repo.completed_course_ids(tenant_id, user.id)
    items: list[AvailableCourseRead] = []
    for row in rows:
        prereq = await CoursePrerequisite.find_one({"tenant_id": tenant_id, "course_id": row.course_id})
        prereq_met = True
        if prereq and prereq.prerequisite_course_ids:
            prereq_met = all(pid in completed for pid in prereq.prerequisite_course_ids)
        course = await CourseRecord.find_one({"tenant_id": tenant_id, "course_id": row.course_id})
        items.append(
            AvailableCourseRead(
                course_id=row.course_id,
                course_code=row.course_code,
                name=course.name if course else row.course_code,
                credit_units=row.credit_units or (course.credit_units if course else 0),
                registration_type=row.registration_type,
                is_open_for_registration=row.is_open_for_registration,
                prerequisites_met=prereq_met,
                max_capacity=row.max_capacity,
            )
        )
    return items


async def list_elective_groups(scope: AccessScope, user: User) -> list[ElectiveGroupRead]:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, semester = await _term_and_programme(scope, user)
    groups = await ElectiveGroup.find(
        {
            "tenant_id": tenant_id,
            "programme_code": programme,
            "academic_year_label": year,
            "semester_label": semester,
            "is_active": True,
        }
    ).to_list()
    return [
        ElectiveGroupRead(
            id=str(g.id),
            group_code=g.group_code,
            title=g.title,
            description=g.description,
            min_selections=g.min_selections,
            max_selections=g.max_selections,
            min_credits=g.min_credits,
            max_credits=g.max_credits,
        )
        for g in groups
    ]


async def list_elective_options(scope: AccessScope, user: User, group_id: str) -> list[ElectiveOptionRead]:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, semester = await _term_and_programme(scope, user)
    gid = to_object_id(group_id, "elective group id")
    group = await ElectiveGroup.get(gid)
    if group is None or str(group.tenant_id) != str(tenant_id):
        raise AppError(code="NOT_FOUND", message="Elective group not found", status_code=404)
    if group.programme_code != programme:
        raise AppError(code="FORBIDDEN", message="Elective group not available for your programme", status_code=403)
    options = await ElectiveOption.find({"tenant_id": tenant_id, "elective_group_id": gid, "is_active": True}).to_list()
    completed = await _registration_repo.completed_course_ids(tenant_id, user.id)
    result: list[ElectiveOptionRead] = []
    for opt in options:
        prereq = await CoursePrerequisite.find_one({"tenant_id": tenant_id, "course_id": opt.course_id})
        eligible = True
        if prereq and prereq.prerequisite_course_ids:
            eligible = all(pid in completed for pid in prereq.prerequisite_course_ids)
        seats = None
        if opt.max_seats is not None:
            seats = max(0, opt.max_seats - opt.seats_taken)
        result.append(
            ElectiveOptionRead(
                course_id=opt.course_id,
                course_code=opt.course_code,
                course_name=opt.course_name,
                credit_units=opt.credit_units,
                seats_available=seats,
                eligible=eligible,
            )
        )
    return result


async def _validate_selections(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    programme: str,
    year: str,
    semester: str,
    selections: list[RegistrationSelectionInput],
    *,
    check_policy: bool = True,
) -> RegistrationValidationRead:
    errors: list[str] = []
    warnings: list[str] = []
    policy = await _policy_repo.get_policy(tenant_id, programme, year, semester)
    if policy is None and check_policy:
        errors.append("Registration policy not configured")
        return RegistrationValidationRead(valid=False, errors=errors)
    now = _now()
    if policy and check_policy:
        if not (policy.registration_open_at <= now <= policy.registration_close_at):
            errors.append("Registration window is closed")
        if not policy.allow_self_registration:
            errors.append("Self-registration is not allowed")
    seen_courses: set[str] = set()
    total_credits = 0.0
    completed = await _registration_repo.completed_course_ids(tenant_id, user_id)
    existing = await _registration_repo.list_for_student_term(tenant_id, user_id, year, semester)
    for reg in existing:
        if reg.status in _ACTIVE_REGISTRATION_STATUSES:
            seen_courses.add(reg.course_id)
    for sel in selections:
        if sel.course_id in seen_courses:
            errors.append(f"Duplicate registration for course {sel.course_code}")
        seen_courses.add(sel.course_id)
        catalog = await CourseCatalogReference.find_one(
            {
                "tenant_id": tenant_id,
                "programme_code": programme,
                "academic_year_label": year,
                "semester_label": semester,
                "course_id": sel.course_id,
            }
        )
        if catalog is None or not catalog.is_open_for_registration:
            errors.append(f"Course {sel.course_code} is not open for registration")
        course = await CourseRecord.find_one({"tenant_id": tenant_id, "course_id": sel.course_id})
        credits = catalog.credit_units if catalog else (course.credit_units if course else 0)
        total_credits += credits
        prereq = await CoursePrerequisite.find_one({"tenant_id": tenant_id, "course_id": sel.course_id})
        if prereq:
            missing = [p for p in prereq.prerequisite_course_ids if p not in completed]
            if missing:
                errors.append(f"Prerequisites not met for {sel.course_code}")
            if prereq.min_cgpa is not None:
                record = await StudentAcademicRecord.find_one(
                    {"tenant_id": tenant_id, "user_id": user_id, "academic_year_label": year, "semester_label": semester}
                )
                cgpa = record.cgpa if record else None
                if cgpa is None or cgpa < prereq.min_cgpa:
                    errors.append(f"Minimum CGPA {prereq.min_cgpa} required for {sel.course_code}")
    if policy:
        if total_credits < policy.min_credits:
            warnings.append(f"Total credits {total_credits} below minimum {policy.min_credits}")
        if total_credits > policy.max_credits:
            errors.append(f"Total credits {total_credits} exceeds maximum {policy.max_credits}")
    conflicts: list[str] = []
    if policy and policy.check_timetable_conflicts:
        slots: list[tuple[str, int, object, object]] = []
        for sel in selections:
            section = sel.section_code or "A"
            entries = await TimetableEntry.find(
                {
                    "tenant_id": tenant_id,
                    "course_code": sel.course_code,
                    "section": section,
                    "academic_year_label": year,
                    "semester_label": semester,
                }
            ).to_list()
            for e in entries:
                slots.append((sel.course_code, e.day_of_week, e.start_time, e.end_time))
        for i, a in enumerate(slots):
            for b in slots[i + 1 :]:
                if a[1] == b[1] and a[0] != b[0] and a[2] < b[3] and b[2] < a[3]:
                    conflicts.append(f"Timetable clash between {a[0]} and {b[0]} on day {a[1]}")
    if conflicts:
        errors.extend(conflicts)
    valid = len(errors) == 0
    return RegistrationValidationRead(
        valid=valid,
        errors=errors,
        warnings=warnings,
        total_credits=total_credits,
        timetable_conflicts=conflicts,
    )


async def validate_course_selection(
    scope: AccessScope, user: User, selections: list[RegistrationSelectionInput]
) -> RegistrationValidationRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, semester = await _term_and_programme(scope, user)
    return await _validate_selections(tenant_id, user.id, programme, year, semester, selections)


async def _append_history(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    course_id: str,
    course_code: str,
    action: str,
    previous_status: str | None,
    new_status: str | None,
    metadata: dict | None = None,
) -> None:
    await RegistrationHistoryEntry(
        tenant_id=tenant_id,
        user_id=user_id,
        academic_year_label=year,
        semester_label=semester,
        course_id=course_id,
        course_code=course_code,
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        metadata=metadata or {},
    ).insert()


async def submit_registration(
    scope: AccessScope, user: User, selections: list[RegistrationSelectionInput]
) -> RegistrationSubmitRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_MANAGE)
    tenant_id, programme, year, semester = await _term_and_programme(scope, user)
    validation = await _validate_selections(tenant_id, user.id, programme, year, semester, selections)
    if not validation.valid:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Registration validation failed",
            status_code=422,
            details=[{"errors": validation.errors}],
        )
    policy = await _policy_repo.get_policy(tenant_id, programme, year, semester)
    status = (
        RegistrationRequestStatus.PENDING_APPROVAL
        if policy and policy.require_admin_approval
        else RegistrationRequestStatus.SUBMITTED
    )
    request_items = [
        RegistrationSelectionItem(
            course_id=s.course_id,
            course_code=s.course_code,
            section_code=s.section_code,
            registration_type=s.registration_type,
            elective_group_id=s.elective_group_id,
        )
        for s in selections
    ]
    req = CourseRegistrationRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        academic_year_label=year,
        semester_label=semester,
        programme_code=programme,
        status=status,
        selections=request_items,
        validation_snapshot=validation.model_dump(),
        submitted_at=utcnow(),
    )
    await req.insert()
    reg_status = (
        CourseRegistrationStatus.PENDING_APPROVAL
        if status == RegistrationRequestStatus.PENDING_APPROVAL
        else CourseRegistrationStatus.SUBMITTED
    )
    for sel in selections:
        catalog = await CourseCatalogReference.find_one({"tenant_id": tenant_id, "course_id": sel.course_id})
        credit = catalog.credit_units if catalog else 0
        course = await CourseRecord.find_one({"tenant_id": tenant_id, "course_id": sel.course_id})
        if credit == 0 and course:
            credit = course.credit_units
        reg = StudentCourseRegistration(
            tenant_id=tenant_id,
            user_id=user.id,
            academic_year_label=year,
            semester_label=semester,
            programme_code=programme,
            course_id=sel.course_id,
            course_code=sel.course_code,
            section_code=sel.section_code,
            registration_type=sel.registration_type,
            credit_units=credit,
            status=reg_status,
        )
        try:
            await reg.insert()
        except DuplicateKeyError:
            raise AppError(
                code="CONFLICT",
                message=f"Already registered for {sel.course_code}",
                status_code=409,
            ) from None
        await _append_history(
            tenant_id,
            user.id,
            year=year,
            semester=semester,
            course_id=sel.course_id,
            course_code=sel.course_code,
            action="submitted",
            previous_status=None,
            new_status=reg_status.value,
        )
        if sel.elective_group_id and sel.registration_type == CourseRegistrationType.ELECTIVE:
            egid = to_object_id(sel.elective_group_id, "elective group id")
            try:
                await StudentElectiveSelection(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    academic_year_label=year,
                    semester_label=semester,
                    elective_group_id=egid,
                    course_id=sel.course_id,
                    course_code=sel.course_code,
                    status=reg_status,
                ).insert()
            except DuplicateKeyError:
                pass
    await record_audit(
        actor_id=scope.user_id,
        action="student.registration.submitted",
        resource_type="course_registration_request",
        resource_id=str(req.id),
        tenant_id=tenant_id,
        metadata={"course_count": len(selections)},
    )
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=StudentActivityType.OTHER,
        title="Course registration submitted",
        description=f"{len(selections)} course(s)",
    )
    return RegistrationSubmitRead(
        request_id=str(req.id),
        status=req.status,
        selections=selections,
        submitted_at=req.submitted_at,
    )


async def update_registration(
    scope: AccessScope, user: User, request_id: str, selections: list[RegistrationSelectionInput]
) -> RegistrationSubmitRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_MANAGE)
    tenant_id, programme, year, semester = await _term_and_programme(scope, user)
    policy = await _policy_repo.get_policy(tenant_id, programme, year, semester)
    if policy is None or _now() > policy.modification_deadline:
        raise AppError(code="FORBIDDEN", message="Modification deadline has passed", status_code=403)
    rid = to_object_id(request_id, "request id")
    req = await CourseRegistrationRequest.get(rid)
    if req is None or str(req.tenant_id) != str(tenant_id) or str(req.user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Registration request not found", status_code=404)
    if req.status not in {RegistrationRequestStatus.DRAFT, RegistrationRequestStatus.SUBMITTED}:
        raise AppError(code="FORBIDDEN", message="This request can no longer be modified", status_code=403)
    validation = await _validate_selections(tenant_id, user.id, programme, year, semester, selections)
    if not validation.valid:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Registration validation failed",
            status_code=422,
            details=[{"errors": validation.errors}],
        )
    old_regs = await StudentCourseRegistration.find(
        {
            "tenant_id": tenant_id,
            "user_id": user.id,
            "academic_year_label": year,
            "semester_label": semester,
            "status": CourseRegistrationStatus.SUBMITTED,
        }
    ).to_list()
    for old in old_regs:
        await old.delete()
    req.selections = [
        RegistrationSelectionItem(
            course_id=s.course_id,
            course_code=s.course_code,
            section_code=s.section_code,
            registration_type=s.registration_type,
            elective_group_id=s.elective_group_id,
        )
        for s in selections
    ]
    req.validation_snapshot = validation.model_dump()
    req.updated_at = utcnow()
    await req.save()
    for sel in selections:
        catalog = await CourseCatalogReference.find_one({"tenant_id": tenant_id, "course_id": sel.course_id})
        credit = catalog.credit_units if catalog else 0
        await StudentCourseRegistration(
            tenant_id=tenant_id,
            user_id=user.id,
            academic_year_label=year,
            semester_label=semester,
            programme_code=programme,
            course_id=sel.course_id,
            course_code=sel.course_code,
            section_code=sel.section_code,
            registration_type=sel.registration_type,
            credit_units=credit,
            status=CourseRegistrationStatus.SUBMITTED,
        ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.registration.updated",
        resource_type="course_registration_request",
        resource_id=str(req.id),
        tenant_id=tenant_id,
    )
    return RegistrationSubmitRead(
        request_id=str(req.id),
        status=req.status,
        selections=selections,
        submitted_at=req.submitted_at,
    )


async def cancel_registration(scope: AccessScope, user: User, course_id: str) -> CourseRegistrationRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_MANAGE)
    tenant_id, programme, year, semester = await _term_and_programme(scope, user)
    policy = await _policy_repo.get_policy(tenant_id, programme, year, semester)
    if policy and _now() > policy.modification_deadline:
        raise AppError(code="FORBIDDEN", message="Cancellation deadline has passed", status_code=403)
    reg = await StudentCourseRegistration.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": user.id,
            "academic_year_label": year,
            "semester_label": semester,
            "course_id": course_id,
        }
    )
    if reg is None:
        raise AppError(code="NOT_FOUND", message="Registration not found", status_code=404)
    if reg.status not in {CourseRegistrationStatus.DRAFT, CourseRegistrationStatus.SUBMITTED, CourseRegistrationStatus.PENDING_APPROVAL}:
        raise AppError(code="FORBIDDEN", message="This registration cannot be cancelled", status_code=403)
    prev = reg.status.value
    reg.status = CourseRegistrationStatus.CANCELLED
    reg.cancelled_at = utcnow()
    reg.updated_at = utcnow()
    await reg.save()
    await _append_history(
        tenant_id,
        user.id,
        year=year,
        semester=semester,
        course_id=reg.course_id,
        course_code=reg.course_code,
        action="cancelled",
        previous_status=prev,
        new_status=reg.status.value,
    )
    await record_audit(
        actor_id=scope.user_id,
        action="student.registration.cancelled",
        resource_type="student_course_registration",
        resource_id=str(reg.id),
        tenant_id=tenant_id,
    )
    return CourseRegistrationRead(
        id=str(reg.id),
        course_id=reg.course_id,
        course_code=reg.course_code,
        section_code=reg.section_code,
        registration_type=reg.registration_type,
        credit_units=reg.credit_units,
        status=reg.status,
        academic_year_label=year,
        semester_label=semester,
    )


async def list_confirmed_registrations(scope: AccessScope, user: User) -> list[CourseRegistrationRead]:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, _, year, semester = await _term_and_programme(scope, user)
    rows = await _registration_repo.list_for_student_term(tenant_id, user.id, year, semester)
    return [
        CourseRegistrationRead(
            id=str(r.id),
            course_id=r.course_id,
            course_code=r.course_code,
            section_code=r.section_code,
            registration_type=r.registration_type,
            credit_units=r.credit_units,
            status=r.status,
            academic_year_label=r.academic_year_label,
            semester_label=r.semester_label,
        )
        for r in rows
        if r.status != CourseRegistrationStatus.CANCELLED
    ]


async def get_registration_request(scope: AccessScope, user: User, request_id: str) -> RegistrationRequestRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    rid = to_object_id(request_id, "request id")
    req = await CourseRegistrationRequest.get(rid)
    if req is None or str(req.tenant_id) != str(tenant_id) or str(req.user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Registration request not found", status_code=404)
    return RegistrationRequestRead(
        id=str(req.id),
        status=req.status,
        academic_year_label=req.academic_year_label,
        semester_label=req.semester_label,
        selections=[
            RegistrationSelectionInput(
                course_id=s.course_id,
                course_code=s.course_code,
                section_code=s.section_code,
                registration_type=s.registration_type,
                elective_group_id=s.elective_group_id,
            )
            for s in req.selections
        ],
        reviewer_note=req.reviewer_note,
        submitted_at=req.submitted_at,
        resolved_at=req.resolved_at,
    )


async def registration_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[RegistrationHistoryRead]:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    skip = (pagination.page - 1) * pagination.page_size
    query = RegistrationHistoryEntry.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-occurred_at")
    total = await query.count()
    items = await query.skip(skip).limit(pagination.page_size).to_list()
    return Page(
        items=[
            RegistrationHistoryRead(
                id=str(h.id),
                course_code=h.course_code,
                action=h.action,
                previous_status=h.previous_status,
                new_status=h.new_status,
                occurred_at=h.occurred_at,
            )
            for h in items
        ],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


async def concurrent_registration_guard(
    scope: AccessScope, user: User, selections: list[RegistrationSelectionInput]
) -> RegistrationValidationRead:
    """Used in tests to simulate parallel submits — validates then attempts atomic inserts."""
    authorize(scope, Permission.STUDENT_REGISTRATION_MANAGE)
    tenant_id, programme, year, semester = await _term_and_programme(scope, user)
    validation = await _validate_selections(tenant_id, user.id, programme, year, semester, selections)
    if not validation.valid:
        return validation

    async def _insert_one(sel: RegistrationSelectionInput) -> str | None:
        try:
            reg = StudentCourseRegistration(
                tenant_id=tenant_id,
                user_id=user.id,
                academic_year_label=year,
                semester_label=semester,
                programme_code=programme,
                course_id=sel.course_id,
                course_code=sel.course_code,
                section_code=sel.section_code,
                registration_type=sel.registration_type,
                credit_units=0,
                status=CourseRegistrationStatus.SUBMITTED,
            )
            await reg.insert()
            return None
        except DuplicateKeyError:
            return sel.course_code

    results = await asyncio.gather(*[_insert_one(s) for s in selections])
    dupes = [r for r in results if r]
    if dupes:
        validation.valid = False
        validation.errors.append(f"Duplicate registration blocked: {', '.join(dupes)}")
    return validation
