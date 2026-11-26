"""Student academic and enrollment views (read) plus permitted requests."""

import re
from datetime import datetime, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.enums import (
    StudentAcademicRequestStatus,
    StudentAcademicRequestType,
    StudentActivityType,
    StudentEnrollmentStatus,
    StudentTermEnrollmentConfirmationStatus,
)
from app.modules.students.curriculum_repositories import RegistrationPolicyRepository
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.college_admin.academic_config_models import (
    AcademicProgramme,
    AcademicRegulation,
    ConfigPublicationStatus,
)
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.models import InstitutionProfile
from app.modules.department_admin.models import DepartmentProfileDetails
from app.modules.students.arrear_backlog_enums import BacklogStatus
from app.modules.students.arrear_backlog_models import StudentArrearReference
from app.modules.students.models import (
    StudentAcademicRecord,
    StudentAcademicRequest,
    StudentEnrollment,
    StudentEnrollmentHistory,
    StudentTermEnrollmentConfirmation,
)
from app.modules.students.policy import require_student_scope
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.academics.models import AcademicYearContext
from app.modules.students.profile_service import _department_name, _load_admission, ensure_student_profile
from app.modules.students.repositories import (
    StudentAcademicRecordRepository,
    StudentActivityRepository,
    StudentEnrollmentHistoryRepository,
    StudentEnrollmentRepository,
)
from app.common.time import utcnow
from app.modules.students.schemas import (
    AcademicDetailsRead,
    AcademicEligibilityRead,
    AcademicProgressionDetailsRead,
    AcademicStatusDetailsRead,
    AcademicStatusPendingRequirementRead,
    AcademicStatusStandingFieldRead,
    CourseCreditCategoryRowRead,
    CourseCreditSummaryRead,
    CurrentSemesterOverviewRead,
    AdmissionInfoRead,
    DepartmentProgrammeRead,
    EnrollmentConfirmResultRead,
    EnrollmentConfirmationHistoryRowRead,
    EnrollmentConfirmationRead,
    EnrollmentDeclarationUpdate,
    EnrollmentHistoryRead,
    EnrollmentLineRead,
    EnrollmentRequestCreate,
    EnrollmentRequestRead,
    EnrollmentStatusRead,
    ProgrammeDepartmentContextRead,
    ProgressionPolicyRead,
    ProgressionTransitionRead,
    SemesterSubjectsTermRead,
    StudentAcademicAdvisorRead,
    StudentAcademicInformationRead,
    StudentDepartmentContactsRead,
    StudentDepartmentDetailsRead,
    StudentProgrammeDetailsRead,
    _semester_number_from_label,
    enrollment_history_from_doc,
    enrollment_line_from_doc,
    enrollment_status_from_record,
    request_from_doc,
    semester_academic_history_from_doc,
)

_reader = StudentDataReader()
_enrollment_repo = StudentEnrollmentRepository()
_history_repo = StudentEnrollmentHistoryRepository()
_record_repo = StudentAcademicRecordRepository()
_activity_repo = StudentActivityRepository()
_registration_policy_repo = RegistrationPolicyRepository()

_PERMITTED_REQUEST_TYPES = frozenset(
    {
        StudentAcademicRequestType.SECTION_CHANGE,
        StudentAcademicRequestType.COURSE_ADD,
        StudentAcademicRequestType.COURSE_DROP,
        StudentAcademicRequestType.LEAVE_OF_ABSENCE,
        StudentAcademicRequestType.OTHER,
    }
)


def _summary_int(summary: dict, *keys: str) -> int | None:
    for key in keys:
        raw = summary.get(key)
        if isinstance(raw, bool):
            continue
        if isinstance(raw, (int, float)):
            return int(raw)
    return None


def _summary_float(summary: dict, *keys: str) -> float | None:
    for key in keys:
        raw = summary.get(key)
        if isinstance(raw, bool):
            continue
        if isinstance(raw, (int, float)):
            return float(raw)
    return None


def _programme_total_semesters(meta: dict, summary: dict) -> int | None:
    total = _summary_int(summary, "total_semesters")
    if total is not None:
        return total
    duration = meta.get("programme_duration_years")
    if duration is not None:
        try:
            years = int(duration)
            if years > 0:
                return years * 2
        except (TypeError, ValueError):
            pass
    return None


def _batch_display_label(batch_label: str | None, metadata: dict) -> str | None:
    if not batch_label:
        return None
    explicit = metadata.get("batch_display")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    raw = batch_label.strip()
    if "–" in raw or ("-" in raw and len(raw) > 6):
        return raw.replace("-", "–")
    try:
        start = int(raw[:4])
        duration = metadata.get("programme_duration_years")
        years = int(duration) if duration is not None else 4
        return f"{start}–{start + years}"
    except (TypeError, ValueError):
        return raw


async def _programme_regulation(tenant_id: PydanticObjectId, programme_code: str | None) -> str | None:
    if not programme_code:
        return None
    course = await CourseRecord.find_one(
        Eq(CourseRecord.tenant_id, tenant_id),
        Eq(CourseRecord.course_code, programme_code),
    )
    if course is None or not course.regulation_label:
        return None
    return course.regulation_label


async def _current_semester_number(tenant_id: PydanticObjectId) -> int | None:
    context = await AcademicYearContext.find_one(
        Eq(AcademicYearContext.tenant_id, tenant_id),
        Eq(AcademicYearContext.is_current, True),
    )
    if context is None:
        return None
    if context.semester_number is not None:
        return context.semester_number
    import re
    match = re.search(r"\d+", context.semester_label)
    if match:
        try:
            return int(match.group())
        except ValueError:
            pass
    return None


async def _user_display_name(user_id: PydanticObjectId | None) -> str | None:
    if user_id is None:
        return None
    user = await User.get(user_id)
    return user.full_name if user else None


async def _load_institution_profile(tenant_id: PydanticObjectId) -> InstitutionProfile | None:
    return await InstitutionProfile.find_one(Eq(InstitutionProfile.tenant_id, tenant_id))


async def _load_academic_programme(
    tenant_id: PydanticObjectId,
    programme_code: str | None,
) -> AcademicProgramme | None:
    if not programme_code:
        return None
    programme = await AcademicProgramme.find_one(
        Eq(AcademicProgramme.tenant_id, tenant_id),
        Eq(AcademicProgramme.programme_code, programme_code),
    )
    if programme is not None:
        return programme
    normalised = programme_code.replace(" ", "").replace(".", "").upper()
    cursor = AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id))
    async for row in cursor:
        row_key = row.programme_code.replace(" ", "").replace(".", "").upper()
        if row_key == normalised or normalised in row_key or row_key in normalised:
            return row
    return None


async def _resolve_institution_department(
    tenant_id: PydanticObjectId,
    department_name: str | None,
    programme_code: str | None,
) -> InstitutionDepartment | None:
    if programme_code:
        institution = await InstitutionDepartment.find_one(
            {"tenant_id": tenant_id, "programme_codes": programme_code},
        )
        if institution is not None:
            return institution
    if department_name:
        return await InstitutionDepartment.find_one(
            Eq(InstitutionDepartment.tenant_id, tenant_id),
            Eq(InstitutionDepartment.name, department_name),
        )
    return None


async def _load_department_profile_details(
    tenant_id: PydanticObjectId,
    institution_department_id: PydanticObjectId | None,
) -> DepartmentProfileDetails | None:
    if institution_department_id is None:
        return None
    return await DepartmentProfileDetails.find_one(
        Eq(DepartmentProfileDetails.tenant_id, tenant_id),
        Eq(DepartmentProfileDetails.institution_department_id, institution_department_id),
    )


async def _published_progression_regulation(tenant_id: PydanticObjectId) -> AcademicRegulation | None:
    return await AcademicRegulation.find(
        {
            "tenant_id": tenant_id,
            "scope_key": "progression",
            "status": ConfigPublicationStatus.PUBLISHED,
        }
    ).sort("-version").first_or_none()


def _term_odd_even_label(semester_label: str) -> str | None:
    label = semester_label.strip().lower()
    if "odd" in label:
        return "Odd"
    if "even" in label:
        return "Even"
    match = re.search(r"\b(\d{1,2})\b", semester_label)
    if match:
        num = int(match.group(1))
        return "Odd" if num % 2 == 1 else "Even"
    return None


def _build_current_semester_overview(
    enrollments: list,
    enrollment_status: EnrollmentStatusRead,
    academic_information: StudentAcademicInformationRead,
    record: StudentAcademicRecord | None,
) -> CurrentSemesterOverviewRead:
    subject_count = len(enrollments)
    credits = sum(getattr(line, "credits", 0) or 0 for line in enrollments)
    summary = record.eligibility_summary if record is not None else {}

    def _summary_str(*keys: str) -> str | None:
        for key in keys:
            raw = summary.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
        return None

    def _summary_float(*keys: str) -> float | None:
        for key in keys:
            raw = summary.get(key)
            if isinstance(raw, (int, float)) and not isinstance(raw, bool):
                return float(raw)
        return None

    internal_done = summary.get("internal_tests_completed")
    internal_total = summary.get("internal_tests_total")
    internal_label = _summary_str("internal_tests_label")
    if internal_label is None and isinstance(internal_done, (int, float)) and isinstance(internal_total, (int, float)):
        internal_label = f"{int(internal_done)} of {int(internal_total)} done"

    attendance = _summary_float("aggregate_attendance_percent", "attendance_percent")
    sem_num = academic_information.current_semester_number
    odd_even = _term_odd_even_label(enrollment_status.semester_label)
    parts: list[str] = []
    if sem_num is not None:
        parts.append(f"Semester {sem_num}")
    if enrollment_status.academic_year_label and enrollment_status.academic_year_label != "N/A":
        parts.append(f"AY {enrollment_status.academic_year_label}")
    if odd_even:
        parts.append(odd_even)
    term_subtitle = " · ".join(parts) if parts else None

    return CurrentSemesterOverviewRead(
        term_subtitle=term_subtitle,
        subject_count=subject_count,
        credits_registered=credits,
        internal_tests_label=internal_label,
        attendance_percent=attendance,
        next_exam_title=_summary_str("next_exam_label", "next_exam_title"),
        next_exam_date_label=_summary_str("next_exam_date_label", "next_exam_date"),
    )


def _category_row_from_mapping(item: dict) -> CourseCreditCategoryRowRead | None:
    category = item.get("category")
    if not isinstance(category, str) or not category.strip():
        return None

    def _num(*keys: str) -> float:
        for key in keys:
            raw = item.get(key)
            if isinstance(raw, bool):
                continue
            if isinstance(raw, (int, float)):
                return float(raw)
        return 0.0

    required = _num("credits_required", "required")
    earned = _num("credits_earned", "earned")
    in_progress = _num("credits_in_progress", "in_progress")
    remaining = _num("credits_remaining", "remaining")
    if remaining == 0.0 and required > 0:
        remaining = max(required - earned - in_progress, 0.0)
    return CourseCreditCategoryRowRead(
        category=category.strip(),
        credits_required=required,
        credits_earned=earned,
        credits_in_progress=in_progress,
        credits_remaining=remaining,
    )


def _build_course_credit_summary(
    record: StudentAcademicRecord | None,
    enrollments: list[EnrollmentLineRead],
    academic_information: StudentAcademicInformationRead,
) -> CourseCreditSummaryRead:
    summary = record.eligibility_summary if record is not None else {}
    earned = float(record.credits_earned) if record is not None else 0.0
    in_progress = (
        float(record.credits_registered)
        if record is not None and record.credits_registered
        else sum((line.credits or 0.0) for line in enrollments)
    )
    required = _summary_float(summary, "minimum_credits_required", "credits_required")
    if required is None:
        required = academic_information.minimum_credits_required
    required = float(required) if required is not None else 0.0
    remaining = max(required - earned - in_progress, 0.0)

    sem_label: str | None = None
    if academic_information.current_semester_number is not None:
        sem_label = f"Semester {academic_information.current_semester_number}"

    categories: list[CourseCreditCategoryRowRead] = []
    raw_cats = summary.get("credit_by_category")
    if isinstance(raw_cats, list):
        for item in raw_cats:
            if isinstance(item, dict):
                row = _category_row_from_mapping(item)
                if row is not None:
                    categories.append(row)

    return CourseCreditSummaryRead(
        credits_earned=earned,
        credits_in_progress=in_progress,
        credits_remaining=remaining,
        credits_required=required,
        in_progress_semester_label=sem_label,
        categories=categories,
    )


async def _build_semester_subject_terms(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    current_year: str,
    current_semester: str,
    current_semester_number: int | None,
) -> list[SemesterSubjectsTermRead]:
    rows = await StudentEnrollment.find({"tenant_id": tenant_id, "user_id": user_id}).sort(
        "academic_year_label", "semester_label", "course_code"
    ).to_list()
    buckets: dict[tuple[str, str], list[EnrollmentLineRead]] = {}
    for row in rows:
        key = (row.academic_year_label, row.semester_label)
        buckets.setdefault(key, []).append(enrollment_line_from_doc(row))

    terms: list[SemesterSubjectsTermRead] = []
    for (year, semester), subjects in buckets.items():
        is_current = year == current_year and semester == current_semester
        sem_num = current_semester_number if is_current and current_semester_number is not None else _semester_number_from_label(semester)
        terms.append(
            SemesterSubjectsTermRead(
                academic_year_label=year,
                semester_label=semester,
                semester_number=sem_num,
                is_current=is_current,
                subjects=subjects,
            )
        )

    def _sort_key(term: SemesterSubjectsTermRead) -> tuple[int, int, str, str]:
        return (
            1 if term.is_current else 0,
            term.semester_number or 0,
            term.academic_year_label,
            term.semester_label,
        )

    terms.sort(key=_sort_key, reverse=True)
    return terms


def _aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _summary_datetime(summary: dict, *keys: str) -> datetime | None:
    for key in keys:
        raw = summary.get(key)
        if isinstance(raw, datetime):
            return _aware_datetime(raw)
        if isinstance(raw, str) and raw.strip():
            try:
                return _aware_datetime(datetime.fromisoformat(raw.replace("Z", "+00:00")))
            except ValueError:
                continue
    return None


def _summary_bool(summary: dict, *keys: str) -> bool:
    for key in keys:
        raw = summary.get(key)
        if isinstance(raw, bool):
            return raw
    return False


def _format_short_date(dt: datetime) -> str:
    return dt.strftime("%d %b %Y")


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


def _enrollment_eligibility_label(
    record: StudentAcademicRecord | None,
    academic_information: StudentAcademicInformationRead,
    summary: dict,
) -> str:
    custom = summary.get("enrollment_eligibility_label")
    if isinstance(custom, str) and custom.strip():
        return custom.strip()
    if record is not None and record.promotion_eligible is False:
        current = academic_information.current_semester_number
        if current is not None:
            return f"Pending Semester {current} results"
    if record is not None and record.promotion_eligible:
        return "Eligible"
    return "Pending review"


def _attendance_condition_label(
    summary: dict,
    progression_regulation: AcademicRegulation | None,
) -> str:
    custom = summary.get("enrollment_attendance_condition_label")
    if isinstance(custom, str) and custom.strip():
        return custom.strip()
    min_attendance: float | None = None
    if progression_regulation is not None and isinstance(progression_regulation.rules, dict):
        raw = progression_regulation.rules.get("min_attendance_percent")
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            min_attendance = float(raw)
    if min_attendance is None:
        min_attendance = _summary_float(summary, "minimum_attendance_percent")
    if min_attendance is not None:
        pct = int(min_attendance) if min_attendance == int(min_attendance) else min_attendance
        return f"{pct}% or above"
    return "—"


def _confirmation_status_tone(status: str) -> str:
    upper = status.upper()
    if upper == StudentTermEnrollmentConfirmationStatus.CONFIRMED.value.upper():
        return "success"
    if upper == StudentTermEnrollmentConfirmationStatus.PENDING.value.upper():
        return "info"
    return "muted"


def _enum_display_label(value: object | None) -> str:
    if value is None:
        return "—"
    raw = value.value if hasattr(value, "value") else value
    text = str(raw).strip()
    if not text or text.lower() == "unknown":
        return "—"
    return text.replace("_", " ").title()


def _academic_standing_short_label(enrollment_status: EnrollmentStatusRead) -> str:
    raw = enrollment_status.academic_standing
    token = raw.value if hasattr(raw, "value") else raw
    if str(token).lower() in {"good", "normal"}:
        return "Good"
    label = _enum_display_label(raw)
    if label.lower() in {"good standing", "good"}:
        return "Good"
    return label


def _format_percent_value(value: float | None) -> str:
    if value is None:
        return "—"
    if value == int(value):
        return f"{int(value)}%"
    return f"{round(value, 1)}%"


def _disciplinary_action_label(summary: dict) -> str:
    custom = summary.get("disciplinary_action_label")
    if isinstance(custom, str) and custom.strip():
        return custom.strip()
    if summary.get("disciplinary_action") is True:
        detail = summary.get("disciplinary_action_detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
        return "Active"
    return "None"


def _academic_holds_label(record: StudentAcademicRecord | None, summary: dict) -> str:
    custom = summary.get("academic_holds_label")
    if isinstance(custom, str) and custom.strip():
        return custom.strip()
    if record is not None:
        fee = record.fee_snapshot if isinstance(record.fee_snapshot, dict) else {}
        outstanding = fee.get("outstanding_amount")
        if isinstance(outstanding, (int, float)) and float(outstanding) > 0:
            currency = fee.get("currency")
            amount = float(outstanding)
            if isinstance(currency, str) and currency.strip():
                return f"Fee hold ({currency} {amount:g})"
            return f"Fee hold ({amount:g})"
    holds = summary.get("active_holds")
    if isinstance(holds, list) and holds:
        labels = [str(item).strip() for item in holds if str(item).strip()]
        if labels:
            return ", ".join(labels[:3])
    return "None"


async def _count_active_backlogs(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> int:
    return await StudentArrearReference.find(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "backlog_status": {"$in": [BacklogStatus.PENDING, BacklogStatus.REGISTERED]},
        }
    ).count()


def _pending_requirement_from_summary_entry(entry: object) -> AcademicStatusPendingRequirementRead | None:
    if not isinstance(entry, dict):
        return None
    title = entry.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    detail = entry.get("detail")
    detail_text = detail.strip() if isinstance(detail, str) and detail.strip() else None
    status_label = entry.get("status_label")
    if not isinstance(status_label, str) or not status_label.strip():
        status_label = "Pending"
    status_tone = entry.get("status_tone")
    icon_tone = entry.get("icon_tone")
    action_href = entry.get("action_href")
    return AcademicStatusPendingRequirementRead(
        title=title.strip(),
        detail=detail_text,
        status_label=status_label.strip(),
        status_tone=status_tone.strip() if isinstance(status_tone, str) and status_tone.strip() else "info",
        icon_tone=icon_tone.strip() if isinstance(icon_tone, str) and icon_tone.strip() else "info",
        action_href=action_href.strip() if isinstance(action_href, str) and action_href.strip() else None,
    )


def _derive_pending_requirements(
    record: StudentAcademicRecord | None,
    academic_information: StudentAcademicInformationRead,
    enrollment_confirmation: EnrollmentConfirmationRead | None,
    progression_regulation: AcademicRegulation | None,
) -> list[AcademicStatusPendingRequirementRead]:
    summary = record.eligibility_summary if record is not None else {}
    configured = summary.get("pending_requirements")
    if isinstance(configured, list) and configured:
        items: list[AcademicStatusPendingRequirementRead] = []
        for entry in configured:
            row = _pending_requirement_from_summary_entry(entry)
            if row is not None:
                items.append(row)
        if items:
            return items

    items = []
    eligibility = _enrollment_eligibility_label(record, academic_information, summary)
    eligibility_lower = eligibility.lower()
    if record is not None and record.promotion_eligible is False:
        items.append(
            AcademicStatusPendingRequirementRead(
                title="Academic eligibility",
                detail=eligibility,
                status_label="Pending",
                status_tone="warning",
                icon_tone="alert",
            )
        )
    elif "pending" in eligibility_lower or "not eligible" in eligibility_lower:
        items.append(
            AcademicStatusPendingRequirementRead(
                title="Academic eligibility",
                detail=eligibility,
                status_label="Pending",
                status_tone="warning",
                icon_tone="alert",
            )
        )

    fee_label = _fee_clearance_label(record)
    if fee_label.lower() in {"pending", "due", "outstanding"}:
        items.append(
            AcademicStatusPendingRequirementRead(
                title="Fee clearance",
                detail=fee_label,
                status_label="Pending",
                status_tone="warning",
                icon_tone="alert",
            )
        )

    attendance_percent = _summary_float(summary, "aggregate_attendance_percent")
    min_attendance: float | None = None
    if progression_regulation is not None and isinstance(progression_regulation.rules, dict):
        raw_min = progression_regulation.rules.get("min_attendance_percent")
        if isinstance(raw_min, (int, float)) and not isinstance(raw_min, bool):
            min_attendance = float(raw_min)
    if min_attendance is None:
        min_attendance = _summary_float(summary, "minimum_attendance_percent")
    if (
        attendance_percent is not None
        and min_attendance is not None
        and attendance_percent < min_attendance
    ):
        pct = (
            int(attendance_percent)
            if attendance_percent == int(attendance_percent)
            else round(attendance_percent, 1)
        )
        min_pct = int(min_attendance) if min_attendance == int(min_attendance) else min_attendance
        items.append(
            AcademicStatusPendingRequirementRead(
                title="Attendance",
                detail=f"Aggregate attendance is {pct}% (required {min_pct}% or above)",
                status_label="Below threshold",
                status_tone="warning",
                icon_tone="alert",
            )
        )

    if enrollment_confirmation is not None and not enrollment_confirmation.already_confirmed:
        if not enrollment_confirmation.window_open:
            detail = enrollment_confirmation.window_banner_body or enrollment_confirmation.window_banner_title
            items.append(
                AcademicStatusPendingRequirementRead(
                    title="Term enrollment confirmation",
                    detail=detail,
                    status_label="Upcoming",
                    status_tone="info",
                    icon_tone="info",
                )
            )
        elif enrollment_confirmation.confirm_blocked_reasons:
            for reason in enrollment_confirmation.confirm_blocked_reasons:
                items.append(
                    AcademicStatusPendingRequirementRead(
                        title="Enrollment confirmation",
                        detail=reason,
                        status_label="Action required",
                        status_tone="warning",
                        icon_tone="alert",
                    )
                )

    shortages = summary.get("attendance_shortages")
    if isinstance(shortages, list):
        min_attendance: float | None = None
        if progression_regulation is not None and isinstance(progression_regulation.rules, dict):
            raw_min = progression_regulation.rules.get("min_attendance_percent")
            if isinstance(raw_min, (int, float)) and not isinstance(raw_min, bool):
                min_attendance = float(raw_min)
        if min_attendance is None:
            min_attendance = _summary_float(summary, "minimum_attendance_percent")
        for entry in shortages:
            if not isinstance(entry, dict):
                continue
            course = entry.get("course_name") or entry.get("course_code")
            if not isinstance(course, str) or not course.strip():
                continue
            pct = entry.get("percent")
            if not isinstance(pct, (int, float)):
                pct = entry.get("attendance_percent")
            required = entry.get("required_percent")
            if not isinstance(required, (int, float)) and min_attendance is not None:
                required = min_attendance
            detail: str | None = None
            if isinstance(pct, (int, float)) and isinstance(required, (int, float)):
                req = int(required) if float(required) == int(required) else round(float(required), 1)
                detail = f"{_format_percent_value(float(pct))} (need {req}%)"
            action_href = entry.get("action_href")
            href = action_href.strip() if isinstance(action_href, str) and action_href.strip() else "/student/timetable/attendance"
            items.append(
                AcademicStatusPendingRequirementRead(
                    title=f"{course.strip()} attendance",
                    detail=detail,
                    status_label="Action",
                    status_tone="warning",
                    icon_tone="alert",
                    action_href=href,
                )
            )

    mandatory = summary.get("mandatory_course_requirements")
    if isinstance(mandatory, list):
        for entry in mandatory:
            row = _pending_requirement_from_summary_entry(entry)
            if row is not None:
                if row.action_href is None:
                    row = row.model_copy(update={"action_href": "/student/academics/eligibility"})
                items.append(row)

    credit_rows = summary.get("credit_by_category")
    if isinstance(credit_rows, list) and not mandatory:
        for bucket in credit_rows:
            if not isinstance(bucket, dict):
                continue
            category = bucket.get("category")
            remaining = bucket.get("remaining")
            if (
                isinstance(category, str)
                and "mandatory" in category.lower()
                and isinstance(remaining, (int, float))
                and float(remaining) > 0
            ):
                items.append(
                    AcademicStatusPendingRequirementRead(
                        title=f"Mandatory course: {category}",
                        detail="Pending",
                        status_label="Open",
                        status_tone="info",
                        icon_tone="info",
                        action_href="/student/academics/eligibility",
                    )
                )
                break

    return items


def _build_academic_status_details(
    enrollment_status: EnrollmentStatusRead,
    record: StudentAcademicRecord | None,
    academic_information: StudentAcademicInformationRead,
    enrollment_confirmation: EnrollmentConfirmationRead | None,
    progression_regulation: AcademicRegulation | None,
    *,
    active_backlog_count: int | None = None,
) -> AcademicStatusDetailsRead:
    summary = record.eligibility_summary if record is not None else {}
    attendance = _summary_float(
        summary,
        "aggregate_attendance_percent",
        "attendance_percent",
    )
    attendance_value = _format_percent_value(attendance)
    cgpa_value = "—"
    if record is not None and record.cgpa is not None:
        cgpa = record.cgpa
        cgpa_value = str(int(cgpa) if cgpa == int(cgpa) else round(cgpa, 2))

    backlog_override = _summary_int(summary, "backlogs_count", "active_backlogs_count")
    if backlog_override is not None:
        backlogs_value = str(backlog_override)
    elif active_backlog_count is not None:
        backlogs_value = str(active_backlog_count)
    elif record is not None:
        backlogs_value = "0"
    else:
        backlogs_value = "—"

    standing_fields = [
        AcademicStatusStandingFieldRead(
            label="Standing",
            value=_academic_standing_short_label(enrollment_status),
        ),
        AcademicStatusStandingFieldRead(label="CGPA", value=cgpa_value),
        AcademicStatusStandingFieldRead(label="Backlogs", value=backlogs_value),
        AcademicStatusStandingFieldRead(label="Attendance", value=attendance_value),
        AcademicStatusStandingFieldRead(
            label="Disciplinary action",
            value=_disciplinary_action_label(summary),
        ),
        AcademicStatusStandingFieldRead(
            label="Holds",
            value=_academic_holds_label(record, summary),
        ),
    ]

    subtitle = summary.get("academic_status_subtitle")
    if not isinstance(subtitle, str) or not subtitle.strip():
        subtitle = "Standing, holds and requirements"
    else:
        subtitle = subtitle.strip()

    pending_requirements = _derive_pending_requirements(
        record,
        academic_information,
        enrollment_confirmation,
        progression_regulation,
    )

    return AcademicStatusDetailsRead(
        page_subtitle=subtitle,
        standing_fields=standing_fields,
        pending_requirements=pending_requirements,
    )


async def _list_enrollment_confirmation_history(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
) -> list[EnrollmentConfirmationHistoryRowRead]:
    rows = await StudentTermEnrollmentConfirmation.find(
        {"tenant_id": tenant_id, "user_id": user_id},
    ).sort("-confirmed_at", "-created_at").limit(30).to_list()
    items: list[EnrollmentConfirmationHistoryRowRead] = []
    for row in rows:
        status = row.status.value if hasattr(row.status, "value") else str(row.status)
        items.append(
            EnrollmentConfirmationHistoryRowRead(
                id=str(row.id),
                academic_year_label=row.academic_year_label,
                semester_label=row.semester_label,
                semester_number=row.semester_number,
                study_mode=row.study_mode,
                confirmed_on_label=_format_short_date(row.confirmed_at) if row.confirmed_at else None,
                status=status.replace("_", " ").title(),
                status_tone=_confirmation_status_tone(status),
            )
        )
    return items


async def _build_enrollment_confirmation(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    profile_programme: str | None,
    current_year: str,
    current_semester: str,
    record: StudentAcademicRecord | None,
    academic_information: StudentAcademicInformationRead,
    study_mode: str | None,
    progression_regulation: AcademicRegulation | None,
) -> EnrollmentConfirmationRead:
    summary = record.eligibility_summary if record is not None else {}
    target_semester = _summary_int(summary, "enrollment_target_semester_number")
    if target_semester is None and academic_information.current_semester_number is not None:
        target_semester = academic_information.current_semester_number + 1

    target_year = summary.get("enrollment_target_academic_year_label")
    if not isinstance(target_year, str) or not target_year.strip():
        target_year = current_year
    target_sem_label = summary.get("enrollment_target_semester_label")
    if not isinstance(target_sem_label, str) or not target_sem_label.strip():
        target_sem_label = f"Semester {target_semester}" if target_semester else current_semester

    window_open = False
    window_open_at = _summary_datetime(
        summary,
        "enrollment_window_opens_at",
        "enrollment_confirmation_opens_at",
    )
    window_close_at = _summary_datetime(
        summary,
        "enrollment_window_closes_at",
        "enrollment_confirmation_closes_at",
    )
    now = datetime.now(timezone.utc)
    if window_open_at and window_close_at:
        window_open = window_open_at <= now <= window_close_at
    elif window_open_at:
        window_open = now >= window_open_at
    elif profile_programme and target_year != "N/A" and target_sem_label != "N/A":
        policy = await _registration_policy_repo.get_policy(
            tenant_id,
            profile_programme,
            target_year,
            target_sem_label,
        )
        if policy is not None:
            window_open_at = _aware_datetime(policy.registration_open_at)
            window_close_at = _aware_datetime(policy.registration_close_at)
            window_open = window_open_at <= now <= window_close_at

    existing = await StudentTermEnrollmentConfirmation.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "academic_year_label": target_year,
            "semester_label": target_sem_label,
        }
    )

    declaration_accepted = _summary_bool(
        summary,
        "student_enrollment_declaration_accepted",
        "enrollment_declaration_accepted",
    )
    fee_label = _fee_clearance_label(record)
    fee_ok = fee_label.lower() in {"cleared", "clear", "paid", "no dues"}
    eligibility_label = _enrollment_eligibility_label(record, academic_information, summary)
    eligibility_ok = bool(record is not None and record.promotion_eligible is True)
    custom_eligibility = summary.get("enrollment_eligibility_label")
    if isinstance(custom_eligibility, str):
        lower = custom_eligibility.lower()
        if "pending" in lower or "not eligible" in lower or "held" in lower:
            eligibility_ok = False
        elif "eligible" in lower:
            eligibility_ok = True

    already_confirmed = existing is not None and (
        existing.status == StudentTermEnrollmentConfirmationStatus.CONFIRMED
    )
    can_confirm = (
        window_open
        and declaration_accepted
        and fee_ok
        and eligibility_ok
        and not already_confirmed
        and target_semester is not None
    )

    blockers: list[str] = []
    if already_confirmed:
        blockers.append("This semester is already confirmed")
    elif not declaration_accepted:
        blockers.append("Turn on the declaration toggle")
    if not window_open:
        blockers.append("Enrollment window is not open yet")
    if not fee_ok:
        blockers.append("Fee clearance is required")
    if not eligibility_ok:
        blockers.append("Eligibility requirements are not met")
    if target_semester is None:
        blockers.append("Target semester is not configured")

    banner_title: str | None = None
    if window_open_at is not None:
        banner_title = f"Enrollment window opens on {_format_short_date(window_open_at)}"
        if window_open:
            banner_title = "Enrollment window is open"
    banner_body = summary.get("enrollment_window_notice")
    if not isinstance(banner_body, str) or not banner_body.strip():
        banner_body = summary.get("enrollment_confirmation_notice")
    if not isinstance(banner_body, str) or not banner_body.strip():
        prev = academic_information.current_semester_number
        if prev is not None:
            banner_body = f"You will be able to confirm after Semester {prev} results are published."
        else:
            banner_body = None
    else:
        banner_body = banner_body.strip()

    subtitle = summary.get("enrollment_confirmation_subtitle")
    if not isinstance(subtitle, str) or not subtitle.strip():
        if target_semester is not None:
            subtitle = f"Confirm your Semester {target_semester} enrollment when the window opens"
        else:
            subtitle = "Confirm your next semester enrollment when the window opens"

    return EnrollmentConfirmationRead(
        page_subtitle=subtitle,
        window_banner_title=banner_title,
        window_banner_body=banner_body,
        target_semester_number=target_semester,
        target_academic_year_label=target_year,
        target_semester_label=target_sem_label,
        eligibility_label=eligibility_label,
        fee_clearance_label=fee_label,
        attendance_condition_label=_attendance_condition_label(summary, progression_regulation),
        declaration_accepted=declaration_accepted,
        window_open=window_open,
        can_confirm=can_confirm,
        already_confirmed=already_confirmed,
        confirmed_at=existing.confirmed_at if existing is not None else None,
        confirm_blocked_reasons=blockers if not can_confirm else [],
    )


async def update_enrollment_declaration(
    scope: AccessScope,
    user: User,
    payload: EnrollmentDeclarationUpdate,
) -> EnrollmentConfirmationRead:
    authorize(scope, Permission.STUDENT_ENROLLMENT_REQUEST)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    year, semester = await _resolve_term_labels(tenant_id)
    record = await _get_academic_record(tenant_id, user.id, year, semester)
    if record is None:
        raise AppError(code="NOT_FOUND", message="Academic record not found", status_code=404)
    summary = dict(record.eligibility_summary or {})
    summary["student_enrollment_declaration_accepted"] = payload.accepted
    record.eligibility_summary = summary
    record.updated_at = utcnow()
    await record.save()
    progression_regulation = await _published_progression_regulation(tenant_id)
    academic_information = StudentAcademicInformationRead(
        current_semester_number=await _current_semester_number(tenant_id),
    )
    admission_doc = await _load_admission(tenant_id, user.id, profile)
    meta = admission_doc.metadata if admission_doc is not None else {}
    study_mode = meta.get("study_mode") if isinstance(meta.get("study_mode"), str) else None
    return await _build_enrollment_confirmation(
        tenant_id,
        user.id,
        profile.programme_code,
        year,
        semester,
        record,
        academic_information,
        study_mode,
        progression_regulation,
    )


async def confirm_term_enrollment(scope: AccessScope, user: User) -> EnrollmentConfirmResultRead:
    authorize(scope, Permission.STUDENT_ENROLLMENT_REQUEST)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    year, semester = await _resolve_term_labels(tenant_id)
    record = await _get_academic_record(tenant_id, user.id, year, semester)
    if record is None:
        raise AppError(code="NOT_FOUND", message="Academic record not found", status_code=404)
    admission_doc = await _load_admission(tenant_id, user.id, profile)
    meta = admission_doc.metadata if admission_doc is not None else {}
    study_mode = meta.get("study_mode") if isinstance(meta.get("study_mode"), str) else None
    progression_regulation = await _published_progression_regulation(tenant_id)
    academic_information = StudentAcademicInformationRead(
        current_semester_number=await _current_semester_number(tenant_id),
    )
    confirmation = await _build_enrollment_confirmation(
        tenant_id,
        user.id,
        profile.programme_code,
        year,
        semester,
        record,
        academic_information,
        study_mode,
        progression_regulation,
    )
    if not confirmation.can_confirm:
        raise AppError(
            code="ENROLLMENT_CONFIRMATION_BLOCKED",
            message="Enrollment cannot be confirmed right now",
            status_code=422,
        )
    summary = record.eligibility_summary if record is not None else {}
    target_year = confirmation.target_academic_year_label or year
    target_semester = confirmation.target_semester_label or semester
    eligibility_label = confirmation.eligibility_label
    confirmed_at = utcnow()
    existing = await StudentTermEnrollmentConfirmation.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": user.id,
            "academic_year_label": target_year,
            "semester_label": target_semester,
        }
    )
    if existing is not None:
        existing.status = StudentTermEnrollmentConfirmationStatus.CONFIRMED
        existing.confirmed_at = confirmed_at
        existing.study_mode = study_mode
        existing.eligibility_label = eligibility_label
        existing.semester_number = confirmation.target_semester_number
        existing.updated_at = utcnow()
        await existing.save()
        doc = existing
    else:
        doc = StudentTermEnrollmentConfirmation(
            tenant_id=tenant_id,
            user_id=user.id,
            academic_year_label=target_year,
            semester_label=target_semester,
            semester_number=confirmation.target_semester_number,
            study_mode=study_mode,
            status=StudentTermEnrollmentConfirmationStatus.CONFIRMED,
            eligibility_label=eligibility_label,
            confirmed_at=confirmed_at,
        )
        await doc.insert()
    summary = dict(record.eligibility_summary or {})
    summary["student_enrollment_declaration_accepted"] = False
    record.eligibility_summary = summary
    record.updated_at = utcnow()
    await record.save()
    await record_audit(
        actor_id=scope.user_id,
        action="student.enrollment_confirmation.submitted",
        resource_type="student_term_enrollment_confirmation",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=StudentActivityType.OTHER,
        title="Semester enrollment confirmed",
        description=target_semester,
    )
    status = doc.status.value if hasattr(doc.status, "value") else str(doc.status)
    return EnrollmentConfirmResultRead(
        id=str(doc.id),
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        semester_number=doc.semester_number,
        status=status,
        confirmed_at=confirmed_at,
    )


def _duration_label(years: int | None, semesters: int | None) -> str | None:
    parts: list[str] = []
    if years is not None:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if semesters is not None:
        parts.append(f"{semesters} semester{'s' if semesters != 1 else ''}")
    if not parts:
        return None
    return " · ".join(parts)


def _progression_requirement_label(rules: dict) -> str:
    if isinstance(rules.get("progression_requirement_label"), str):
        return str(rules["progression_requirement_label"])
    min_attendance = rules.get("min_attendance_percent")
    if isinstance(min_attendance, (int, float)):
        return f"{int(min_attendance)}% attendance and pass"
    if isinstance(rules.get("completed_semester_requirement"), str):
        return str(rules["completed_semester_requirement"])
    if rules.get("require_pass_all") is True:
        return "Pass all"
    return "—"


def _progression_outcome(record: StudentAcademicRecord | None, *, pending: bool = False) -> tuple[str, str]:
    if pending:
        return "Pending", "info"
    if record is None:
        return "—", "muted"
    status = record.progression_status
    raw = status.value if hasattr(status, "value") else str(status)
    upper = raw.upper()
    if upper in {"PROMOTED", "CLEARED"}:
        return "Promoted", "success"
    if upper in {"PENDING", "IN_PROGRESS"}:
        return "Pending", "info"
    if upper in {"HELD", "WITHHELD"}:
        return "Held", "warning"
    return raw.replace("_", " ").title(), "muted"


async def _build_programme_department_context(
    tenant_id: PydanticObjectId,
    profile,
    department_name: str | None,
    academic_information: StudentAcademicInformationRead,
    advisors: StudentAcademicAdvisorRead,
    meta: dict,
) -> ProgrammeDepartmentContextRead:
    institution = await _load_institution_profile(tenant_id)
    programme_doc = await _load_academic_programme(tenant_id, profile.programme_code)
    institution_dept = await _resolve_institution_department(
        tenant_id,
        department_name,
        profile.programme_code,
    )
    dept_details = await _load_department_profile_details(
        tenant_id,
        institution_dept.id if institution_dept else None,
    )

    years = academic_information.programme_duration_years
    semesters = academic_information.total_semesters
    if programme_doc is not None:
        if semesters is None:
            semesters = programme_doc.duration_semesters
    total_credits = academic_information.minimum_credits_required
    if total_credits is None and programme_doc is not None:
        total_credits = programme_doc.credits_required

    programme_name = (
        profile.programme_name
        or (programme_doc.name if programme_doc else None)
        or profile.programme_code
    )
    accreditation = None
    if institution and institution.accreditation_display:
        accreditation = institution.accreditation_display
    elif isinstance(meta.get("accreditation_label"), str):
        accreditation = meta["accreditation_label"]

    affiliation = institution.affiliation_name if institution else None
    if affiliation is None and isinstance(meta.get("affiliation_name"), str):
        affiliation = meta["affiliation_name"]

    hod_name = await _user_display_name(institution_dept.head_user_id if institution_dept else None)
    email = None
    if dept_details and dept_details.contact_email:
        email = dept_details.contact_email
    elif institution_dept and institution_dept.contact_email:
        email = institution_dept.contact_email

    office = dept_details.office_location if dept_details else None
    if not office and institution_dept and institution_dept.building_floor_label:
        office = institution_dept.building_floor_label

    phone = dept_details.contact_phone if dept_details else None

    return ProgrammeDepartmentContextRead(
        programme=StudentProgrammeDetailsRead(
            programme_name=programme_name,
            duration_label=_duration_label(years, semesters),
            total_credits=total_credits,
            affiliation_name=affiliation,
            accreditation_label=accreditation,
        ),
        department=StudentDepartmentDetailsRead(
            department_name=department_name,
            head_of_department_name=hod_name,
            class_advisor_name=advisors.class_advisor_name,
            department_email=email,
        ),
        contacts=StudentDepartmentContactsRead(
            office_location=office,
            contact_phone=phone,
        ),
    )


def _build_progression_details(
    history: list[StudentEnrollmentHistory],
    record: StudentAcademicRecord | None,
    *,
    current_semester: int | None,
    regulation: AcademicRegulation | None,
    regulation_label: str | None,
) -> AcademicProgressionDetailsRead:
    rules = regulation.rules if regulation is not None else {}
    requirement = _progression_requirement_label(rules)
    sorted_history = sorted(
        history,
        key=lambda row: (
            _semester_number_from_label(row.semester_label) or 0,
            row.closed_at,
        ),
    )
    transitions: list[ProgressionTransitionRead] = []
    for row in sorted_history:
        from_sem = row.semester_number or _semester_number_from_label(row.semester_label)
        if from_sem is None:
            continue
        to_sem = from_sem + 1
        earned = row.credits_earned
        required = row.credits_required
        credits_display = (
            f"{int(earned) if earned == int(earned) else earned} / {int(required) if required == int(required) else required}"
            if required is not None
            else str(int(earned) if earned == int(earned) else earned)
        )
        outcome, tone = _progression_outcome(None, pending=False)
        standing = row.final_standing.value if hasattr(row.final_standing, "value") else str(row.final_standing)
        if str(standing).lower() in {"good", "normal"}:
            outcome, tone = "Promoted", "success"
        transitions.append(
            ProgressionTransitionRead(
                transition_label=f"Semester {from_sem} → {to_sem}",
                credits_display=credits_display,
                requirement_label=requirement if requirement != "—" else "Pass all",
                outcome=outcome,
                outcome_tone=tone,
            )
        )

    if current_semester is not None:
        pending_outcome, pending_tone = _progression_outcome(record, pending=True)
        next_sem = current_semester + 1
        transitions.append(
            ProgressionTransitionRead(
                transition_label=f"Semester {current_semester} → {next_sem}",
                credits_display="In progress",
                requirement_label=requirement,
                outcome=pending_outcome,
                outcome_tone=pending_tone,
            )
        )

    min_attendance = rules.get("min_attendance_percent")
    attendance_percent = float(min_attendance) if isinstance(min_attendance, (int, float)) else None
    arrears_label = None
    if isinstance(rules.get("max_arrears_carried_label"), str):
        arrears_label = str(rules["max_arrears_carried_label"])
    elif regulation_label:
        arrears_label = f"Per regulation {regulation_label}"

    return AcademicProgressionDetailsRead(
        transitions=transitions,
        policy=ProgressionPolicyRead(
            minimum_attendance_percent=attendance_percent,
            arrears_rule_label=arrears_label,
            regulation_label=regulation_label,
        ),
    )


async def _resolve_term_labels(tenant_id: PydanticObjectId) -> tuple[str, str]:
    """Returns current year/semester labels, or placeholders when the college has not set a term."""
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        return "N/A", "N/A"
    return context.academic_year_label, context.semester_label


async def _get_academic_record(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    year: str,
    semester: str,
) -> StudentAcademicRecord | None:
    """Finds current academic record for user, with graceful fallback across terms."""
    if year != "N/A" and semester != "N/A":
        record = await _record_repo.get_current(tenant_id, user_id, academic_year_label=year, semester_label=semester)
        if record is not None:
            return record
    if year != "N/A":
        record = await StudentAcademicRecord.find_one(
            {"tenant_id": tenant_id, "user_id": user_id, "academic_year_label": year}
        )
        if record is not None:
            return record
    return await StudentAcademicRecord.find(
        {"tenant_id": tenant_id, "user_id": user_id}
    ).sort("-updated_at").first_or_none()


async def get_academic_details(scope: AccessScope, user: User) -> AcademicDetailsRead:
    authorize(scope, Permission.STUDENT_ACADEMIC_READ)
    tenant_id = require_student_scope(scope)
    profile = await ensure_student_profile(scope, user)
    department_name = await _department_name(tenant_id, profile.department_id)
    year, semester = await _resolve_term_labels(tenant_id)

    admission = AdmissionInfoRead(
        student_id=profile.student_id,
        roll_number=profile.roll_number,
        admission_number=profile.admission_number,
        admission_date=profile.admission_date,
        programme_code=profile.programme_code,
        programme_name=profile.programme_name,
        department_name=department_name,
        batch_label=profile.batch_label,
        section_code=profile.section_code,
    )

    record = await _get_academic_record(tenant_id, user.id, year, semester)
    enrollment_status = enrollment_status_from_record(record, year=year, semester=semester)

    department_programme = DepartmentProgrammeRead(
        department_id=str(profile.department_id) if profile.department_id else None,
        department_name=department_name,
        programme_code=profile.programme_code,
        programme_name=profile.programme_name,
        batch_label=profile.batch_label,
        section_code=profile.section_code,
    )

    current_lines: list[EnrollmentLineRead] = []
    if year != "N/A" and semester != "N/A":
        enrollments = await _enrollment_repo.list_for_term(
            tenant_id, user.id, academic_year_label=year, semester_label=semester
        )
        if not enrollments:
            enrollments = await StudentEnrollment.find(
                {
                    "tenant_id": tenant_id,
                    "user_id": user.id,
                    "academic_year_label": year,
                    "status": StudentEnrollmentStatus.ACTIVE,
                }
            ).sort("course_code").to_list()
        if not enrollments:
            enrollments = await StudentEnrollment.find(
                {
                    "tenant_id": tenant_id,
                    "user_id": user.id,
                    "status": StudentEnrollmentStatus.ACTIVE,
                }
            ).sort("course_code").to_list()

        if enrollments:
            current_lines = [enrollment_line_from_doc(row) for row in enrollments]
        else:
            roster = await _reader.roster_entries(
                tenant_id, user.id, academic_year_label=year, semester_label=semester
            )
            current_lines = [
                EnrollmentLineRead(
                    course_code=r.course_code,
                    course_name=r.course_code,
                    section_code=r.section_code,
                    status=enrollment_status.enrollment_status,
                    academic_year_label=year,
                    semester_label=semester,
                )
                for r in roster
            ]

    academic_record = None
    if record is not None:
        academic_record = AcademicEligibilityRead(
            promotion_eligible=record.promotion_eligible,
            eligibility_summary=record.eligibility_summary,
            credits_registered=record.credits_registered,
            credits_earned=record.credits_earned,
            cgpa=record.cgpa,
        )

    admission_doc = await _load_admission(tenant_id, user.id, profile)
    meta = admission_doc.metadata if admission_doc is not None else {}
    regulation = meta.get("regulation_label") if isinstance(meta.get("regulation_label"), str) else None
    if not regulation:
        regulation = await _programme_regulation(tenant_id, profile.programme_code)
    admission_type = meta.get("admission_type") if isinstance(meta.get("admission_type"), str) else None
    study_mode = meta.get("study_mode") if isinstance(meta.get("study_mode"), str) else None

    batch_source = profile.batch_label or (admission_doc.batch_label if admission_doc else None)
    admission_year: str | None = None
    if profile.admission_date is not None:
        admission_year = str(profile.admission_date.year)
    elif batch_source and len(batch_source) >= 4 and batch_source[:4].isdigit():
        admission_year = batch_source[:4]
    elif admission_doc and admission_doc.academic_year_code:
        admission_year = admission_doc.academic_year_code.split("-", 1)[0]

    summary = record.eligibility_summary if record is not None else {}
    duration_years: int | None = None
    raw_duration = meta.get("programme_duration_years")
    if isinstance(raw_duration, (int, float)) and not isinstance(raw_duration, bool):
        duration_years = int(raw_duration)

    academic_information = StudentAcademicInformationRead(
        regulation_label=regulation,
        admission_type=admission_type,
        batch_display=_batch_display_label(batch_source, meta),
        admission_year=admission_year,
        study_mode=study_mode,
        current_semester_number=await _current_semester_number(tenant_id),
        total_semesters=_programme_total_semesters(meta, summary),
        minimum_credits_required=_summary_float(
            summary,
            "minimum_credits_required",
            "credits_required",
        ),
        programme_duration_years=duration_years,
    )
    advisors = StudentAcademicAdvisorRead(
        class_advisor_name=meta.get("class_advisor_name") if isinstance(meta.get("class_advisor_name"), str) else None,
        mentor_name=meta.get("mentor_name") if isinstance(meta.get("mentor_name"), str) else None,
    )

    history_rows = await StudentEnrollmentHistory.find(
        {"tenant_id": tenant_id, "user_id": user.id},
    ).sort("semester_number", "closed_at").limit(50).to_list()
    semester_academic_history = [semester_academic_history_from_doc(row) for row in history_rows]

    programme_department_context = await _build_programme_department_context(
        tenant_id,
        profile,
        department_name,
        academic_information,
        advisors,
        meta,
    )
    progression_regulation = await _published_progression_regulation(tenant_id)
    current_semester = academic_information.current_semester_number
    academic_progression = _build_progression_details(
        history_rows,
        record,
        current_semester=current_semester,
        regulation=progression_regulation,
        regulation_label=academic_information.regulation_label,
    )
    current_semester_overview = _build_current_semester_overview(
        current_lines,
        enrollment_status,
        academic_information,
        record,
    )
    course_credit_summary = _build_course_credit_summary(record, current_lines, academic_information)
    semester_subject_terms = await _build_semester_subject_terms(
        tenant_id,
        user.id,
        year,
        semester,
        academic_information.current_semester_number,
    )
    enrollment_confirmation = await _build_enrollment_confirmation(
        tenant_id,
        user.id,
        profile.programme_code,
        year,
        semester,
        record,
        academic_information,
        study_mode,
        progression_regulation,
    )
    enrollment_confirmation_history = await _list_enrollment_confirmation_history(tenant_id, user.id)
    active_backlog_count = await _count_active_backlogs(tenant_id, user.id)
    academic_status_details = _build_academic_status_details(
        enrollment_status,
        record,
        academic_information,
        enrollment_confirmation,
        progression_regulation,
        active_backlog_count=active_backlog_count,
    )

    return AcademicDetailsRead(
        admission=admission,
        enrollment_status=enrollment_status,
        department_programme=department_programme,
        current_enrollments=current_lines,
        academic_record=academic_record,
        academic_information=academic_information,
        advisors=advisors,
        programme_department_context=programme_department_context,
        current_semester_overview=current_semester_overview,
        semester_academic_history=semester_academic_history,
        academic_progression=academic_progression,
        course_credit_summary=course_credit_summary,
        semester_subject_terms=semester_subject_terms,
        enrollment_confirmation=enrollment_confirmation,
        enrollment_confirmation_history=enrollment_confirmation_history,
        academic_status_details=academic_status_details,
    )


async def get_enrollment_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[EnrollmentHistoryRead]:
    authorize(scope, Permission.STUDENT_ENROLLMENT_READ)
    tenant_id = require_student_scope(scope)
    items, total = await _history_repo.list_for_user(
        tenant_id, user.id, skip=pagination.offset, limit=pagination.limit
    )
    return Page(
        items=[enrollment_history_from_doc(row) for row in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_enrollment_status(scope: AccessScope, user: User) -> EnrollmentStatusRead:
    authorize(scope, Permission.STUDENT_ENROLLMENT_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _resolve_term_labels(tenant_id)
    record = await _get_academic_record(tenant_id, user.id, year, semester)
    return enrollment_status_from_record(record, year=year, semester=semester)


async def get_academic_eligibility(scope: AccessScope, user: User) -> AcademicEligibilityRead:
    authorize(scope, Permission.STUDENT_ACADEMIC_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _resolve_term_labels(tenant_id)
    record = await _get_academic_record(tenant_id, user.id, year, semester)
    if record is None:
        return AcademicEligibilityRead()
    return AcademicEligibilityRead(
        promotion_eligible=record.promotion_eligible,
        eligibility_summary=record.eligibility_summary,
        credits_registered=record.credits_registered,
        credits_earned=record.credits_earned,
        cgpa=record.cgpa,
    )


async def submit_enrollment_request(scope: AccessScope, user: User, payload: EnrollmentRequestCreate) -> EnrollmentRequestRead:
    authorize(scope, Permission.STUDENT_ENROLLMENT_REQUEST)
    tenant_id = require_student_scope(scope)
    if payload.request_type not in _PERMITTED_REQUEST_TYPES:
        raise AppError(code="FORBIDDEN", message="This request type cannot be submitted by students", status_code=403)
    year, semester = await _resolve_term_labels(tenant_id)
    doc = StudentAcademicRequest(
        tenant_id=tenant_id,
        user_id=user.id,
        request_type=payload.request_type,
        academic_year_label=year,
        semester_label=semester,
        title=payload.title.strip(),
        description=payload.description.strip(),
        payload=payload.payload,
        status=StudentAcademicRequestStatus.SUBMITTED,
    )
    await doc.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.enrollment_request.submitted",
        resource_type="student_academic_request",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"request_type": payload.request_type.value},
    )
    await _activity_repo.append(
        tenant_id=tenant_id,
        user_id=user.id,
        activity_type=StudentActivityType.ENROLLMENT_REQUEST,
        title=f"Enrollment request: {payload.title}",
        description=payload.request_type.value,
    )
    return request_from_doc(doc)


async def get_enrollment_request_status(scope: AccessScope, user: User, request_id: str) -> EnrollmentRequestRead:
    authorize(scope, Permission.STUDENT_ENROLLMENT_READ)
    tenant_id = require_student_scope(scope)
    doc_id = to_object_id(request_id, "request id")
    doc = await StudentAcademicRequest.get(doc_id)
    if doc is None or str(doc.tenant_id) != str(tenant_id) or str(doc.user_id) != str(user.id):
        raise AppError(code="NOT_FOUND", message="Enrollment request not found", status_code=404)
    return request_from_doc(doc)


async def list_enrollment_requests(scope: AccessScope, user: User, pagination: Pagination) -> Page[EnrollmentRequestRead]:
    authorize(scope, Permission.STUDENT_ENROLLMENT_READ)
    tenant_id = require_student_scope(scope)
    query = StudentAcademicRequest.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-submitted_at")
    total = await query.count()
    items = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[request_from_doc(row) for row in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
