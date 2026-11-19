"""Examination cell — student eligibility evaluation."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_assessment_enums import ExamAssessmentConfigStatus
from app.modules.examinations.exam_cell_assessment_models import ExamAssessmentConfig
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_eligibility_manage,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_registration_enums import (
    ExamEligibilityRuleCode,
    ExamRegistrationSubjectType,
)
from app.modules.examinations.exam_cell_registration_models import ExamEligibilityRecord, ExamEligibilityRuleResult
from app.modules.examinations.exam_cell_registration_schemas import (
    ExamEligibilityEvaluateRequest,
    ExamEligibilityRead,
    ExamEligibilitySubjectRead,
)
from app.modules.examinations.examination_registration_models import ExaminationFeePayment, ExaminationRegistrationWindow
from app.modules.students.arrear_backlog_models import StudentArrearReference
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.examination_registration_reader import fee_verified
from app.modules.students.models import StudentAcademicRecord, StudentProfile
from app.modules.students.arrear_backlog_enums import BacklogStatus

_reader = StudentDataReader()


def _eligibility_id() -> str:
    return f"eel_{uuid4().hex[:10]}"


async def _load_session(tenant_id: PydanticObjectId, exam_session_id: PydanticObjectId) -> ExamSession:
    session = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, exam_session_id))
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    return session


async def evaluate_student_eligibility(
    scope: AccessScope,
    user: User,
    payload: ExamEligibilityEvaluateRequest,
) -> ExamEligibilityRead:
    authorize_examination_cell_eligibility_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    session_id = to_object_id(payload.exam_session_id, "exam_session_id")
    session = await _load_session(tenant_id, session_id)

    student_user = await User.get(student_id)
    if student_user is None or student_user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student not found", status_code=404)

    rules: list[tuple[ExamEligibilityRuleCode, bool, str, dict]] = []
    summary_reasons: list[str] = []

    active_ok = bool(student_user.is_active)
    rules.append((ExamEligibilityRuleCode.STUDENT_ACTIVE, active_ok, "Student account is active" if active_ok else "Student account inactive", {}))
    if not active_ok:
        summary_reasons.append("Student account is not active")

    profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": student_id})
    programme = profile.programme_code if profile else None

    record = await StudentAcademicRecord.find_one(
        {
            "tenant_id": tenant_id,
            "user_id": student_id,
            "academic_year_label": session.academic_year_label,
            "semester_label": session.semester_label,
        }
    )
    enroll_ok = record is not None and record.enrollment_status == StudentEnrollmentStatus.ACTIVE
    rules.append(
        (
            ExamEligibilityRuleCode.ENROLLMENT,
            enroll_ok,
            "Active enrollment for term" if enroll_ok else "No active enrollment for examination term",
            {},
        )
    )
    if not enroll_ok:
        summary_reasons.append("Enrollment not active for examination term")

    session_open = session.status == ExamSessionStatus.REGISTRATION_OPEN
    rules.append(
        (
            ExamEligibilityRuleCode.SESSION_OPEN,
            session_open,
            "Exam session registration is open" if session_open else f"Session status is {session.status.value}",
            {"status": session.status.value},
        )
    )
    if not session_open:
        summary_reasons.append("Registration is not open for this exam session")

    roster = await _reader.roster_entries(
        tenant_id,
        student_id,
        academic_year_label=session.academic_year_label,
        semester_label=session.semester_label,
    )
    roster_codes = {r.course_code for r in roster}
    arrear_rows = await StudentArrearReference.find(
        {"tenant_id": tenant_id, "user_id": student_id, "backlog_status": {"$ne": BacklogStatus.CLEARED.value}}
    ).to_list()
    arrear_codes = {r.course_code for r in arrear_rows if r.course_code}
    subject_reads: list[ExamEligibilitySubjectRead] = []

    config_query: dict = {
        "tenant_id": tenant_id,
        "academic_year_label": session.academic_year_label,
        "semester_label": session.semester_label,
        "status": ExamAssessmentConfigStatus.ACTIVE.value,
    }
    if programme:
        config_query["programme_code"] = programme
    assessment_config = await ExamAssessmentConfig.find_one(config_query)

    attendance_summary = await _reader.attendance_summary(
        tenant_id,
        student_id,
        academic_year_label=session.academic_year_label,
        semester_label=session.semester_label,
    )
    min_attendance = assessment_config.attendance_eligibility_percent if assessment_config and assessment_config.attendance_eligibility_percent is not None else None
    overall_pct = attendance_summary.get("overall_percentage")
    attendance_ok = True
    attendance_message = "Attendance requirement not configured"
    if min_attendance is not None:
        attendance_ok = overall_pct is not None and float(overall_pct) >= float(min_attendance)
        attendance_message = (
            f"Attendance {overall_pct}% meets minimum {min_attendance}%"
            if attendance_ok
            else f"Attendance {overall_pct}% below minimum {min_attendance}%"
        )
        if not attendance_ok:
            summary_reasons.append(attendance_message)
    rules.append(
        (
            ExamEligibilityRuleCode.ATTENDANCE,
            attendance_ok,
            attendance_message,
            {"overall_percentage": overall_pct, "minimum_required": min_attendance},
        )
    )

    window = None
    if session.season_id:
        window = await ExaminationRegistrationWindow.find_one({"tenant_id": tenant_id, "season_id": session.season_id})
    fee_code = window.fee_code if window else "exam_fee"
    payment = None
    if session.season_id:
        payment = await ExaminationFeePayment.find_one(
            {"tenant_id": tenant_id, "student_user_id": student_id, "season_id": session.season_id, "fee_code": fee_code}
        )
    fee_required = window.fee_required if window else False
    fee_ok = fee_verified(payment, fee_required=fee_required)
    rules.append(
        (
            ExamEligibilityRuleCode.FEE_CLEARANCE,
            fee_ok,
            "Examination fee verified" if fee_ok else "Examination fee not verified",
            {"fee_required": fee_required, "fee_code": fee_code},
        )
    )
    if fee_required and not fee_ok:
        summary_reasons.append("Examination fee not cleared")

    if session.examination_type == ExamSessionType.ARREAR:
        arrear_ok = bool(arrear_codes)
        rules.append(
            (
                ExamEligibilityRuleCode.ARREAR_POLICY,
                arrear_ok,
                "Arrear backlog present" if arrear_ok else "No arrear courses on record",
                {"arrear_courses": sorted(arrear_codes)},
            )
        )
        if not arrear_ok:
            summary_reasons.append("No arrear subjects eligible")
    elif session.examination_type == ExamSessionType.SUPPLEMENTARY:
        supp_ok = bool(arrear_codes)
        rules.append(
            (
                ExamEligibilityRuleCode.ARREAR_POLICY,
                supp_ok,
                "Supplementary attempt courses present" if supp_ok else "No supplementary courses",
                {},
            )
        )
    else:
        rules.append((ExamEligibilityRuleCode.ARREAR_POLICY, True, "Regular session arrear rule not applicable", {}))

    for code in sorted(roster_codes):
        subject_reads.append(
            ExamEligibilitySubjectRead(
                course_code=code,
                subject_type=ExamRegistrationSubjectType.SEMESTER,
                eligible=True,
                reasons=[],
            )
        )
    if session.examination_type in {ExamSessionType.ARREAR, ExamSessionType.SUPPLEMENTARY}:
        for code in sorted(arrear_codes - roster_codes):
            subject_reads.append(
                ExamEligibilitySubjectRead(
                    course_code=code,
                    subject_type=ExamRegistrationSubjectType.ARREAR
                    if session.examination_type == ExamSessionType.ARREAR
                    else ExamRegistrationSubjectType.SUPPLEMENTARY,
                    eligible=True,
                    reasons=[],
                )
            )

    roster_ok = bool(subject_reads)
    rules.append(
        (
            ExamEligibilityRuleCode.SUBJECT_ROSTER,
            roster_ok,
            "Subjects available for registration" if roster_ok else "No subjects on roster",
            {"course_count": len(subject_reads)},
        )
    )
    if not roster_ok:
        summary_reasons.append("No eligible subjects found")

    rules.append(
        (
            ExamEligibilityRuleCode.ASSESSMENT_CONFIG,
            assessment_config is not None,
            "Active assessment configuration present" if assessment_config else "No active assessment configuration (warning)",
            {"config_code": assessment_config.config_code if assessment_config else None},
        )
    )

    overall = all(
        passed
        for rule_code, passed, _, _ in rules
        if rule_code not in {ExamEligibilityRuleCode.ASSESSMENT_CONFIG}
    ) and roster_ok

    for subj in subject_reads:
        if not overall:
            subj.eligible = False
            subj.reasons = list(summary_reasons) or ["Not eligible"]

    existing = await ExamEligibilityRecord.find_one(
        Eq(ExamEligibilityRecord.tenant_id, tenant_id),
        Eq(ExamEligibilityRecord.student_user_id, student_id),
        Eq(ExamEligibilityRecord.exam_session_id, session_id),
    )
    eligibility_id = existing.eligibility_id if existing else _eligibility_id()
    doc = existing or ExamEligibilityRecord(
        tenant_id=tenant_id,
        eligibility_id=eligibility_id,
        exam_session_id=session_id,
        season_id=session.season_id,
        student_user_id=student_id,
    )
    doc.overall_eligible = overall
    doc.summary_reasons = summary_reasons
    doc.evaluated_at = utcnow()
    doc.published = payload.publish
    doc.actor_id = user.id
    doc.updated_at = utcnow()
    if existing:
        await doc.save()
    else:
        await doc.insert()

    await ExamEligibilityRuleResult.find({"tenant_id": tenant_id, "eligibility_id": eligibility_id}).delete()
    for rule_code, passed, message, metadata in rules:
        await ExamEligibilityRuleResult(
            tenant_id=tenant_id,
            eligibility_id=eligibility_id,
            rule_code=rule_code,
            passed=passed,
            message=message,
            metadata=metadata,
        ).insert()

    if payload.publish:
        from app.modules.examinations.exam_cell_notification_triggers import notify_eligibility_published

        await notify_eligibility_published(
            tenant_id,
            student_user_id=student_id,
            exam_session_id=session_id,
            session_name=session.name or session.session_code,
            eligibility_id=eligibility_id,
        )

    return ExamEligibilityRead(
        eligibility_id=eligibility_id,
        exam_session_id=str(session_id),
        season_id=session.season_id,
        student_user_id=str(student_id),
        overall_eligible=overall,
        summary_reasons=summary_reasons,
        subjects=subject_reads,
        evaluated_at=doc.evaluated_at,
        published=doc.published,
    )


async def get_student_eligibility(
    scope: AccessScope,
    *,
    exam_session_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
) -> ExamEligibilityRead:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamEligibilityRecord.find_one(
        Eq(ExamEligibilityRecord.tenant_id, tenant_id),
        Eq(ExamEligibilityRecord.exam_session_id, exam_session_id),
        Eq(ExamEligibilityRecord.student_user_id, student_user_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Eligibility record not found", status_code=404)
    return await _eligibility_read(tenant_id, doc)


async def _eligibility_read(tenant_id: PydanticObjectId, doc: ExamEligibilityRecord) -> ExamEligibilityRead:
    session = await ExamSession.get(doc.exam_session_id)
    student_id = doc.student_user_id
    roster = await _reader.roster_entries(
        tenant_id,
        student_id,
        academic_year_label=session.academic_year_label if session else "",
        semester_label=session.semester_label if session else "",
    )
    subjects = [
        ExamEligibilitySubjectRead(
            course_code=r.course_code,
            subject_type=ExamRegistrationSubjectType.SEMESTER,
            eligible=doc.overall_eligible,
            reasons=list(doc.summary_reasons) if not doc.overall_eligible else [],
        )
        for r in roster
    ]
    return ExamEligibilityRead(
        eligibility_id=doc.eligibility_id,
        exam_session_id=str(doc.exam_session_id),
        season_id=doc.season_id,
        student_user_id=str(doc.student_user_id),
        overall_eligible=doc.overall_eligible,
        summary_reasons=list(doc.summary_reasons),
        subjects=subjects,
        evaluated_at=doc.evaluated_at,
        published=doc.published,
    )