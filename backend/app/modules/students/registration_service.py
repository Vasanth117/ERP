"""Student course registration and elective selection."""

import asyncio
from collections import defaultdict
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
from app.modules.faculty.models import FacultyAssignment
from app.modules.faculty.enums import AssignmentStatus
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.curriculum_models import (
    CourseCatalogReference,
    CoursePrerequisite,
    CourseRegistrationRequest,
    ElectiveGroup,
    ElectiveOption,
    RegistrationHistoryEntry,
    RegistrationPolicyReference,
    RegistrationSelectionItem,
    StudentCourseRegistration,
    StudentElectiveSelection,
)
from app.modules.students.curriculum_repositories import (
    CourseCatalogRepository,
    RegistrationHistoryRepository,
    RegistrationPolicyRepository,
    RegistrationRequestRepository,
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
    RegistrationClosedPanelRead,
    RegistrationEligibilityRead,
    RegistrationHistoryRead,
    RegistrationOverviewCourseRowRead,
    RegistrationOverviewKpisRead,
    RegistrationOverviewPageRead,
    RegistrationOverviewStepRead,
    RegistrationCourseDetailPageRead,
    RegistrationCourseListRowRead,
    RegistrationCoursesPageRead,
    RegistrationElectiveCatalogueGroupRead,
    RegistrationElectiveCatalogueRowRead,
    RegistrationElectiveCatalogueSectionRead,
    RegistrationElectiveCreditCheckRead,
    RegistrationElectiveGroupSelectionRead,
    RegistrationElectiveOptionChoiceRead,
    RegistrationElectiveSelectionSectionRead,
    RegistrationElectivesPageRead,
    RegistrationFilterOptionRead,
    RegistrationPrerequisiteCheckRead,
    RegistrationRequestRead,
    RegistrationReviewConfirmationDetailRead,
    RegistrationReviewConfirmationSectionRead,
    RegistrationReviewPageRead,
    RegistrationReviewSelectedRowRead,
    RegistrationReviewSummarySectionRead,
    RegistrationReviewTotalsRead,
    RegistrationReviewValidationCheckRead,
    RegistrationReviewValidationSectionRead,
    RegistrationApprovalStepRead,
    RegistrationHistorySectionRead,
    RegistrationHistorySemesterRowRead,
    RegistrationStatusCourseRowRead,
    RegistrationStatusPageRead,
    RegistrationStatusSectionRead,
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
_request_repo = RegistrationRequestRepository()
_activity_repo = StudentActivityRepository()
_reader = StudentDataReader()

_OVERVIEW_PREVIEW_LIMIT = 4
_REGISTRATION_FLOW_STEPS = (
    ("browse", "Browse courses"),
    ("electives", "Select electives"),
    ("validate", "Validate"),
    ("review", "Review summary"),
    ("submit", "Submit"),
    ("confirmation", "Confirmation"),
)

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


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


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


async def _registration_catalog_semester(
    tenant_id: PydanticObjectId, programme: str, year: str, current_semester: str, semester_number: int | None
) -> str:
    reg_sem_number = (semester_number + 1) if semester_number else None
    registration_semester = f"Semester {reg_sem_number}" if reg_sem_number else current_semester
    policy = await _policy_repo.get_policy(tenant_id, programme, year, registration_semester)
    if policy is None:
        policy = await _policy_repo.get_policy(tenant_id, programme, year, current_semester)
    if policy is None:
        fallback_policies = await RegistrationPolicyReference.find(
            {"tenant_id": tenant_id, "programme_code": programme, "academic_year_label": year}
        ).to_list()
        if fallback_policies:
            policy = max(fallback_policies, key=lambda row: row.registration_close_at)
    return registration_semester if policy else current_semester


async def _registration_catalog_context(
    scope: AccessScope, user: User
) -> tuple[PydanticObjectId, str, str, str, str]:
    tenant_id, programme, year, current_semester = await _term_and_programme(scope, user)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    catalog_semester = await _registration_catalog_semester(
        tenant_id, programme, year, current_semester, context.semester_number
    )
    return tenant_id, programme, year, current_semester, catalog_semester


async def _registration_policy_for_term(
    tenant_id: PydanticObjectId,
    programme: str,
    year: str,
    catalog_semester: str,
    current_semester: str,
) -> RegistrationPolicyReference | None:
    policy = await _policy_repo.get_policy(tenant_id, programme, year, catalog_semester)
    if policy is None:
        policy = await _policy_repo.get_policy(tenant_id, programme, year, current_semester)
    return policy


async def _list_student_regs_for_registration_term(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    year: str,
    catalog_semester: str,
    current_semester: str,
) -> list[StudentCourseRegistration]:
    rows = await _registration_repo.list_for_student_term(tenant_id, user_id, year, catalog_semester)
    if not rows and catalog_semester != current_semester:
        rows = await _registration_repo.list_for_student_term(tenant_id, user_id, year, current_semester)
    return rows


async def _find_student_course_registration(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    year: str,
    catalog_semester: str,
    current_semester: str,
    course_id: str,
) -> StudentCourseRegistration | None:
    for semester_label in (catalog_semester, current_semester):
        reg = await StudentCourseRegistration.find_one(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "academic_year_label": year,
                "semester_label": semester_label,
                "course_id": course_id,
            }
        )
        if reg is not None:
            return reg
    return None


async def _default_registration_selections(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    programme: str,
    year: str,
    catalog_semester: str,
    current_semester: str,
) -> list[RegistrationSelectionInput]:
    """Eligible default picks for review when no draft exists (catalog core + one elective per group)."""
    selections: list[RegistrationSelectionInput] = []
    catalog_rows = await _catalog.list_for_term(tenant_id, programme, year, catalog_semester, open_only=True)
    if not catalog_rows and catalog_semester != current_semester:
        catalog_rows = await _catalog.list_for_term(tenant_id, programme, year, current_semester, open_only=True)
    for row in catalog_rows:
        if row.registration_type == CourseRegistrationType.CORE:
            selections.append(
                RegistrationSelectionInput(
                    course_id=row.course_id,
                    course_code=row.course_code,
                    registration_type=CourseRegistrationType.CORE,
                )
            )
    groups = await _elective_groups_for_catalog(tenant_id, programme, year, catalog_semester, current_semester)
    completed = await _registration_repo.completed_course_ids(tenant_id, user_id)
    for group in groups:
        primary_opts, _ = await _options_for_group(tenant_id, group, completed)
        pick = next((o for o in primary_opts if o.eligible), None)
        if pick is None:
            continue
        selections.append(
            RegistrationSelectionInput(
                course_id=pick.course_id,
                course_code=pick.course_code,
                registration_type=CourseRegistrationType.ELECTIVE,
                elective_group_id=str(group.id),
            )
        )
    return selections


def _seats_display_label(max_capacity: int | None, taken: int, *, detailed: bool = False) -> str:
    if max_capacity is None:
        return "—"
    left = max(0, max_capacity - taken)
    if left == 0:
        return "Full"
    if detailed:
        return f"{left} of {max_capacity} left"
    return f"{left} left"


async def get_registration_eligibility(scope: AccessScope, user: User) -> RegistrationEligibilityRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, current_semester, catalog_semester = await _registration_catalog_context(scope, user)
    policy = await _registration_policy_for_term(tenant_id, programme, year, catalog_semester, current_semester)
    reasons: list[str] = []
    if policy is None:
        return RegistrationEligibilityRead(eligible=False, reasons=["Registration policy not configured"])
    now = _now()
    window_open = _aware(policy.registration_open_at) <= now <= _aware(policy.registration_close_at)
    if not policy.allow_self_registration:
        reasons.append("Self-registration is disabled for this programme")
    if not window_open:
        reasons.append("Outside registration window")
    record = await StudentAcademicRecord.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": user.id,
            "academic_year_label": year,
            "semester_label": current_semester,
        }
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
    tenant_id, programme, year, current_semester, catalog_semester = await _registration_catalog_context(scope, user)
    rows = await _catalog.list_for_term(tenant_id, programme, year, catalog_semester, open_only=True)
    if not rows and catalog_semester != current_semester:
        rows = await _catalog.list_for_term(tenant_id, programme, year, current_semester, open_only=True)
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
    tenant_id, programme, year, current_semester, catalog_semester = await _registration_catalog_context(scope, user)
    groups = await _elective_groups_for_catalog(tenant_id, programme, year, catalog_semester, current_semester)
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
        if not (_aware(policy.registration_open_at) <= now <= _aware(policy.registration_close_at)):
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
    tenant_id, programme, year, _current, catalog_semester = await _registration_catalog_context(scope, user)
    return await _validate_selections(tenant_id, user.id, programme, year, catalog_semester, selections)


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
    tenant_id, programme, year, current_semester, catalog_semester = await _registration_catalog_context(scope, user)
    semester = catalog_semester
    validation = await _validate_selections(tenant_id, user.id, programme, year, semester, selections)
    if not validation.valid:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Registration validation failed",
            status_code=422,
            details=[{"errors": validation.errors}],
        )
    policy = await _registration_policy_for_term(tenant_id, programme, year, catalog_semester, current_semester)
    status = (
        RegistrationRequestStatus.UNDER_REVIEW
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
    mutable = await _request_repo.mutable_draft(tenant_id, user.id, year, catalog_semester, current_semester)
    submitted_at = utcnow()
    if mutable is not None:
        mutable.status = status
        mutable.selections = request_items
        mutable.validation_snapshot = validation.model_dump()
        mutable.submitted_at = submitted_at
        mutable.updated_at = submitted_at
        await mutable.save()
        req = mutable
    else:
        req = CourseRegistrationRequest(
            tenant_id=tenant_id,
            user_id=user.id,
            academic_year_label=year,
            semester_label=semester,
            programme_code=programme,
            status=status,
            selections=request_items,
            validation_snapshot=validation.model_dump(),
            submitted_at=submitted_at,
        )
        await req.insert()
    reg_status = (
        CourseRegistrationStatus.PENDING_APPROVAL
        if status == RegistrationRequestStatus.UNDER_REVIEW
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
    tenant_id, programme, year, current_semester, catalog_semester = await _registration_catalog_context(scope, user)
    semester = catalog_semester
    policy = await _registration_policy_for_term(tenant_id, programme, year, catalog_semester, current_semester)
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
            "status": {
                "$in": [
                    CourseRegistrationStatus.SUBMITTED,
                    CourseRegistrationStatus.PENDING_APPROVAL,
                ]
            },
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


async def save_registration_draft(
    scope: AccessScope, user: User, selections: list[RegistrationSelectionInput]
) -> RegistrationSubmitRead:
    """Merge course selections into the student's active draft request for the registration term."""
    authorize(scope, Permission.STUDENT_REGISTRATION_MANAGE)
    tenant_id, programme, year, current_semester, catalog_semester = await _registration_catalog_context(scope, user)
    semester_label = catalog_semester
    draft = await _request_repo.mutable_draft(tenant_id, user.id, year, catalog_semester, current_semester)

    incoming_group_ids = {s.elective_group_id for s in selections if s.elective_group_id}
    incoming_course_ids = {s.course_id for s in selections}
    existing = list(draft.selections) if draft else []
    kept = [
        item
        for item in existing
        if item.elective_group_id not in incoming_group_ids and item.course_id not in incoming_course_ids
    ]
    merged = kept + [
        RegistrationSelectionItem(
            course_id=s.course_id,
            course_code=s.course_code,
            section_code=s.section_code,
            registration_type=s.registration_type,
            elective_group_id=s.elective_group_id,
        )
        for s in selections
    ]

    if draft is None:
        draft = CourseRegistrationRequest(
            tenant_id=tenant_id,
            user_id=user.id,
            academic_year_label=year,
            semester_label=semester_label,
            programme_code=programme,
            status=RegistrationRequestStatus.DRAFT,
            selections=merged,
        )
        await draft.insert()
    else:
        if draft.status != RegistrationRequestStatus.DRAFT:
            raise AppError(code="FORBIDDEN", message="This request can no longer be modified", status_code=403)
        draft.selections = merged
        draft.updated_at = utcnow()
        await draft.save()

    await record_audit(
        actor_id=scope.user_id,
        action="student.registration.draft_saved",
        resource_type="course_registration_request",
        resource_id=str(draft.id),
        tenant_id=tenant_id,
    )
    return RegistrationSubmitRead(
        request_id=str(draft.id),
        status=draft.status,
        selections=[
            RegistrationSelectionInput(
                course_id=s.course_id,
                course_code=s.course_code,
                section_code=s.section_code,
                registration_type=s.registration_type,
                elective_group_id=s.elective_group_id,
            )
            for s in draft.selections
        ],
        submitted_at=draft.submitted_at,
    )


async def cancel_registration(scope: AccessScope, user: User, course_id: str) -> CourseRegistrationRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_MANAGE)
    tenant_id, programme, year, current_semester, catalog_semester = await _registration_catalog_context(scope, user)
    policy = await _registration_policy_for_term(tenant_id, programme, year, catalog_semester, current_semester)
    if policy and _now() > policy.modification_deadline:
        raise AppError(code="FORBIDDEN", message="Cancellation deadline has passed", status_code=403)
    reg = await _find_student_course_registration(
        tenant_id, user.id, year, catalog_semester, current_semester, course_id
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
        semester_label=reg.semester_label,
    )


async def list_confirmed_registrations(scope: AccessScope, user: User) -> list[CourseRegistrationRead]:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, _, year, current_semester, catalog_semester = await _registration_catalog_context(scope, user)
    rows = await _list_student_regs_for_registration_term(
        tenant_id, user.id, year, catalog_semester, current_semester
    )
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


def _format_short_date(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    aware = _aware(dt)
    return aware.strftime("%d %b %Y")


def _format_submitted_at(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    aware = _aware(dt)
    return aware.strftime("%d %b %Y %H:%M")


def _build_flow_steps(active_index: int) -> list[RegistrationOverviewStepRead]:
    steps: list[RegistrationOverviewStepRead] = []
    for idx, (key, label) in enumerate(_REGISTRATION_FLOW_STEPS):
        if idx < active_index:
            state = "completed"
        elif idx == active_index:
            state = "current"
        else:
            state = "upcoming"
        steps.append(RegistrationOverviewStepRead(key=key, label=label, state=state))
    return steps


def _registration_reference_label(req: CourseRegistrationRequest, catalog_semester: str) -> str:
    year_token = req.academic_year_label.split("-")[-1].strip() if "-" in req.academic_year_label else req.academic_year_label
    sem_token = catalog_semester.replace("Semester", "").strip()
    tail = str(req.id)[-4:]
    return f"REG-{year_token}-{sem_token}-{tail}"


def _additional_registration_fees_label(record: StudentAcademicRecord | None) -> str:
    if record is None:
        return "₹0 additional"
    fee = record.fee_snapshot if isinstance(record.fee_snapshot, dict) else {}
    extra = fee.get("registration_additional_amount", fee.get("additional_fee_amount"))
    if isinstance(extra, (int, float)) and float(extra) > 0:
        currency = fee.get("currency_symbol", "₹")
        return f"{currency}{int(extra) if extra == int(extra) else extra} additional"
    return "₹0 additional"


def _confirmation_status_label(status: RegistrationRequestStatus) -> str:
    mapping = {
        RegistrationRequestStatus.SUBMITTED: "Submitted",
        RegistrationRequestStatus.UNDER_REVIEW: "Pending approval",
        RegistrationRequestStatus.APPROVED: "Approved",
        RegistrationRequestStatus.REJECTED: "Rejected",
        RegistrationRequestStatus.CANCELLED: "Cancelled",
        RegistrationRequestStatus.DRAFT: "Draft",
    }
    return mapping.get(status, status.value.replace("_", " ").title())


def _registration_status_tone(status: RegistrationRequestStatus | str | None) -> str:
    if status is None:
        return "muted"
    raw = status.value if isinstance(status, RegistrationRequestStatus) else str(status).lower()
    if raw in {"approved", "submitted"}:
        return "success"
    if raw in {"under_review", "pending_approval", "submitted"}:
        return "info"
    if raw in {"rejected", "cancelled"}:
        return "warning"
    if raw == "draft":
        return "muted"
    return "muted"


def _registration_history_action_label(action: str) -> str:
    return action.replace("_", " ").strip().title() if action else "—"


def _registration_history_status_label(previous: str | None, new: str | None) -> str:
    prev = (previous or "—").replace("_", " ")
    nxt = (new or "—").replace("_", " ")
    return f"{prev} → {nxt}"


def _course_registration_status_label(status: CourseRegistrationStatus) -> str:
    return status.value.replace("_", " ").title()


def _course_registration_status_tone(status: CourseRegistrationStatus) -> str:
    if status in {CourseRegistrationStatus.APPROVED}:
        return "success"
    if status in {CourseRegistrationStatus.SUBMITTED, CourseRegistrationStatus.PENDING_APPROVAL}:
        return "info"
    if status in {CourseRegistrationStatus.REJECTED, CourseRegistrationStatus.CANCELLED}:
        return "warning"
    return "muted"


def _request_course_status_display(status: RegistrationRequestStatus) -> tuple[str, str]:
    if status == RegistrationRequestStatus.APPROVED:
        return "Approved", "success"
    if status in {RegistrationRequestStatus.UNDER_REVIEW, RegistrationRequestStatus.SUBMITTED}:
        return "Pending", "warning"
    if status == RegistrationRequestStatus.REJECTED:
        return "Rejected", "warning"
    return "Pending", "muted"


async def _credits_for_selection_items(
    tenant_id: PydanticObjectId,
    programme: str,
    year: str,
    semester: str,
    items: list[RegistrationSelectionItem],
    course_by_id: dict[str, CourseRecord],
) -> float:
    total = 0.0
    for item in items:
        catalog = await CourseCatalogReference.find_one(
            {
                "tenant_id": tenant_id,
                "programme_code": programme,
                "academic_year_label": year,
                "semester_label": semester,
                "course_id": item.course_id,
            }
        )
        credits = catalog.credit_units if catalog else 0.0
        course = course_by_id.get(item.course_id)
        if course and credits == 0:
            credits = course.credit_units
        total += credits
    return total


def _build_registration_approval_steps(
    request: CourseRegistrationRequest | None,
    policy: RegistrationPolicyReference | None,
) -> list[RegistrationApprovalStepRead]:
    need_dept = policy.require_admin_approval if policy else True

    def step(key: str, label: str, detail: str, state: str, tone: str) -> RegistrationApprovalStepRead:
        return RegistrationApprovalStepRead(key=key, label=label, detail=detail, state=state, tone=tone)

    if request is None or request.submitted_at is None:
        return [
            step("submitted", "Submitted", "Pending", "upcoming", "muted"),
            step("faculty", "Faculty advisor", "Pending", "upcoming", "muted"),
            step("department", "Department head", "Pending", "upcoming", "muted"),
            step("confirmed", "Confirmed", "Pending", "upcoming", "muted"),
        ]

    status = request.status
    submitted_detail = _format_short_date(request.submitted_at)

    if status == RegistrationRequestStatus.APPROVED:
        return [
            step("submitted", "Submitted", submitted_detail, "completed", "success"),
            step("faculty", "Faculty advisor", "Done", "completed", "success"),
            step("department", "Department head", "Done", "completed", "success"),
            step("confirmed", "Confirmed", "Done", "completed", "success"),
        ]

    if need_dept:
        return [
            step("submitted", "Submitted", submitted_detail, "completed", "success"),
            step("faculty", "Faculty advisor", "Done", "completed", "success"),
            step(
                "department",
                "Department head",
                "Pending",
                "current" if status == RegistrationRequestStatus.UNDER_REVIEW else "upcoming",
                "warning",
            ),
            step("confirmed", "Confirmed", "Pending", "upcoming", "muted"),
        ]

    return [
        step("submitted", "Submitted", submitted_detail, "completed", "success"),
        step("faculty", "Faculty advisor", "Done", "completed", "success"),
        step("department", "Department head", "Done", "completed", "success"),
        step("confirmed", "Confirmed", "Pending", "current", "muted"),
    ]


def _draft_to_selection_inputs(draft: CourseRegistrationRequest | None) -> list[RegistrationSelectionInput]:
    if draft is None:
        return []
    return [
        RegistrationSelectionInput(
            course_id=item.course_id,
            course_code=item.course_code,
            section_code=item.section_code,
            registration_type=item.registration_type,
            elective_group_id=item.elective_group_id,
        )
        for item in draft.selections
    ]


async def _build_review_validation_checks(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    programme: str,
    year: str,
    semester: str,
    selections: list[RegistrationSelectionInput],
    validation: RegistrationValidationRead,
) -> tuple[list[RegistrationReviewValidationCheckRead], str | None, str | None]:
    completed = await _registration_repo.completed_course_ids(tenant_id, user_id)
    seat_counts = await _active_registration_counts(tenant_id, year, semester)
    checks: list[RegistrationReviewValidationCheckRead] = []
    courses = await CourseRecord.find({"tenant_id": tenant_id}).to_list()
    course_by_id = {c.course_id: c for c in courses}

    conflict_codes: set[str] = set()
    for conflict in validation.timetable_conflicts:
        for part in conflict.replace("Timetable clash between ", "").split(" on day ")[0].split(" and "):
            code = part.strip()
            if code:
                conflict_codes.add(code)

    alert_title: str | None = None
    alert_body: str | None = None

    for sel in selections:
        course = course_by_id.get(sel.course_id)
        course_name = course.name if course else sel.course_code
        prereq = await CoursePrerequisite.find_one({"tenant_id": tenant_id, "course_id": sel.course_id})
        if prereq and prereq.prerequisite_course_ids:
            missing = [p for p in prereq.prerequisite_course_ids if p not in completed]
            passed = len(missing) == 0
            checks.append(
                RegistrationReviewValidationCheckRead(
                    check_key="prerequisite",
                    check_label="Prerequisite",
                    course_label=course_name,
                    result_label="Passed" if passed else "Missing",
                    result_tone="success" if passed else "warning",
                )
            )

        catalog = await CourseCatalogReference.find_one(
            {
                "tenant_id": tenant_id,
                "programme_code": programme,
                "academic_year_label": year,
                "semester_label": semester,
                "course_id": sel.course_id,
            }
        )
        seats_tone = "success"
        seats_result = "Passed"
        if catalog and catalog.max_capacity is not None:
            taken = seat_counts.get(sel.course_id, 0)
            left = max(0, catalog.max_capacity - taken)
            if left == 0:
                seats_result = "Full"
                seats_tone = "warning"
            elif left <= 5:
                seats_result = f"{left} seats left"
                seats_tone = "warning"
            else:
                seats_result = "Passed"
        else:
            opt = await ElectiveOption.find_one(
                {"tenant_id": tenant_id, "course_id": sel.course_id, "is_active": True}
            )
            if opt is not None and opt.max_seats is not None:
                left = max(0, opt.max_seats - opt.seats_taken)
                if left == 0:
                    seats_result = "Full"
                    seats_tone = "warning"
                elif left <= 5:
                    seats_result = f"{left} seats left"
                    seats_tone = "warning"

        checks.append(
            RegistrationReviewValidationCheckRead(
                check_key="seats",
                check_label="Seat availability",
                course_label=course_name,
                result_label=seats_result,
                result_tone=seats_tone,
            )
        )

        if sel.course_code in conflict_codes:
            checks.append(
                RegistrationReviewValidationCheckRead(
                    check_key="timetable",
                    check_label="Timetable conflict",
                    course_label=course_name,
                    result_label="Conflict",
                    result_tone="warning",
                )
            )
            if alert_title is None:
                alert_title = f"{course_name} has a timetable conflict"
                alert_body = validation.timetable_conflicts[0] if validation.timetable_conflicts else None

    credit_tone = "success" if validation.valid or not any("credit" in e.lower() for e in validation.errors) else "warning"
    credit_label = "Passed"
    if any("exceeds maximum" in e.lower() for e in validation.errors):
        credit_label = "Over limit"
        credit_tone = "warning"
    elif validation.warnings:
        credit_label = "Below minimum"
        credit_tone = "warning"
    checks.append(
        RegistrationReviewValidationCheckRead(
            check_key="credits",
            check_label="Credit limit",
            course_label="All",
            result_label=credit_label,
            result_tone=credit_tone,
        )
    )

    if alert_title is None and validation.errors:
        first = validation.errors[0]
        alert_title = "Registration validation failed"
        alert_body = first

    return checks, alert_title, alert_body


def _fee_clearance_label(record: StudentAcademicRecord | None) -> str:
    if record is None:
        return "—"
    fee = record.fee_snapshot if isinstance(record.fee_snapshot, dict) else {}
    outstanding = fee.get("outstanding_amount")
    if isinstance(outstanding, (int, float)) and float(outstanding) > 0:
        return "Pending"
    status = fee.get("status")
    if isinstance(status, str) and status.strip():
        return status.replace("_", " ").title()
    return "Cleared"


def _registration_type_label(
    registration_type: CourseRegistrationType,
    elective_titles_by_course: dict[str, str],
    course_id: str,
) -> str:
    if registration_type == CourseRegistrationType.CORE:
        return "Core"
    if registration_type == CourseRegistrationType.OPEN:
        return "Open elective"
    title = elective_titles_by_course.get(course_id)
    if title:
        return title
    return "Prof. elective"


async def _elective_category_by_course(
    tenant_id: PydanticObjectId, programme: str, year: str, semester_label: str
) -> dict[str, str]:
    groups = await ElectiveGroup.find(
        {
            "tenant_id": tenant_id,
            "programme_code": programme,
            "academic_year_label": year,
            "semester_label": semester_label,
            "is_active": True,
        }
    ).to_list()
    group_title = {g.id: g.title for g in groups}
    mapping: dict[str, str] = {}
    if not groups:
        return mapping
    group_ids = list(group_title.keys())
    options = await ElectiveOption.find(
        {"tenant_id": tenant_id, "elective_group_id": {"$in": group_ids}, "is_active": True}
    ).to_list()
    for opt in options:
        title = group_title.get(opt.elective_group_id)
        if title:
            mapping[opt.course_id] = title
    return mapping


async def _seat_label_for_course(
    tenant_id: PydanticObjectId,
    year: str,
    semester: str,
    course_id: str,
    max_capacity: int | None,
    taken_counts: dict[str, int],
) -> str:
    if max_capacity is None:
        opt = await ElectiveOption.find_one({"tenant_id": tenant_id, "course_id": course_id, "is_active": True})
        if opt is not None and opt.max_seats is not None:
            left = max(0, opt.max_seats - opt.seats_taken)
            if left == 0:
                return "Full"
            return f"{left} left"
        return "—"
    taken = taken_counts.get(course_id, 0)
    left = max(0, max_capacity - taken)
    if left == 0:
        return "Full"
    return f"{left} left"


async def _active_registration_counts(
    tenant_id: PydanticObjectId, year: str, semester: str
) -> dict[str, int]:
    rows = await StudentCourseRegistration.find(
        {"tenant_id": tenant_id, "academic_year_label": year, "semester_label": semester}
    ).to_list()
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        if row.status in _ACTIVE_REGISTRATION_STATUSES:
            counts[row.course_id] += 1
    return counts


def _derive_registration_status(
    draft_selection_count: int,
    active_registrations: list[StudentCourseRegistration],
    window_open: bool,
) -> tuple[str, int]:
    approved = [r for r in active_registrations if r.status == CourseRegistrationStatus.APPROVED]
    if approved:
        return "Registered", 5
    pending = [
        r
        for r in active_registrations
        if r.status
        in (
            CourseRegistrationStatus.SUBMITTED,
            CourseRegistrationStatus.PENDING_APPROVAL,
        )
    ]
    if pending:
        return "Submitted", 4
    if draft_selection_count > 0:
        return "In progress", max(1, min(3, draft_selection_count))
    if window_open:
        return "Not started", 0
    return "Not registered", 0


async def get_registration_overview_page(scope: AccessScope, user: User) -> RegistrationOverviewPageRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    profile = await ensure_student_profile(scope, user)
    programme = profile.programme_code
    if not programme:
        raise AppError(code="VALIDATION_ERROR", message="Programme is not set on your profile", status_code=422)

    year = context.academic_year_label
    current_semester = context.semester_label
    reg_sem_number = (context.semester_number + 1) if context.semester_number else None
    registration_semester = f"Semester {reg_sem_number}" if reg_sem_number else current_semester

    policy = await _policy_repo.get_policy(tenant_id, programme, year, registration_semester)
    if policy is None:
        policy = await _policy_repo.get_policy(tenant_id, programme, year, current_semester)
    if policy is None:
        fallback_policies = await RegistrationPolicyReference.find(
            {"tenant_id": tenant_id, "programme_code": programme, "academic_year_label": year}
        ).to_list()
        if fallback_policies:
            policy = max(fallback_policies, key=lambda row: row.registration_close_at)

    now = _now()
    window_open = False
    registration_closed = False
    if policy is not None:
        open_at = _aware(policy.registration_open_at)
        close_at = _aware(policy.registration_close_at)
        window_open = open_at <= now <= close_at
        registration_closed = now > close_at

    record = await StudentAcademicRecord.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "academic_year_label": year, "semester_label": current_semester}
    )

    catalog_semester = registration_semester if policy else current_semester
    catalog_rows = await _catalog.list_for_term(tenant_id, programme, year, catalog_semester, open_only=False)
    if not catalog_rows and catalog_semester != current_semester:
        catalog_rows = await _catalog.list_for_term(tenant_id, programme, year, current_semester, open_only=False)

    completed = await _registration_repo.completed_course_ids(tenant_id, user.id)
    seat_counts = await _active_registration_counts(tenant_id, year, catalog_semester)
    elective_map = await _elective_category_by_course(tenant_id, programme, year, catalog_semester)

    course_records = await CourseRecord.find({"tenant_id": tenant_id}).to_list()
    course_by_id = {c.course_id: c for c in course_records}

    preview_rows: list[RegistrationOverviewCourseRowRead] = []
    for row in catalog_rows[:_OVERVIEW_PREVIEW_LIMIT]:
        course = course_by_id.get(row.course_id)
        prereq = await CoursePrerequisite.find_one({"tenant_id": tenant_id, "course_id": row.course_id})
        prereq_label = "—"
        if prereq and prereq.prerequisite_course_ids:
            codes: list[str] = []
            for pid in prereq.prerequisite_course_ids:
                match = course_by_id.get(pid)
                if match:
                    codes.append(match.course_code)
                else:
                    ref = next((c for c in course_records if c.course_id == pid), None)
                    if ref:
                        codes.append(ref.course_code)
            prereq_label = ", ".join(codes) if codes else "—"
        elif prereq and prereq.prerequisite_course_ids is not None:
            prereq_met = True
            if prereq.prerequisite_course_ids:
                prereq_met = all(pid in completed for pid in prereq.prerequisite_course_ids)
            if not prereq_met and prereq.course_code:
                prereq_label = "Prerequisite pending"
        seats_label = await _seat_label_for_course(
            tenant_id, year, catalog_semester, row.course_id, row.max_capacity, seat_counts
        )
        preview_rows.append(
            RegistrationOverviewCourseRowRead(
                course_code=row.course_code,
                course_name=course.name if course else row.course_code,
                category_label=_registration_type_label(row.registration_type, elective_map, row.course_id),
                credit_units=row.credit_units or (course.credit_units if course else 0),
                prerequisite_label=prereq_label,
                seats_label=seats_label,
            )
        )

    active_regs = await _registration_repo.list_for_student_term(tenant_id, user.id, year, catalog_semester)
    draft = await _request_repo.active_draft(tenant_id, user.id, year, catalog_semester)
    draft_count = len(draft.selections) if draft else 0
    selected_course_count = draft_count or len(
        [
            r
            for r in active_regs
            if r.status
            in (
                CourseRegistrationStatus.DRAFT,
                CourseRegistrationStatus.SUBMITTED,
                CourseRegistrationStatus.PENDING_APPROVAL,
                CourseRegistrationStatus.APPROVED,
            )
        ]
    )

    status_label, active_step = _derive_registration_status(draft_count, active_regs, window_open)

    min_c = policy.min_credits if policy else None
    max_c = policy.max_credits if policy else None
    credit_limit_label = "—"
    if min_c is not None and max_c is not None:
        lo = int(min_c) if min_c == int(min_c) else min_c
        hi = int(max_c) if max_c == int(max_c) else max_c
        credit_limit_label = f"{lo} – {hi}"

    window_label = "—"
    window_hint: str | None = None
    if policy is not None:
        window_label = f"{_format_short_date(policy.registration_open_at)} – {_format_short_date(policy.registration_close_at)}"
        open_at = _aware(policy.registration_open_at)
        close_at = _aware(policy.registration_close_at)
        if now < open_at:
            days = max(0, (open_at.date() - now.date()).days)
            window_hint = f"Opens in {days} days" if days else "Opens today"
        elif now <= close_at:
            days = max(0, (close_at.date() - now.date()).days)
            window_hint = f"Closes in {days} days" if days else "Closes today"

    steps: list[RegistrationOverviewStepRead] = []
    for idx, (key, label) in enumerate(_REGISTRATION_FLOW_STEPS):
        if idx < active_step:
            state = "completed"
        elif idx == active_step:
            state = "current"
        else:
            state = "upcoming"
        steps.append(RegistrationOverviewStepRead(key=key, label=label, state=state))

    fee_label = _fee_clearance_label(record)
    fee_ok = fee_label.lower() in {"cleared", "clear", "paid", "no dues"}
    summary = record.eligibility_summary if record and isinstance(record.eligibility_summary, dict) else {}
    prior_flag = summary.get("prior_semester_results_published")
    if prior_flag is None:
        prior_ok = bool(record and record.promotion_eligible)
        prior_sem = (reg_sem_number - 1) if reg_sem_number and reg_sem_number > 1 else None
        prior_title = (
            f"Semester {prior_sem} results published" if prior_sem else "Previous semester results published"
        )
    else:
        prior_ok = bool(prior_flag)
        prior_sem = summary.get("prior_semester_number")
        if isinstance(prior_sem, int):
            prior_title = f"Semester {prior_sem} results published"
        else:
            prior_title = "Previous semester results published"

    prerequisite_checks = [
        RegistrationPrerequisiteCheckRead(
            key="fee_dues",
            title="Clear all fee dues",
            detail=fee_label,
            status_label="Done" if fee_ok else "Pending",
            status_tone="success" if fee_ok else "warning",
        ),
        RegistrationPrerequisiteCheckRead(
            key="prior_results",
            title=prior_title,
            detail="Published" if prior_ok else "Pending",
            status_label="Done" if prior_ok else "Pending",
            status_tone="success" if prior_ok else "warning",
        ),
    ]

    reg_num_display = reg_sem_number or context.semester_number
    open_label = _format_short_date(policy.registration_open_at) if policy else "—"
    page_subtitle = (
        f"Semester {reg_num_display} registration · opens {open_label}"
        if policy and reg_num_display
        else f"Semester {reg_num_display or '—'} registration"
    )

    closed_panel: RegistrationClosedPanelRead | None = None
    if policy is not None:
        close_label = _format_short_date(policy.registration_close_at)
        if registration_closed:
            banner_title = f"Registration closed on {close_label}"
            banner_body = (
                "Late registration needs approval from your department head. Raise a request with a reason."
            )
        else:
            banner_title = f"Registration closes on {close_label}"
            banner_body = (
                "Submit your courses before the window ends. After it closes, late registration "
                "needs approval from your department head."
            )
        closed_panel = RegistrationClosedPanelRead(
            page_title="Registration Period Closed Screen",
            page_subtitle="Shown after the registration window ends",
            banner_title=banner_title,
            banner_body=banner_body,
            raise_request_href="/student/registration/submit",
            window_opened_label=_format_short_date(policy.registration_open_at),
            window_closed_label=close_label,
            student_status_label=status_label,
            show_late_registration_banner=True,
            show_raise_request_action=registration_closed,
        )

    kpis = RegistrationOverviewKpisRead(
        window_label=window_label,
        window_hint=window_hint,
        credit_limit_label=credit_limit_label,
        selected_count=str(selected_course_count),
        status_label=status_label,
    )

    total_courses = len(catalog_rows)
    shown = len(preview_rows)
    footer = f"{shown} of {total_courses}" if total_courses else "0 of 0"

    eligible = window_open and (policy.allow_self_registration if policy else False)
    if record and record.academic_standing == AcademicStanding.SUSPENDED:
        eligible = False

    return RegistrationOverviewPageRead(
        page_title="Course Registration Dashboard",
        page_subtitle=page_subtitle,
        registration_semester_number=reg_sem_number or context.semester_number,
        window_open=window_open,
        show_start_registration=eligible,
        kpis=kpis,
        steps=steps,
        active_step_index=active_step,
        available_courses=preview_rows,
        courses_footer_label=footer,
        prerequisite_checks=prerequisite_checks,
        closed_panel=closed_panel,
    )


async def _prerequisite_label(
    tenant_id: PydanticObjectId,
    course_id: str,
    course_by_id: dict[str, CourseRecord],
    course_records: list[CourseRecord],
    completed: set[str],
) -> tuple[str, bool]:
    prereq = await CoursePrerequisite.find_one({"tenant_id": tenant_id, "course_id": course_id})
    if prereq is None or not prereq.prerequisite_course_ids:
        return "—", True
    codes: list[str] = []
    for pid in prereq.prerequisite_course_ids:
        match = course_by_id.get(pid) or next((c for c in course_records if c.course_id == pid), None)
        if match:
            codes.append(match.course_code)
    label = ", ".join(codes) if codes else "—"
    met = all(pid in completed for pid in prereq.prerequisite_course_ids)
    return label, met


async def _timetable_conflict_messages(
    tenant_id: PydanticObjectId,
    year: str,
    semester: str,
    target_course_code: str,
    other_course_codes: list[str],
) -> list[str]:
    section = "A"
    entries = await TimetableEntry.find(
        {
            "tenant_id": tenant_id,
            "course_code": target_course_code,
            "academic_year_label": year,
            "semester_label": semester,
            "section": section,
        }
    ).to_list()
    if not entries:
        return []
    conflicts: list[str] = []
    for other_code in other_course_codes:
        other_entries = await TimetableEntry.find(
            {
                "tenant_id": tenant_id,
                "course_code": other_code,
                "academic_year_label": year,
                "semester_label": semester,
                "section": section,
            }
        ).to_list()
        for a in entries:
            for b in other_entries:
                if a.day_of_week == b.day_of_week and a.start_time < b.end_time and b.start_time < a.end_time:
                    conflicts.append(f"Clash with {other_code} on day {a.day_of_week}")
    return conflicts


async def get_registration_courses_page(
    scope: AccessScope,
    user: User,
    *,
    semester: str | None = None,
    category: str | None = None,
    q: str | None = None,
) -> RegistrationCoursesPageRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, current_semester = await _term_and_programme(scope, user)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    catalog_semester = await _registration_catalog_semester(
        tenant_id, programme, year, current_semester, context.semester_number
    )
    reg_num = (context.semester_number + 1) if context.semester_number else None
    semester_label = semester or (f"Semester {reg_num}" if reg_num else catalog_semester)
    catalog_rows = await _catalog.list_for_term(tenant_id, programme, year, catalog_semester, open_only=True)
    if not catalog_rows and catalog_semester != current_semester:
        catalog_rows = await _catalog.list_for_term(tenant_id, programme, year, current_semester, open_only=True)

    seat_counts = await _active_registration_counts(tenant_id, year, catalog_semester)
    elective_map = await _elective_category_by_course(tenant_id, programme, year, catalog_semester)
    course_records = await CourseRecord.find({"tenant_id": tenant_id}).to_list()
    course_by_id = {c.course_id: c for c in course_records}
    completed = await _registration_repo.completed_course_ids(tenant_id, user.id)

    rows: list[RegistrationCourseListRowRead] = []
    category_labels: set[str] = set()
    for row in catalog_rows:
        course = course_by_id.get(row.course_id)
        category_label = _registration_type_label(row.registration_type, elective_map, row.course_id)
        category_labels.add(category_label)
        prereq_label, prereq_ok = await _prerequisite_label(
            tenant_id, row.course_id, course_by_id, course_records, completed
        )
        taken = seat_counts.get(row.course_id, 0)
        seats_label = _seats_display_label(row.max_capacity, taken)
        if seats_label == "—":
            seats_label = await _seat_label_for_course(
                tenant_id, year, catalog_semester, row.course_id, row.max_capacity, seat_counts
            )
        rows.append(
            RegistrationCourseListRowRead(
                course_id=row.course_id,
                course_code=row.course_code,
                course_name=course.name if course else row.course_code,
                category_label=category_label,
                credit_units=row.credit_units or (course.credit_units if course else 0),
                prerequisite_label=prereq_label,
                seats_label=seats_label,
                is_selectable=row.is_open_for_registration and prereq_ok and seats_label != "Full",
            )
        )

    selected_category = (category or "all").strip()
    if selected_category and selected_category != "all":
        slug = selected_category.lower()
        rows = [r for r in rows if r.category_label.lower().replace(" ", "_") == slug.replace(" ", "_") or r.category_label.lower() == slug.lower()]
    needle = (q or "").strip().lower()
    if needle:
        rows = [
            r
            for r in rows
            if needle in r.course_code.lower() or needle in r.course_name.lower()
        ]

    category_options = [RegistrationFilterOptionRead(value="all", label="All categories")]
    for label in sorted(category_labels):
        value = label.lower().replace(" ", "_")
        category_options.append(RegistrationFilterOptionRead(value=value, label=label))

    semester_options = [RegistrationFilterOptionRead(value=semester_label, label=semester_label)]

    return RegistrationCoursesPageRead(
        page_title="Available Courses",
        page_subtitle="Courses you are eligible for",
        go_to_selection_href="/student/registration/submit",
        semester_options=semester_options,
        category_options=category_options,
        selected_semester=semester_label,
        selected_category=selected_category or "all",
        search_placeholder="Search course or code",
        courses=rows,
        courses_footer_label=f"{len(rows)} of {len(catalog_rows)}" if catalog_rows else "0 of 0",
        default_course_code=rows[0].course_code if rows else None,
    )


async def get_registration_course_detail_page(
    scope: AccessScope, user: User, course_code: str
) -> RegistrationCourseDetailPageRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, current_semester = await _term_and_programme(scope, user)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    catalog_semester = await _registration_catalog_semester(
        tenant_id, programme, year, current_semester, context.semester_number
    )
    code = course_code.strip().upper()
    catalog = await CourseCatalogReference.find_one(
        {
            "tenant_id": tenant_id,
            "programme_code": programme,
            "academic_year_label": year,
            "semester_label": catalog_semester,
            "course_code": code,
        }
    )
    if catalog is None:
        catalog = await CourseCatalogReference.find_one(
            {
                "tenant_id": tenant_id,
                "programme_code": programme,
                "academic_year_label": year,
                "semester_label": current_semester,
                "course_code": code,
            }
        )
    if catalog is None or not catalog.is_open_for_registration:
        raise AppError(code="NOT_FOUND", message="Course not available for registration", status_code=404)

    course = await CourseRecord.find_one({"tenant_id": tenant_id, "course_id": catalog.course_id})
    if course is None:
        raise AppError(code="NOT_FOUND", message="Course not found", status_code=404)

    elective_map = await _elective_category_by_course(tenant_id, programme, year, catalog_semester)
    category_label = _registration_type_label(catalog.registration_type, elective_map, catalog.course_id)
    seat_counts = await _active_registration_counts(tenant_id, year, catalog_semester)
    taken = seat_counts.get(catalog.course_id, 0)
    seats_label = _seats_display_label(catalog.max_capacity, taken, detailed=True)
    if seats_label == "—":
        seats_label = await _seat_label_for_course(
            tenant_id, year, catalog_semester, catalog.course_id, catalog.max_capacity, seat_counts
        )

    assignments = await FacultyAssignment.find(
        {
            "tenant_id": tenant_id,
            "course_code": code,
            "academic_year_label": year,
            "semester_label": catalog_semester,
            "status": AssignmentStatus.ACTIVE,
        }
    ).to_list()
    faculty_label = "—"
    slot_label = "—"
    if assignments:
        user_ids = {a.user_id for a in assignments}
        users = await User.find({"_id": {"$in": list(user_ids)}}).to_list()
        names = [u.full_name for u in users if u.full_name]
        faculty_label = ", ".join(names) if names else "Faculty"
        slot_label = assignments[0].section or "—"
    if slot_label == "—":
        entry = await TimetableEntry.find_one(
            {
                "tenant_id": tenant_id,
                "course_code": code,
                "academic_year_label": year,
                "semester_label": catalog_semester,
            }
        )
        if entry is not None:
            slot_label = entry.section or "—"

    completed = await _registration_repo.completed_course_ids(tenant_id, user.id)
    course_records = await CourseRecord.find({"tenant_id": tenant_id}).to_list()
    course_by_id = {c.course_id: c for c in course_records}
    prereq_label, prereq_met = await _prerequisite_label(
        tenant_id, catalog.course_id, course_by_id, course_records, completed
    )

    policy = await _policy_repo.get_policy(tenant_id, programme, year, catalog_semester)
    active_regs = await _registration_repo.list_for_student_term(tenant_id, user.id, year, catalog_semester)
    active_codes = [
        r.course_code
        for r in active_regs
        if r.status in _ACTIVE_REGISTRATION_STATUSES and r.course_code.upper() != code
    ]
    selected_credits = sum(
        r.credit_units
        for r in active_regs
        if r.status in _ACTIVE_REGISTRATION_STATUSES
    )
    course_credits = catalog.credit_units or course.credit_units
    max_credits = policy.max_credits if policy else None
    credit_ok = max_credits is None or (selected_credits + course_credits) <= max_credits
    credit_detail = f"Within {int(max_credits) if max_credits == int(max_credits) else max_credits}" if max_credits else "—"
    if not credit_ok and max_credits is not None:
        credit_detail = f"{selected_credits + course_credits} / {max_credits} credits"

    conflicts = await _timetable_conflict_messages(tenant_id, year, catalog_semester, code, active_codes)
    timetable_ok = len(conflicts) == 0

    eligibility_title = f"Prerequisite {prereq_label}" if prereq_label != "—" else "Prerequisites"
    elig_checks = [
        RegistrationPrerequisiteCheckRead(
            key="prerequisite",
            title=eligibility_title,
            detail="Completed" if prereq_met else "Pending",
            status_label="Met" if prereq_met else "Pending",
            status_tone="success" if prereq_met else "warning",
        ),
        RegistrationPrerequisiteCheckRead(
            key="credit_limit",
            title="Credit limit",
            detail=credit_detail,
            status_label="Met" if credit_ok else "Over limit",
            status_tone="success" if credit_ok else "warning",
        ),
        RegistrationPrerequisiteCheckRead(
            key="timetable",
            title="Timetable conflict",
            detail="None" if timetable_ok else conflicts[0],
            status_label="Clear" if timetable_ok else "Conflict",
            status_tone="success" if timetable_ok else "warning",
        ),
    ]

    eligibility_state = await get_registration_eligibility(scope, user)
    show_add = (
        catalog.is_open_for_registration
        and prereq_met
        and credit_ok
        and timetable_ok
        and eligibility_state.window_open
    )

    description = (course.description or "").strip() or "—"
    headline = f"{course.course_code} · {course.name}"

    return RegistrationCourseDetailPageRead(
        page_title="Course Details",
        headline=headline,
        course_code=course.course_code,
        course_name=course.name,
        category_label=category_label,
        credit_units=course_credits,
        faculty_label=faculty_label,
        seats_label=seats_label,
        slot_label=slot_label,
        description=description,
        eligibility=elig_checks,
        add_to_selection_href=f"/student/registration/submit?course={course.course_code}",
        show_add_to_selection=show_add,
        back_href="/student/registration/courses",
    )


async def _elective_groups_for_catalog(
    tenant_id: PydanticObjectId,
    programme: str,
    year: str,
    catalog_semester: str,
    current_semester: str,
) -> list[ElectiveGroup]:
    groups = await ElectiveGroup.find(
        {
            "tenant_id": tenant_id,
            "programme_code": programme,
            "academic_year_label": year,
            "semester_label": catalog_semester,
            "is_active": True,
        }
    ).to_list()
    if not groups:
        groups = await ElectiveGroup.find(
            {
                "tenant_id": tenant_id,
                "programme_code": programme,
                "academic_year_label": year,
                "semester_label": current_semester,
                "is_active": True,
            }
        ).to_list()
    if not groups:
        groups = await ElectiveGroup.find(
            {
                "tenant_id": tenant_id,
                "programme_code": programme,
                "academic_year_label": year,
                "is_active": True,
            }
        ).sort("group_code").to_list()
    return groups


async def _options_for_group(
    tenant_id: PydanticObjectId, group: ElectiveGroup, completed: set[str]
) -> tuple[list[RegistrationElectiveOptionChoiceRead], list[RegistrationElectiveOptionChoiceRead]]:
    options = await ElectiveOption.find(
        {"tenant_id": tenant_id, "elective_group_id": group.id, "is_active": True}
    ).sort("course_code").to_list()
    choices: list[RegistrationElectiveOptionChoiceRead] = []
    for opt in options:
        prereq = await CoursePrerequisite.find_one({"tenant_id": tenant_id, "course_id": opt.course_id})
        eligible = True
        if prereq and prereq.prerequisite_course_ids:
            eligible = all(pid in completed for pid in prereq.prerequisite_course_ids)
        seats = None
        if opt.max_seats is not None:
            seats = max(0, opt.max_seats - opt.seats_taken)
        if seats == 0:
            eligible = False
        choices.append(
            RegistrationElectiveOptionChoiceRead(
                course_id=opt.course_id,
                course_code=opt.course_code,
                course_name=opt.course_name,
                choice_label=f"{opt.course_name} ({opt.course_code})",
                credit_units=opt.credit_units,
                eligible=eligible,
            )
        )
    return choices, list(choices)


async def get_registration_electives_page(scope: AccessScope, user: User) -> RegistrationElectivesPageRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, current_semester = await _term_and_programme(scope, user)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    catalog_semester = await _registration_catalog_semester(
        tenant_id, programme, year, current_semester, context.semester_number
    )
    policy = await _policy_repo.get_policy(tenant_id, programme, year, catalog_semester)
    if policy is None:
        policy = await _policy_repo.get_policy(tenant_id, programme, year, current_semester)

    completed = await _registration_repo.completed_course_ids(tenant_id, user.id)
    groups = await _elective_groups_for_catalog(tenant_id, programme, year, catalog_semester, current_semester)

    draft = await _request_repo.mutable_draft(tenant_id, user.id, year, catalog_semester, current_semester)
    picks_by_group: dict[str, str] = {}
    if draft:
        for item in draft.selections:
            if item.elective_group_id:
                picks_by_group[item.elective_group_id] = item.course_id

    selection_groups: list[RegistrationElectiveGroupSelectionRead] = []
    catalogue_groups: list[RegistrationElectiveCatalogueGroupRead] = []
    selected_credits = 0.0

    for group in groups:
        primary_opts, alt_opts = await _options_for_group(tenant_id, group, completed)
        gid = str(group.id)
        selected_id = picks_by_group.get(gid)
        if selected_id is None:
            selected_id = next((o.course_id for o in primary_opts if o.eligible), None)
        alternate_id = next(
            (o.course_id for o in alt_opts if o.eligible and o.course_id != selected_id),
            None,
        )
        if selected_id:
            match = next((o for o in primary_opts if o.course_id == selected_id), None)
            if match:
                selected_credits += match.credit_units

        selection_groups.append(
            RegistrationElectiveGroupSelectionRead(
                group_id=gid,
                title=group.title,
                choose_label="Choose one *" if group.min_selections >= 1 else "Choose one",
                selected_course_id=selected_id,
                alternate_course_id=alternate_id,
                primary_options=primary_opts,
                alternate_options=alt_opts,
            )
        )

        cat_rows: list[RegistrationElectiveCatalogueRowRead] = []
        for opt in await ElectiveOption.find(
            {"tenant_id": tenant_id, "elective_group_id": group.id, "is_active": True}
        ).sort("course_code").to_list():
            if opt.max_seats is not None:
                left = max(0, opt.max_seats - opt.seats_taken)
                seats_label = "Full" if left == 0 else f"{left} left"
            else:
                seats_label = "—"
            cat_rows.append(
                RegistrationElectiveCatalogueRowRead(
                    course_code=opt.course_code,
                    course_name=opt.course_name,
                    seats_label=seats_label,
                )
            )
        catalogue_groups.append(
            RegistrationElectiveCatalogueGroupRead(
                title=group.title,
                courses=cat_rows,
                footer_label=f"{len(cat_rows)} courses",
            )
        )

    steps = [
        RegistrationOverviewStepRead(key=k, label=label, state="upcoming")
        for k, label in _REGISTRATION_FLOW_STEPS
    ]
    steps[0] = RegistrationOverviewStepRead(key="browse", label="Browse courses", state="completed")
    steps[1] = RegistrationOverviewStepRead(key="electives", label="Select electives", state="current")
    active_step = 1

    min_c = policy.min_credits if policy else None
    max_c = policy.max_credits if policy else None
    allowed = "—"
    if min_c is not None and max_c is not None:
        lo = int(min_c) if min_c == int(min_c) else min_c
        hi = int(max_c) if max_c == int(max_c) else max_c
        allowed = f"{lo} – {hi}"
    within = max_c is None or selected_credits <= max_c
    credit_check = RegistrationElectiveCreditCheckRead(
        selected_detail=f"{int(selected_credits) if selected_credits == int(selected_credits) else selected_credits} credits",
        allowed_range=allowed,
        status_label="Within limit" if within else "Over limit",
        status_tone="success" if within else "warning",
        min_credits=min_c,
        max_credits=max_c,
    )

    draft_request_id = str(draft.id) if draft else None

    return RegistrationElectivesPageRead(
        selection=RegistrationElectiveSelectionSectionRead(
            page_title="Elective Selection",
            page_subtitle="Choose one from each group",
            steps=steps,
            active_step_index=active_step,
            cancel_href="/student/registration/courses",
            review_href="/student/registration/submit",
            draft_request_id=draft_request_id,
            groups=selection_groups,
            credit_check=credit_check,
        ),
        catalogue=RegistrationElectiveCatalogueSectionRead(
            page_title="Elective Catalogue",
            page_subtitle="All electives by group",
            groups=catalogue_groups,
        ),
    )


async def get_registration_review_page(scope: AccessScope, user: User) -> RegistrationReviewPageRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, current_semester = await _term_and_programme(scope, user)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)

    catalog_semester = await _registration_catalog_semester(
        tenant_id, programme, year, current_semester, context.semester_number
    )
    elective_map = await _elective_category_by_course(tenant_id, programme, year, catalog_semester)

    draft = await _request_repo.mutable_draft(tenant_id, user.id, year, catalog_semester, current_semester)
    if draft is None:
        defaults = await _default_registration_selections(
            tenant_id, user.id, programme, year, catalog_semester, current_semester
        )
        if defaults:
            try:
                await save_registration_draft(scope, user, defaults)
            except AppError:
                pass
            draft = await _request_repo.mutable_draft(tenant_id, user.id, year, catalog_semester, current_semester)

    selections = _draft_to_selection_inputs(draft)
    validation = await _validate_selections(
        tenant_id, user.id, programme, year, catalog_semester, selections, check_policy=False
    )

    courses = await CourseRecord.find({"tenant_id": tenant_id}).to_list()
    course_by_id = {c.course_id: c for c in courses}
    selected_rows: list[RegistrationReviewSelectedRowRead] = []
    total_credits = 0.0

    for item in draft.selections if draft else []:
        catalog = await CourseCatalogReference.find_one(
            {
                "tenant_id": tenant_id,
                "programme_code": programme,
                "academic_year_label": year,
                "semester_label": catalog_semester,
                "course_id": item.course_id,
            }
        )
        if catalog is None and catalog_semester != current_semester:
            catalog = await CourseCatalogReference.find_one(
                {
                    "tenant_id": tenant_id,
                    "programme_code": programme,
                    "academic_year_label": year,
                    "semester_label": current_semester,
                    "course_id": item.course_id,
                }
            )
        course = course_by_id.get(item.course_id)
        credits = catalog.credit_units if catalog else 0.0
        if course and credits == 0:
            credits = course.credit_units
        reg_type = (
            catalog.registration_type
            if catalog
            else (item.registration_type if item.registration_type else CourseRegistrationType.ELECTIVE)
        )
        selected_rows.append(
            RegistrationReviewSelectedRowRead(
                course_id=item.course_id,
                course_code=item.course_code,
                course_name=course.name if course else item.course_code,
                category_label=_registration_type_label(reg_type, elective_map, item.course_id),
                credit_units=credits,
                registration_type=reg_type,
                elective_group_id=item.elective_group_id,
            )
        )
        total_credits += credits

    record = await StudentAcademicRecord.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "academic_year_label": year, "semester_label": current_semester}
    )
    count = len(selected_rows)
    credit_display = int(total_credits) if total_credits == int(total_credits) else total_credits
    summary_footer = f"{count} courses • {credit_display} credits"

    submitted_request = None
    for semester_label in (catalog_semester, current_semester):
        submitted_hits = await CourseRegistrationRequest.find(
            {
                "tenant_id": tenant_id,
                "user_id": user.id,
                "academic_year_label": year,
                "semester_label": semester_label,
                "status": {
                    "$in": [
                        RegistrationRequestStatus.SUBMITTED,
                        RegistrationRequestStatus.UNDER_REVIEW,
                        RegistrationRequestStatus.APPROVED,
                    ]
                },
                "submitted_at": {"$ne": None},
            }
        ).sort("-submitted_at").limit(1).to_list()
        if submitted_hits:
            submitted_request = submitted_hits[0]
            break

    policy = await _policy_repo.get_policy(tenant_id, programme, year, catalog_semester)
    require_approval = policy.require_admin_approval if policy else True
    review_days = "2 working days"

    checks, alert_title, alert_body = await _build_review_validation_checks(
        tenant_id, user.id, programme, year, catalog_semester, selections, validation
    )

    validation_section = RegistrationReviewValidationSectionRead(
        page_title="Registration Validation",
        page_subtitle="Messages from the eligibility check",
        steps=_build_flow_steps(2),
        active_step_index=2,
        fix_selection_href="/student/registration/electives",
        alert_title=alert_title,
        alert_body=alert_body,
        checks=checks,
        checks_footer_label=f"{len(checks)} checks",
        is_valid=validation.valid,
    )

    confirmation_section: RegistrationReviewConfirmationSectionRead
    if submitted_request is not None and submitted_request.submitted_at is not None:
        ref = _registration_reference_label(submitted_request, catalog_semester)
        sub_credits = validation.total_credits
        if submitted_request.validation_snapshot:
            snap = submitted_request.validation_snapshot
            if isinstance(snap, dict) and "total_credits" in snap:
                try:
                    sub_credits = float(snap["total_credits"])
                except (TypeError, ValueError):
                    pass
        course_count = len(submitted_request.selections)
        confirmation_section = RegistrationReviewConfirmationSectionRead(
            page_title="Registration Confirmation",
            page_subtitle="Your registration was submitted",
            steps=_build_flow_steps(5),
            active_step_index=5,
            is_submitted=True,
            success_title="Registration submitted",
            success_body=(
                f"Reference {ref}. Your department will review it within {review_days}."
                if require_approval
                else f"Reference {ref}. Your registration is confirmed."
            ),
            download_slip_href=None,
            view_status_href="/student/registration/history",
            details=[
                RegistrationReviewConfirmationDetailRead(key="reference", label="Reference", value=ref),
                RegistrationReviewConfirmationDetailRead(key="courses", label="Courses", value=str(course_count)),
                RegistrationReviewConfirmationDetailRead(
                    key="status",
                    label="Status",
                    value=_confirmation_status_label(submitted_request.status),
                ),
                RegistrationReviewConfirmationDetailRead(
                    key="submitted",
                    label="Submitted",
                    value=_format_submitted_at(submitted_request.submitted_at),
                ),
                RegistrationReviewConfirmationDetailRead(
                    key="credits",
                    label="Credits",
                    value=str(int(sub_credits) if sub_credits == int(sub_credits) else sub_credits),
                ),
            ],
        )
    else:
        confirmation_section = RegistrationReviewConfirmationSectionRead(
            page_title="Registration Confirmation",
            page_subtitle="After you submit",
            steps=_build_flow_steps(5),
            active_step_index=5,
            is_submitted=False,
            pending_title="Awaiting submission",
            pending_body="Submit your registration above. Your reference, status, and timestamps will appear here.",
            success_title="Registration submitted",
            success_body="",
            download_slip_href=None,
            view_status_href="/student/registration/history",
            details=[],
        )

    if confirmation_section.is_submitted:
        default_sub_panel = "confirmation"
    else:
        default_sub_panel = "validation" if not validation.valid else "confirmation"

    return RegistrationReviewPageRead(
        summary=RegistrationReviewSummarySectionRead(
            page_title="Selected Courses Summary",
            page_subtitle="Review before you submit",
            steps=_build_flow_steps(3),
            active_step_index=3,
            back_href="/student/registration/electives",
            submit_enabled=len(selections) > 0 and validation.valid,
            selected_rows=selected_rows,
            footer_label=summary_footer,
            totals=RegistrationReviewTotalsRead(
                course_count=count,
                credit_units=total_credits,
                fees_label=_additional_registration_fees_label(record),
            ),
            declaration_label="I have read the registration rules",
            draft_request_id=str(draft.id) if draft else None,
        ),
        validation=validation_section,
        confirmation=confirmation_section,
        default_sub_panel="confirmation" if default_sub_panel == "confirmation" else "validation",
    )


async def get_registration_status_page(scope: AccessScope, user: User) -> RegistrationStatusPageRead:
    authorize(scope, Permission.STUDENT_REGISTRATION_READ)
    tenant_id, programme, year, current_semester = await _term_and_programme(scope, user)
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    catalog_semester = await _registration_catalog_semester(
        tenant_id, programme, year, current_semester, context.semester_number
    )
    policy = await _registration_policy_for_term(tenant_id, programme, year, catalog_semester, current_semester)

    courses = await CourseRecord.find({"tenant_id": tenant_id}).to_list()
    course_by_id = {c.course_id: c for c in courses}

    draft = await _request_repo.mutable_draft(tenant_id, user.id, year, catalog_semester, current_semester)

    current_request = None
    for semester_label in (catalog_semester, current_semester):
        submitted_hits = await CourseRegistrationRequest.find(
            {
                "tenant_id": tenant_id,
                "user_id": user.id,
                "academic_year_label": year,
                "semester_label": semester_label,
                "submitted_at": {"$ne": None},
            }
        ).sort("-submitted_at").limit(1).to_list()
        if submitted_hits:
            current_request = submitted_hits[0]
            break
    if current_request is None:
        for semester_label in (catalog_semester, current_semester):
            hits = await CourseRegistrationRequest.find(
                {
                    "tenant_id": tenant_id,
                    "user_id": user.id,
                    "academic_year_label": year,
                    "semester_label": semester_label,
                }
            ).sort("-updated_at").limit(1).to_list()
            if hits:
                current_request = hits[0]
                break
    if current_request is None and draft is not None:
        current_request = draft

    page_subtitle = "Draft registration"
    if current_request is not None and current_request.submitted_at is not None:
        page_subtitle = _registration_reference_label(current_request, catalog_semester)
    elif draft is not None and draft.selections:
        page_subtitle = draft.semester_label

    active_regs = await _list_student_regs_for_registration_term(
        tenant_id, user.id, year, catalog_semester, current_semester
    )

    reg_by_course = {r.course_id: r for r in active_regs if r.status != CourseRegistrationStatus.CANCELLED}
    status_courses: list[RegistrationStatusCourseRowRead] = []

    selection_source = (
        list(current_request.selections)
        if current_request and current_request.selections
        else (list(draft.selections) if draft and draft.selections else [])
    )

    req_status = current_request.status if current_request else RegistrationRequestStatus.DRAFT
    default_label, default_tone = _request_course_status_display(req_status)

    if selection_source:
        for item in selection_source:
            course = course_by_id.get(item.course_id)
            reg = reg_by_course.get(item.course_id)
            if reg:
                label = _course_registration_status_label(reg.status)
                tone = _course_registration_status_tone(reg.status)
                credits = reg.credit_units
            else:
                catalog = await CourseCatalogReference.find_one(
                    {
                        "tenant_id": tenant_id,
                        "programme_code": programme,
                        "academic_year_label": year,
                        "semester_label": catalog_semester,
                        "course_id": item.course_id,
                    }
                )
                credits = catalog.credit_units if catalog else (course.credit_units if course else 0)
                label, tone = default_label, default_tone
            status_courses.append(
                RegistrationStatusCourseRowRead(
                    course_code=item.course_code,
                    course_name=course.name if course else item.course_code,
                    status_label=label,
                    status_tone=tone,
                    credit_units=credits,
                )
            )
    else:
        for reg in active_regs:
            course = course_by_id.get(reg.course_id)
            status_courses.append(
                RegistrationStatusCourseRowRead(
                    course_code=reg.course_code,
                    course_name=course.name if course else reg.course_code,
                    status_label=_course_registration_status_label(reg.status),
                    status_tone=_course_registration_status_tone(reg.status),
                    credit_units=reg.credit_units,
                )
            )

    max_slots = len(selection_source) if selection_source else max(len(status_courses), 1)
    courses_footer = f"{len(status_courses)} of {max_slots}"

    approval_steps = _build_registration_approval_steps(
        current_request if current_request and current_request.submitted_at else None,
        policy,
    )

    submitted_all = await CourseRegistrationRequest.find(
        {
            "tenant_id": tenant_id,
            "user_id": user.id,
            "submitted_at": {"$ne": None},
            "status": {
                "$nin": [RegistrationRequestStatus.DRAFT, RegistrationRequestStatus.CANCELLED],
            },
        }
    ).sort("-submitted_at").limit(20).to_list()

    current_id = str(current_request.id) if current_request and current_request.submitted_at else None
    history_rows: list[RegistrationHistorySemesterRowRead] = []
    for req in submitted_all:
        if current_id and str(req.id) == current_id:
            continue
        credits = await _credits_for_selection_items(
            tenant_id, programme, req.academic_year_label, req.semester_label, req.selections, course_by_id
        )
        credit_display = int(credits) if credits == int(credits) else credits
        history_rows.append(
            RegistrationHistorySemesterRowRead(
                reference_label=_registration_reference_label(req, req.semester_label),
                semester_label=req.semester_label,
                course_count=len(req.selections),
                credit_units=credit_display,
                submitted_at_label=_format_short_date(req.submitted_at),
                status_label=_confirmation_status_label(req.status),
                status_tone=_registration_status_tone(req.status),
            )
        )

    total_history = len(submitted_all)
    shown = len(history_rows)
    history_footer = f"{shown} of {total_history}" if total_history else "0 records"

    return RegistrationStatusPageRead(
        status=RegistrationStatusSectionRead(
            page_title="Registration Status",
            page_subtitle=page_subtitle,
            courses=status_courses,
            courses_footer_label=courses_footer,
            approval_steps=approval_steps,
        ),
        history=RegistrationHistorySectionRead(
            page_title="Registration History",
            page_subtitle="Earlier semesters",
            rows=history_rows,
            footer_label=history_footer,
        ),
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
    tenant_id, programme, year, current_semester, catalog_semester = await _registration_catalog_context(scope, user)
    semester = catalog_semester
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
