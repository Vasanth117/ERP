"""Examination administration services."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.examination_admin_models import (
    ExaminationApprovalRecord,
    ExaminationConfiguration,
    ExaminationEligibilityRecord,
    ExaminationMarkRecord,
    ExaminationResultPublicationRecord,
    InstitutionExaminationSchedule,
    ExaminationSessionRecord,
    HallTicketRecord,
)
from app.modules.college_admin.examination_admin_schemas import (
    EligibilityUpsert,
    ExaminationConfigRead,
    ExaminationConfigUpsert,
    ExaminationSeasonCreate,
    ExaminationSessionCreate,
    HallTicketGenerate,
    MarksBatchDecision,
    RegistrationWindowUpsert,
    ResultPublishRequest,
    ReviewWindowUpsert,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.examinations.enums import AssessmentComponentType, MarksBatchStatus
from app.modules.examinations.examination_registration_enums import (
    HallTicketPublicationStatus,
    SemesterResultPublicationStatus,
)
from app.modules.examinations.examination_registration_models import ExaminationRegistrationWindow
from app.modules.examinations.exam_review_models import ExaminationReviewWindow
from app.modules.examinations.hall_ticket_models import ExaminationHallTicket
from app.modules.examinations.models import AssessmentComponent, MarksApprovalHistory, MarksSubmissionBatch
from app.modules.examinations.result_publication_models import SemesterResultPublication, SemesterResultSubjectMark
from app.modules.examinations.semester_examination_models import (
    ExaminationCentre,
    SemesterExaminationSeason,
    SemesterExaminationSession,
    StudentExaminationEligibility,
)


async def _audit_exam(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    *,
    scope_key: str,
    resource_type: str,
    resource_id: str,
    decision: str,
    note: str | None = None,
) -> None:
    await ExaminationApprovalRecord(
        tenant_id=tenant_id,
        scope=scope_key,
        resource_type=resource_type,
        resource_id=resource_id,
        decision=decision,
        actor_id=scope.user_id,
        note=note,
    ).insert()


async def upsert_examination_config(scope: AccessScope, payload: ExaminationConfigUpsert) -> ExaminationConfigRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    existing = await ExaminationConfiguration.find_one(
        Eq(ExaminationConfiguration.tenant_id, tenant_id),
        Eq(ExaminationConfiguration.season_id, payload.season_id),
    )
    if existing:
        existing.title = payload.title
        existing.examination_type = payload.examination_type
        existing.academic_year_label = payload.academic_year_label
        existing.semester_label = payload.semester_label
        existing.component_definitions = payload.component_definitions
        existing.regulations = payload.regulations
        existing.version += 1
        existing.updated_by = scope.user_id
        existing.updated_at = utcnow()
        await existing.save()
        doc = existing
    else:
        doc = ExaminationConfiguration(
            tenant_id=tenant_id,
            season_id=payload.season_id,
            title=payload.title,
            examination_type=payload.examination_type,
            academic_year_label=payload.academic_year_label,
            semester_label=payload.semester_label,
            component_definitions=payload.component_definitions,
            regulations=payload.regulations,
            updated_by=scope.user_id,
        )
        await doc.insert()
    for comp in payload.component_definitions:
        component_id = comp.get("component_id") or f"cmp_{uuid4().hex[:8]}"
        assessment_id = comp.get("assessment_id") or f"asm_{payload.season_id}"
        existing_comp = await AssessmentComponent.find_one(
            {
                "tenant_id": tenant_id,
                "assessment_id": assessment_id,
                "component_id": component_id,
            }
        )
        if existing_comp is None:
            await AssessmentComponent(
                tenant_id=tenant_id,
                assessment_id=assessment_id,
                component_id=component_id,
                code=comp.get("code", component_id),
                name=comp.get("name", component_id),
                component_type=AssessmentComponentType(comp.get("component_type", "final_exam")),
                max_marks=float(comp.get("max_marks", 100)),
                weight_percent=float(comp.get("weight_percent", 100)),
                faculty_may_enter=bool(comp.get("faculty_may_enter", True)),
                is_official_final=bool(comp.get("is_official_final", True)),
            ).insert()
    return ExaminationConfigRead.from_document(doc)


async def create_examination_season(scope: AccessScope, payload: ExaminationSeasonCreate) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    if await SemesterExaminationSeason.find_one(
        Eq(SemesterExaminationSeason.tenant_id, tenant_id),
        Eq(SemesterExaminationSeason.season_id, payload.season_id),
    ):
        raise AppError(code="CONFLICT", message="Examination season already exists", status_code=409)
    season = SemesterExaminationSeason(
        tenant_id=tenant_id,
        season_id=payload.season_id,
        title=payload.title,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )
    await season.insert()
    return {"season_id": season.season_id}


async def create_examination_session(scope: AccessScope, payload: ExaminationSessionCreate) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.session_code.upper()
    if await ExaminationSessionRecord.find_one(
        Eq(ExaminationSessionRecord.tenant_id, tenant_id),
        Eq(ExaminationSessionRecord.season_id, payload.season_id),
        Eq(ExaminationSessionRecord.session_code, code),
    ):
        raise AppError(code="CONFLICT", message="Examination session code exists", status_code=409)
    semester_session = SemesterExaminationSession(
        tenant_id=tenant_id,
        season_id=payload.season_id,
        session_code=code,
        course_code=payload.course_code.upper(),
        course_name=payload.course_name,
        section=payload.section,
        scheduled_start=payload.scheduled_start,
        scheduled_end=payload.scheduled_end,
        centre_code=payload.centre_code,
        room=payload.room,
        published=False,
    )
    await semester_session.insert()
    admin_row = ExaminationSessionRecord(
        tenant_id=tenant_id,
        season_id=payload.season_id,
        session_code=code,
        semester_session_id=semester_session.id,
        actor_id=scope.user_id,
    )
    await admin_row.insert()
    schedule = InstitutionExaminationSchedule(
        tenant_id=tenant_id,
        season_id=payload.season_id,
        session_code=code,
        course_code=payload.course_code.upper(),
        scheduled_start=payload.scheduled_start,
        scheduled_end=payload.scheduled_end,
        centre_code=payload.centre_code,
        room=payload.room,
        semester_session_id=semester_session.id,
    )
    await schedule.insert()
    return {"session_id": str(admin_row.id), "semester_session_id": str(semester_session.id)}


async def upsert_registration_window(scope: AccessScope, payload: RegistrationWindowUpsert) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    existing = await ExaminationRegistrationWindow.find_one(
        Eq(ExaminationRegistrationWindow.tenant_id, tenant_id),
        Eq(ExaminationRegistrationWindow.season_id, payload.season_id),
    )
    if existing:
        existing.registration_open_at = payload.registration_open_at
        existing.registration_close_at = payload.registration_close_at
        existing.fee_amount = payload.fee_amount
        existing.fee_code = payload.fee_code
        existing.updated_at = utcnow()
        await existing.save()
    else:
        await ExaminationRegistrationWindow(
            tenant_id=tenant_id,
            season_id=payload.season_id,
            registration_open_at=payload.registration_open_at,
            registration_close_at=payload.registration_close_at,
            fee_amount=payload.fee_amount,
            fee_code=payload.fee_code,
        ).insert()
    return {"season_id": payload.season_id}


async def set_eligibility(scope: AccessScope, payload: EligibilityUpsert) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    auth = await StudentExaminationEligibility.find_one(
        Eq(StudentExaminationEligibility.tenant_id, tenant_id),
        Eq(StudentExaminationEligibility.student_user_id, student_id),
        Eq(StudentExaminationEligibility.season_id, payload.season_id),
    )
    if auth is None:
        auth = StudentExaminationEligibility(
            tenant_id=tenant_id,
            student_user_id=student_id,
            season_id=payload.season_id,
        )
    auth.eligible = payload.eligible
    auth.reasons = payload.reasons
    auth.published = False
    auth.updated_at = utcnow()
    if auth.id is None:
        await auth.insert()
    else:
        await auth.save()
    log = ExaminationEligibilityRecord(
        tenant_id=tenant_id,
        student_user_id=student_id,
        season_id=payload.season_id,
        eligible=payload.eligible,
        reasons=payload.reasons,
        authoritative_eligibility_id=auth.id,
        actor_id=scope.user_id,
    )
    await log.insert()
    return {"eligibility_id": str(auth.id)}


async def list_eligibility(scope: AccessScope, season_id: str, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = StudentExaminationEligibility.find(
        Eq(StudentExaminationEligibility.tenant_id, tenant_id),
        Eq(StudentExaminationEligibility.season_id, season_id),
    )
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            {
                "student_user_id": str(r.student_user_id),
                "eligible": r.eligible,
                "reasons": r.reasons,
                "published": r.published,
            }
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def generate_hall_ticket(scope: AccessScope, payload: HallTicketGenerate) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    eligibility = await StudentExaminationEligibility.find_one(
        Eq(StudentExaminationEligibility.tenant_id, tenant_id),
        Eq(StudentExaminationEligibility.student_user_id, student_id),
        Eq(StudentExaminationEligibility.season_id, payload.season_id),
    )
    if eligibility is None or not eligibility.eligible:
        raise AppError(code="FORBIDDEN", message="Student is not eligible for hall ticket", status_code=403)
    existing = await ExaminationHallTicket.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": student_id,
            "season_id": payload.season_id,
        }
    )
    ticket_number = existing.ticket_number if existing else f"HT-{uuid4().hex[:10].upper()}"
    if existing:
        ticket = existing
    else:
        ticket = ExaminationHallTicket(
            tenant_id=tenant_id,
            student_user_id=student_id,
            season_id=payload.season_id,
            ticket_number=ticket_number,
            roll_number=payload.roll_number,
            student_name=payload.student_name,
            centre_code=payload.centre_code,
        )
        await ticket.insert()
    workflow = HallTicketRecord(
        tenant_id=tenant_id,
        student_user_id=student_id,
        season_id=payload.season_id,
        hall_ticket_id=ticket.id,
        workflow_status="generated",
        actor_id=scope.user_id,
    )
    await workflow.insert()
    return {"ticket_number": ticket_number, "ticket_id": str(ticket.id), "status": ticket.status.value}


async def publish_hall_ticket(scope: AccessScope, ticket_id: str) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_PUBLISH)
    tenant_id = require_college_tenant_scope(scope)
    tid = to_object_id(ticket_id, "ticket_id")
    ticket = await ExaminationHallTicket.get(tid)
    if ticket is None or ticket.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Hall ticket not found", status_code=404)
    ticket.status = HallTicketPublicationStatus.PUBLISHED
    ticket.published_at = utcnow()
    ticket.updated_at = utcnow()
    await ticket.save()
    await _audit_exam(scope, tenant_id, scope_key="hall_ticket", resource_type="examination_hall_ticket", resource_id=str(ticket.id), decision="published")
    return {"ticket_id": str(ticket.id), "status": ticket.status.value}


async def review_marks_batch(scope: AccessScope, payload: MarksBatchDecision) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_MARKS)
    tenant_id = require_college_tenant_scope(scope)
    if payload.decision not in (MarksBatchStatus.APPROVED, MarksBatchStatus.REJECTED):
        raise AppError(code="VALIDATION_ERROR", message="Decision must be approved or rejected", status_code=422)
    batch_id = to_object_id(payload.batch_id, "batch_id")
    batch = await MarksSubmissionBatch.get(batch_id)
    if batch is None or batch.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Marks batch not found", status_code=404)
    if batch.status not in (MarksBatchStatus.SUBMITTED, MarksBatchStatus.PENDING_APPROVAL):
        raise AppError(code="CONFLICT", message="Batch is not pending review", status_code=409)
    batch.status = payload.decision
    batch.approved_at = utcnow() if payload.decision == MarksBatchStatus.APPROVED else None
    batch.updated_at = utcnow()
    await batch.save()
    await MarksApprovalHistory(
        tenant_id=tenant_id,
        batch_id=batch_id,
        action=payload.decision.value,
        actor_id=scope.user_id,
        note=payload.note,
    ).insert()
    review = await ExaminationMarkRecord.find_one(Eq(ExaminationMarkRecord.tenant_id, tenant_id), Eq(ExaminationMarkRecord.batch_id, batch_id))
    if review is None:
        review = ExaminationMarkRecord(
            tenant_id=tenant_id,
            batch_id=batch_id,
            assessment_id=batch.assessment_id,
            component_id=batch.component_id,
            course_code=batch.course_code,
            review_status=payload.decision,
            actor_id=scope.user_id,
            note=payload.note,
        )
        await review.insert()
    else:
        review.review_status = payload.decision
        review.note = payload.note
        await review.save()
    await _audit_exam(
        scope,
        tenant_id,
        scope_key="marks_review",
        resource_type="marks_submission_batch",
        resource_id=str(batch_id),
        decision=payload.decision.value,
        note=payload.note,
    )
    return {"batch_id": str(batch_id), "status": batch.status.value}


async def list_pending_marks(scope: AccessScope, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.EXAMINATION_ADMIN_MARKS)
    tenant_id = require_college_tenant_scope(scope)
    query = MarksSubmissionBatch.find(
        Eq(MarksSubmissionBatch.tenant_id, tenant_id),
        Eq(MarksSubmissionBatch.status, MarksBatchStatus.PENDING_APPROVAL),
    ).sort("-updated_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            {
                "batch_id": str(r.id),
                "course_code": r.course_code,
                "section": r.section,
                "component_id": r.component_id,
                "status": r.status.value,
            }
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def publish_results(scope: AccessScope, payload: ResultPublishRequest) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_PUBLISH)
    tenant_id = require_college_tenant_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    pub = await SemesterResultPublication.find_one(
        Eq(SemesterResultPublication.tenant_id, tenant_id),
        Eq(SemesterResultPublication.student_user_id, student_id),
        Eq(SemesterResultPublication.season_id, payload.season_id),
    )
    if pub is None:
        pub = SemesterResultPublication(
            tenant_id=tenant_id,
            student_user_id=student_id,
            season_id=payload.season_id,
            academic_year_label=payload.academic_year_label,
            semester_label=payload.semester_label,
        )
    if pub.status == SemesterResultPublicationStatus.PUBLISHED:
        raise AppError(code="CONFLICT", message="Results already published", status_code=409)
    pub.status = SemesterResultPublicationStatus.PUBLISHED
    pub.published_at = utcnow()
    pub.updated_at = utcnow()
    if pub.id is None:
        await pub.insert()
    else:
        await pub.save()
    marks = await SemesterResultSubjectMark.find(
        Eq(SemesterResultSubjectMark.tenant_id, tenant_id),
        Eq(SemesterResultSubjectMark.student_user_id, student_id),
        Eq(SemesterResultSubjectMark.season_id, payload.season_id),
    ).to_list()
    for mark in marks:
        mark.published = True
        mark.published_at = utcnow()
        await mark.save()
    log = ExaminationResultPublicationRecord(
        tenant_id=tenant_id,
        student_user_id=student_id,
        season_id=payload.season_id,
        publication_id=pub.id,
        published=True,
        actor_id=scope.user_id,
    )
    await log.insert()
    await _audit_exam(
        scope,
        tenant_id,
        scope_key="result_publication",
        resource_type="semester_result_publication",
        resource_id=str(pub.id),
        decision="published",
    )
    return {"publication_id": str(pub.id), "status": pub.status.value}


async def upsert_review_window(scope: AccessScope, payload: ReviewWindowUpsert) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    existing = await ExaminationReviewWindow.find_one(
        {
            "tenant_id": tenant_id,
            "season_id": payload.season_id,
            "review_type": payload.review_type,
        }
    )
    if existing:
        existing.application_open_at = payload.application_open_at
        existing.application_close_at = payload.application_close_at
        existing.fee_amount = payload.fee_amount
        existing.fee_code = payload.fee_code
        existing.updated_at = utcnow()
        await existing.save()
    else:
        await ExaminationReviewWindow(
            tenant_id=tenant_id,
            season_id=payload.season_id,
            review_type=payload.review_type,
            application_open_at=payload.application_open_at,
            application_close_at=payload.application_close_at,
            fee_amount=payload.fee_amount,
            fee_code=payload.fee_code,
        ).insert()
    return {"season_id": payload.season_id, "review_type": payload.review_type}


async def examination_report(scope: AccessScope, season_id: str) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    sessions = await SemesterExaminationSession.find(
        Eq(SemesterExaminationSession.tenant_id, tenant_id),
        Eq(SemesterExaminationSession.season_id, season_id),
    ).count()
    eligibility = await StudentExaminationEligibility.find(
        Eq(StudentExaminationEligibility.tenant_id, tenant_id),
        Eq(StudentExaminationEligibility.season_id, season_id),
    ).count()
    published_results = await SemesterResultPublication.find(
        Eq(SemesterResultPublication.tenant_id, tenant_id),
        Eq(SemesterResultPublication.season_id, season_id),
        Eq(SemesterResultPublication.status, SemesterResultPublicationStatus.PUBLISHED),
    ).count()
    pending_marks = await MarksSubmissionBatch.find(
        Eq(MarksSubmissionBatch.tenant_id, tenant_id),
        Eq(MarksSubmissionBatch.status, MarksBatchStatus.PENDING_APPROVAL),
    ).count()
    return {
        "season_id": season_id,
        "session_count": sessions,
        "eligibility_records": eligibility,
        "published_results": published_results,
        "pending_marks_batches": pending_marks,
    }


async def upsert_examination_centre(scope: AccessScope, centre_code: str, name: str) -> dict:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    code = centre_code.upper()
    doc = await ExaminationCentre.find_one(Eq(ExaminationCentre.tenant_id, tenant_id), Eq(ExaminationCentre.centre_code, code))
    if doc is None:
        doc = ExaminationCentre(tenant_id=tenant_id, centre_code=code, name=name)
        await doc.insert()
    else:
        doc.name = name
        doc.updated_at = utcnow()
        await doc.save()
    return {"centre_code": code}
