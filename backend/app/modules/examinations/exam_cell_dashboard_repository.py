"""MongoDB aggregations for the examination cell dashboard."""

from beanie import PydanticObjectId

from app.modules.department_admin.models import DepartmentExaminationCoordinationIssue, DepartmentExaminationIssueStatus
from app.modules.examinations.enums import ExaminationEligibilityStatus, MarksBatchStatus
from app.modules.examinations.exam_cell_dashboard_filters import ExamDashboardContext
from app.modules.examinations.exam_cell_dashboard_schemas import (
    ExamActivityItem,
    ExamDepartmentStatRow,
    ExamHallTicketSummary,
    ExamIncidentSummary,
    ExamMarksSummary,
    ExamRegistrationSummary,
    ExamResultsSummary,
    ExamSessionCountSummary,
    ExamSessionStatRow,
    ExamSupplementaryRevaluationSummary,
    ExamTimetableItem,
)
from app.modules.examinations.exam_cell_enums import ExamSessionStatus
from app.modules.examinations.exam_cell_models import ExamActivityLog, ExamSession, ExamSessionAcademicScope
from app.modules.examinations.examination_registration_enums import HallTicketPublicationStatus, SemesterResultPublicationStatus
from app.modules.examinations.hall_ticket_models import ExaminationHallTicket
from app.modules.examinations.models import Assessment, MarksSubmissionBatch
from app.modules.examinations.result_publication_models import SemesterResultPublication
from app.modules.examinations.semester_examination_models import SemesterExaminationSession, StudentExaminationEligibility
from app.modules.examinations.arrear_examination_models import SupplementaryExaminationSeason
from app.modules.examinations.exam_review_models import ExaminationReviewFeePayment, ExaminationReviewWindow
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus
from app.modules.students.examination_registration_enums import StudentExamRegistrationStatus
from app.modules.students.examination_registration_models import StudentExamRegistration


def _season_match(ctx: ExamDashboardContext) -> dict:
    if not ctx.season_ids:
        return {}
    return {"season_id": {"$in": list(ctx.season_ids)}}


class ExamCellDashboardRepository:
    async def session_counts(self, ctx: ExamDashboardContext) -> ExamSessionCountSummary:
        base: dict = {"tenant_id": ctx.tenant_id}
        if ctx.academic_year_label:
            base["academic_year_label"] = ctx.academic_year_label
        if ctx.semester_label:
            base["semester_label"] = ctx.semester_label
        if ctx.examination_type:
            base["examination_type"] = ctx.examination_type.value
        if ctx.examination_status:
            base["status"] = ctx.examination_status.value
        if ctx.exam_session_id:
            base["_id"] = ctx.exam_session_id

        total = await ExamSession.find(base).count()
        now = ctx.now
        upcoming = await ExamSession.find(
            {
                **base,
                "examination_start_at": {"$gt": now},
                "status": {
                    "$in": [
                        ExamSessionStatus.SCHEDULED.value,
                        ExamSessionStatus.REGISTRATION_OPEN.value,
                        ExamSessionStatus.REGISTRATION_CLOSED.value,
                    ]
                },
            }
        ).count()
        ongoing = await ExamSession.find(
            {
                **base,
                "status": ExamSessionStatus.ONGOING.value,
            }
        ).count()
        if ongoing == 0:
            ongoing = await ExamSession.find(
                {
                    **base,
                    "examination_start_at": {"$lte": now},
                    "examination_end_at": {"$gte": now},
                    "status": {"$nin": [ExamSessionStatus.CANCELLED.value, ExamSessionStatus.ARCHIVED.value]},
                }
            ).count()
        completed = await ExamSession.find(
            {
                **base,
                "status": {
                    "$in": [
                        ExamSessionStatus.COMPLETED.value,
                        ExamSessionStatus.RESULTS_PROCESSING.value,
                        ExamSessionStatus.PUBLISHED.value,
                    ]
                },
            }
        ).count()
        return ExamSessionCountSummary(total=total, upcoming=upcoming, ongoing=ongoing, completed=completed)

    async def registration_summary(self, ctx: ExamDashboardContext) -> ExamRegistrationSummary:
        if not ctx.season_ids:
            return ExamRegistrationSummary(
                total_registered_candidates=0,
                pending_registrations=0,
                pending_eligibility_checks=0,
            )
        reg_match: dict = {"tenant_id": ctx.tenant_id, **_season_match(ctx)}
        registered = await StudentExamRegistration.find(
            {
                **reg_match,
                "status": {
                    "$in": [
                        StudentExamRegistrationStatus.CONFIRMED.value,
                        StudentExamRegistrationStatus.SUBMITTED.value,
                    ]
                },
            }
        ).count()
        pending_regs = await StudentExamRegistration.find(
            {
                **reg_match,
                "status": {
                    "$in": [
                        StudentExamRegistrationStatus.DRAFT.value,
                        StudentExamRegistrationStatus.SUBMITTED.value,
                    ]
                },
            }
        ).count()
        pending_eligibility = await StudentExaminationEligibility.find(
            {
                "tenant_id": ctx.tenant_id,
                **_season_match(ctx),
                "status": ExaminationEligibilityStatus.PENDING_REVIEW.value,
            }
        ).count()
        return ExamRegistrationSummary(
            total_registered_candidates=registered,
            pending_registrations=pending_regs,
            pending_eligibility_checks=pending_eligibility,
        )

    async def hall_ticket_summary(self, ctx: ExamDashboardContext) -> ExamHallTicketSummary:
        if not ctx.season_ids:
            return ExamHallTicketSummary(generated=0, pending=0)
        match: dict = {"tenant_id": ctx.tenant_id, **_season_match(ctx)}
        generated = await ExaminationHallTicket.find(
            {**match, "status": HallTicketPublicationStatus.PUBLISHED.value}
        ).count()
        pending = await ExaminationHallTicket.find(
            {
                **match,
                "status": {"$in": [HallTicketPublicationStatus.DRAFT.value]},
            }
        ).count()
        return ExamHallTicketSummary(generated=generated, pending=pending)

    async def marks_summary(self, ctx: ExamDashboardContext) -> ExamMarksSummary:
        assessment_match: dict = {"tenant_id": ctx.tenant_id}
        if ctx.academic_year_label:
            assessment_match["academic_year_label"] = ctx.academic_year_label
        if ctx.semester_label:
            assessment_match["semester_label"] = ctx.semester_label
        if ctx.course_code:
            assessment_match["course_code"] = ctx.course_code
        assessments_total = await Assessment.find(assessment_match).count()

        batch_match: dict = {"tenant_id": ctx.tenant_id}
        if ctx.course_code:
            batch_match["course_code"] = ctx.course_code
        pending_submission = await MarksSubmissionBatch.find(
            {
                **batch_match,
                "status": {"$in": [MarksBatchStatus.DRAFT.value, MarksBatchStatus.SUBMITTED.value]},
            }
        ).count()
        pending_approval = await MarksSubmissionBatch.find(
            {**batch_match, "status": MarksBatchStatus.PENDING_APPROVAL.value}
        ).count()
        completed = await MarksSubmissionBatch.find(
            {**batch_match, "status": MarksBatchStatus.APPROVED.value}
        ).count()
        return ExamMarksSummary(
            assessments_total=assessments_total,
            marks_batches_pending_submission=pending_submission,
            marks_batches_pending_approval=pending_approval,
            marks_entry_completed=completed,
        )

    async def results_summary(self, ctx: ExamDashboardContext) -> ExamResultsSummary:
        if not ctx.season_ids:
            return ExamResultsSummary(awaiting_review=0, awaiting_publication=0)
        match = {"tenant_id": ctx.tenant_id, **_season_match(ctx)}
        awaiting_review = await SemesterResultPublication.find(
            {**match, "status": SemesterResultPublicationStatus.PROCESSING.value, "published_at": None}
        ).count()
        awaiting_publication = await SemesterResultPublication.find(
            {
                **match,
                "status": SemesterResultPublicationStatus.PROCESSING.value,
            }
        ).count()
        return ExamResultsSummary(
            awaiting_review=awaiting_review,
            awaiting_publication=awaiting_publication,
        )

    async def supplementary_revaluation_summary(self, ctx: ExamDashboardContext) -> ExamSupplementaryRevaluationSummary:
        supp_match: dict = {"tenant_id": ctx.tenant_id}
        if ctx.academic_year_label:
            supp_match["academic_year_label"] = ctx.academic_year_label
        if ctx.semester_label:
            supp_match["semester_label"] = ctx.semester_label
        supplementary = await SupplementaryExaminationSeason.find(supp_match).count()

        review_match: dict = {"tenant_id": ctx.tenant_id, "published": True}
        if ctx.season_ids:
            review_match["season_id"] = {"$in": list(ctx.season_ids)}
        windows = await ExaminationReviewWindow.find(review_match).count()
        pending_fees = await ExaminationReviewFeePayment.find(
            {
                "tenant_id": ctx.tenant_id,
                "status": ExaminationFeePaymentStatus.PENDING.value,
            }
        ).count()
        return ExamSupplementaryRevaluationSummary(
            revaluation_windows_open=windows,
            supplementary_seasons=supplementary,
            pending_review_fee_payments=pending_fees,
        )

    async def incident_summary(self, ctx: ExamDashboardContext) -> ExamIncidentSummary:
        match: dict = {
            "tenant_id": ctx.tenant_id,
            "status": {
                "$in": [
                    DepartmentExaminationIssueStatus.OPEN.value,
                    DepartmentExaminationIssueStatus.IN_PROGRESS.value,
                ]
            },
        }
        open_issues = await DepartmentExaminationCoordinationIssue.find(match).count()
        malpractice = await DepartmentExaminationCoordinationIssue.find(
            {
                **match,
                "issue_type": {"$regex": "malpractice", "$options": "i"},
            }
        ).count()
        return ExamIncidentSummary(
            open_coordination_issues=open_issues,
            malpractice_related_issues=malpractice,
        )

    async def upcoming_timetable(self, ctx: ExamDashboardContext, limit: int = 10) -> list[ExamTimetableItem]:
        if not ctx.season_ids:
            return []
        query: dict = {
            "tenant_id": ctx.tenant_id,
            "season_id": {"$in": list(ctx.season_ids)},
            "scheduled_start": {"$gte": ctx.now},
            "published": True,
        }
        if ctx.course_code:
            query["course_code"] = ctx.course_code
        rows = await SemesterExaminationSession.find(query).sort("+scheduled_start").limit(limit).to_list()
        return [
            ExamTimetableItem(
                session_code=r.session_code,
                course_code=r.course_code,
                scheduled_start=r.scheduled_start,
                centre_code=r.centre_code,
                room=r.room,
                season_id=r.season_id,
            )
            for r in rows
        ]

    async def recent_activities(self, ctx: ExamDashboardContext, limit: int = 15) -> list[ExamActivityItem]:
        query: dict = {"tenant_id": ctx.tenant_id}
        if ctx.exam_session_id:
            query["exam_session_id"] = ctx.exam_session_id
        elif ctx.season_ids:
            query["season_id"] = {"$in": list(ctx.season_ids)}
        rows = await ExamActivityLog.find(query).sort("-created_at").limit(limit).to_list()
        return [
            ExamActivityItem(
                event_id=r.event_id,
                action=r.action,
                summary=r.summary,
                exam_session_id=str(r.exam_session_id) if r.exam_session_id else None,
                actor_id=str(r.actor_id) if r.actor_id else None,
                created_at=r.created_at,
            )
            for r in rows
        ]

    async def session_statistics(self, ctx: ExamDashboardContext) -> list[ExamSessionStatRow]:
        base: dict = {"tenant_id": ctx.tenant_id}
        if ctx.academic_year_label:
            base["academic_year_label"] = ctx.academic_year_label
        if ctx.semester_label:
            base["semester_label"] = ctx.semester_label
        sessions = await ExamSession.find(base).sort("+session_code").to_list()
        rows: list[ExamSessionStatRow] = []
        for session in sessions:
            season_id = session.season_id
            registered = 0
            pending_eligibility = 0
            hall_published = 0
            if season_id:
                registered = await StudentExamRegistration.find(
                    {
                        "tenant_id": ctx.tenant_id,
                        "season_id": season_id,
                        "status": {
                            "$in": [
                                StudentExamRegistrationStatus.CONFIRMED.value,
                                StudentExamRegistrationStatus.SUBMITTED.value,
                            ]
                        },
                    }
                ).count()
                pending_eligibility = await StudentExaminationEligibility.find(
                    {
                        "tenant_id": ctx.tenant_id,
                        "season_id": season_id,
                        "status": ExaminationEligibilityStatus.PENDING_REVIEW.value,
                    }
                ).count()
                hall_published = await ExaminationHallTicket.find(
                    {
                        "tenant_id": ctx.tenant_id,
                        "season_id": season_id,
                        "status": HallTicketPublicationStatus.PUBLISHED.value,
                    }
                ).count()
            rows.append(
                ExamSessionStatRow(
                    session_code=session.session_code,
                    session_id=session.session_id,
                    name=session.name,
                    status=session.status,
                    registered_candidates=registered,
                    pending_eligibility=pending_eligibility,
                    hall_tickets_published=hall_published,
                )
            )
        return rows

    async def department_statistics(self, ctx: ExamDashboardContext) -> list[ExamDepartmentStatRow]:
        scopes = await ExamSessionAcademicScope.find({"tenant_id": ctx.tenant_id}).to_list()
        by_dept: dict[str, dict[str, int]] = {}
        session_ids_by_dept: dict[str, set[PydanticObjectId]] = {}
        for scope in scopes:
            session = await ExamSession.get(scope.exam_session_id)
            if session is None:
                continue
            if ctx.academic_year_label and session.academic_year_label != ctx.academic_year_label:
                continue
            if ctx.semester_label and session.semester_label != ctx.semester_label:
                continue
            depts = scope.department_codes or ["INSTITUTION"]
            for dept in depts:
                session_ids_by_dept.setdefault(dept, set()).add(session.id)
                by_dept.setdefault(dept, {"exam_sessions": 0, "registered": 0, "pending_regs": 0})
                by_dept[dept]["exam_sessions"] += 1
                if session.season_id:
                    by_dept[dept]["registered"] += await StudentExamRegistration.find(
                        {
                            "tenant_id": ctx.tenant_id,
                            "season_id": session.season_id,
                            "status": StudentExamRegistrationStatus.CONFIRMED.value,
                        }
                    ).count()
                    by_dept[dept]["pending_regs"] += await StudentExamRegistration.find(
                        {
                            "tenant_id": ctx.tenant_id,
                            "season_id": session.season_id,
                            "status": {
                                "$in": [
                                    StudentExamRegistrationStatus.DRAFT.value,
                                    StudentExamRegistrationStatus.SUBMITTED.value,
                                ]
                            },
                        }
                    ).count()
        if ctx.department_code:
            by_dept = {k: v for k, v in by_dept.items() if k == ctx.department_code}
        return [
            ExamDepartmentStatRow(
                department_code=code,
                exam_sessions=stats["exam_sessions"],
                registered_candidates=stats["registered"],
                pending_registrations=stats["pending_regs"],
            )
            for code, stats in sorted(by_dept.items())
        ]