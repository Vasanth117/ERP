"""Training programs, enrollment, attendance, assessment and certification."""

from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.hr.enums import (
    HrTrainingAttendanceStatus,
    HrTrainingEnrollmentStatus,
    HrTrainingProgramStatus,
)
from app.modules.hr.policy import (
    authorize_hr_training_manage,
    authorize_hr_training_read,
    require_employee_tenant_scope,
    require_hr_tenant_scope,
)
from app.modules.hr.training_models import (
    EmployeeTrainingHistory,
    HrTrainingAssessment,
    HrTrainingAttendance,
    HrTrainingEnrollment,
    HrTrainingProgram,
)
from app.modules.hr.training_schemas import (
    TrainingAssessmentSubmit,
    TrainingAttendanceUpsert,
    TrainingEnrollmentCreate,
    TrainingEnrollmentRead,
    TrainingEnrollmentReview,
    TrainingProgramRead,
    TrainingProgramUpsert,
)


async def upsert_training_program(scope: AccessScope, payload: TrainingProgramUpsert) -> TrainingProgramRead:
    authorize_hr_training_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrTrainingProgram.find_one(
        Eq(HrTrainingProgram.tenant_id, tenant_id),
        Eq(HrTrainingProgram.program_code, payload.program_code),
    )
    data = payload.model_dump()
    if doc:
        for k, v in data.items():
            setattr(doc, k, v)
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrTrainingProgram(tenant_id=tenant_id, actor_id=scope.user_id, **data)
        await doc.insert()
    return TrainingProgramRead.from_doc(doc)


async def list_training_programs(scope: AccessScope) -> list[TrainingProgramRead]:
    authorize_hr_training_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrTrainingProgram.find(Eq(HrTrainingProgram.tenant_id, tenant_id)).to_list()
    return [TrainingProgramRead.from_doc(r) for r in rows]


async def create_training_enrollment(scope: AccessScope, payload: TrainingEnrollmentCreate, *, self_service: bool) -> TrainingEnrollmentRead:
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    if self_service:
        if scope.user_id != uid:
            raise AppError(code="FORBIDDEN", message="Cannot enroll another employee", status_code=403)
        tenant_id = require_employee_tenant_scope(scope)
    else:
        authorize_hr_training_manage(scope)
        tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(payload.training_program_id, "training_program_id")
    program = await HrTrainingProgram.get(pid)
    if program is None or program.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Training program not found", status_code=404)
    if program.status not in {HrTrainingProgramStatus.OPEN, HrTrainingProgramStatus.IN_PROGRESS}:
        raise AppError(code="CONFLICT", message="Program not open for enrollment", status_code=409)
    existing = await HrTrainingEnrollment.find_one(
        Eq(HrTrainingEnrollment.tenant_id, tenant_id),
        Eq(HrTrainingEnrollment.training_program_id, program.id),
        Eq(HrTrainingEnrollment.employee_user_id, uid),
    )
    if existing and existing.status not in {HrTrainingEnrollmentStatus.CANCELLED, HrTrainingEnrollmentStatus.WITHDRAWN}:
        raise AppError(code="CONFLICT", message="Already enrolled", status_code=409)
    confirmed_count = await HrTrainingEnrollment.find(
        Eq(HrTrainingEnrollment.tenant_id, tenant_id),
        Eq(HrTrainingEnrollment.training_program_id, program.id),
        Eq(HrTrainingEnrollment.status, HrTrainingEnrollmentStatus.CONFIRMED),
    ).count()
    status = HrTrainingEnrollmentStatus.PENDING_APPROVAL
    waitlist = None
    if program.capacity > 0 and confirmed_count >= program.capacity:
        status = HrTrainingEnrollmentStatus.WAITLISTED
        waitlist = confirmed_count - program.capacity + 1
    row = HrTrainingEnrollment(
        tenant_id=tenant_id,
        training_program_id=program.id,
        program_code=program.program_code,
        employee_user_id=uid,
        enrollment_source=payload.enrollment_source,
        nominator_user_id=scope.user_id if not self_service else None,
        status=status,
        waitlist_position=waitlist,
        actor_id=scope.user_id,
    )
    await row.insert()
    return TrainingEnrollmentRead.from_doc(row)


async def review_training_enrollment(scope: AccessScope, enrollment_id: str, payload: TrainingEnrollmentReview) -> TrainingEnrollmentRead:
    authorize_hr_training_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    eid = to_object_id(enrollment_id, "enrollment_id")
    row = await HrTrainingEnrollment.get(eid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Enrollment not found", status_code=404)
    if payload.action == "confirm":
        program = await HrTrainingProgram.get(row.training_program_id)
        if program and program.capacity > 0:
            count = await HrTrainingEnrollment.find(
                Eq(HrTrainingEnrollment.tenant_id, tenant_id),
                Eq(HrTrainingEnrollment.training_program_id, row.training_program_id),
                Eq(HrTrainingEnrollment.status, HrTrainingEnrollmentStatus.CONFIRMED),
            ).count()
            if count >= program.capacity:
                raise AppError(code="CONFLICT", message="Capacity reached", status_code=409)
        row.status = HrTrainingEnrollmentStatus.CONFIRMED
    elif payload.action == "waitlist":
        row.status = HrTrainingEnrollmentStatus.WAITLISTED
    elif payload.action == "reject":
        row.status = HrTrainingEnrollmentStatus.CANCELLED
    else:
        row.status = HrTrainingEnrollmentStatus.CANCELLED
    row.updated_at = utcnow()
    await row.save()
    return TrainingEnrollmentRead.from_doc(row)


async def record_training_attendance(
    scope: AccessScope,
    enrollment_id: str,
    payload: TrainingAttendanceUpsert,
    *,
    self_service: bool,
) -> dict:
    eid = to_object_id(enrollment_id, "enrollment_id")
    row = await HrTrainingEnrollment.get(eid)
    if row is None:
        raise AppError(code="NOT_FOUND", message="Enrollment not found", status_code=404)
    if self_service:
        if scope.user_id != row.employee_user_id:
            raise AppError(code="FORBIDDEN", message="Attendance access denied", status_code=403)
        require_employee_tenant_scope(scope)
    else:
        authorize_hr_training_manage(scope)
        require_hr_tenant_scope(scope)
    status = HrTrainingAttendanceStatus.PRESENT if payload.status == "present" else HrTrainingAttendanceStatus.ABSENT
    if payload.status == "partial":
        status = HrTrainingAttendanceStatus.PARTIAL
    existing = await HrTrainingAttendance.find_one(
        Eq(HrTrainingAttendance.tenant_id, row.tenant_id),
        Eq(HrTrainingAttendance.enrollment_id, row.id),
        Eq(HrTrainingAttendance.session_code, payload.session_code),
    )
    if existing:
        existing.status = status
        existing.attended_minutes = payload.attended_minutes
        existing.session_date = payload.session_date
        await existing.save()
    else:
        await HrTrainingAttendance(
            tenant_id=row.tenant_id,
            enrollment_id=row.id,
            training_program_id=row.training_program_id,
            employee_user_id=row.employee_user_id,
            session_code=payload.session_code,
            session_date=payload.session_date,
            status=status,
            attended_minutes=payload.attended_minutes,
            actor_id=scope.user_id,
        ).insert()
    return {"recorded": True}


async def submit_training_assessment(scope: AccessScope, enrollment_id: str, payload: TrainingAssessmentSubmit) -> dict:
    authorize_hr_training_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    eid = to_object_id(enrollment_id, "enrollment_id")
    row = await HrTrainingEnrollment.get(eid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Enrollment not found", status_code=404)
    attempt = await HrTrainingAssessment.find(Eq(HrTrainingAssessment.tenant_id, tenant_id), Eq(HrTrainingAssessment.enrollment_id, row.id)).count() + 1
    passed = float(payload.score) >= float((payload.max_score or payload.score))
    program = await HrTrainingProgram.get(row.training_program_id)
    criteria = (program.completion_criteria or {}) if program else {}
    min_score = float(criteria.get("min_score", payload.max_score))
    passed = float(payload.score) >= min_score
    await HrTrainingAssessment(
        tenant_id=tenant_id,
        enrollment_id=row.id,
        employee_user_id=row.employee_user_id,
        attempt_number=attempt,
        score=payload.score,
        max_score=payload.max_score,
        passed=passed,
        feedback=payload.feedback,
        actor_id=scope.user_id,
    ).insert()
    return {"attempt": attempt, "passed": passed}


async def complete_training_enrollment(scope: AccessScope, enrollment_id: str) -> dict:
    authorize_hr_training_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    eid = to_object_id(enrollment_id, "enrollment_id")
    row = await HrTrainingEnrollment.get(eid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Enrollment not found", status_code=404)
    program = await HrTrainingProgram.get(row.training_program_id)
    if program is None:
        raise AppError(code="NOT_FOUND", message="Program not found", status_code=404)
    criteria = program.completion_criteria or {}
    min_sessions = int(criteria.get("min_sessions_present", 0))
    if min_sessions > 0:
        present = await HrTrainingAttendance.find(
            Eq(HrTrainingAttendance.tenant_id, tenant_id),
            Eq(HrTrainingAttendance.enrollment_id, row.id),
            Eq(HrTrainingAttendance.status, HrTrainingAttendanceStatus.PRESENT),
        ).count()
        if present < min_sessions:
            raise AppError(code="VALIDATION_ERROR", message="Attendance criteria not met", status_code=422)
    if criteria.get("requires_passing_assessment", True):
        passed = await HrTrainingAssessment.find_one(
            Eq(HrTrainingAssessment.tenant_id, tenant_id),
            Eq(HrTrainingAssessment.enrollment_id, row.id),
            Eq(HrTrainingAssessment.passed, True),
        )
        if passed is None:
            raise AppError(code="VALIDATION_ERROR", message="Passing assessment required", status_code=422)
    row.status = HrTrainingEnrollmentStatus.COMPLETED
    row.completed_at = utcnow()
    row.certificate_issued = True
    row.certificate_code = f"CERT-{uuid4().hex[:10].upper()}"
    row.updated_at = utcnow()
    await row.save()
    await EmployeeTrainingHistory(
        tenant_id=tenant_id,
        employee_user_id=row.employee_user_id,
        training_program_id=row.training_program_id,
        enrollment_id=row.id,
        program_code=row.program_code,
        title=program.title,
        completed=True,
        certificate_code=row.certificate_code,
        completed_at=row.completed_at,
        summary={"duration_hours": program.duration_hours},
    ).insert()
    return {"completed": True, "certificate_code": row.certificate_code}