"""Examination report data aggregation."""

from collections import Counter, defaultdict

from beanie.odm.operators.find.comparison import Eq, In

from app.common.time import as_utc_aware
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultOutcome
from app.modules.examinations.exam_cell_grading_models import ExamGpaCalculation, ExamStudentSubjectResult
from app.modules.examinations.exam_cell_hall_ticket_models import ExamHallTicket
from app.modules.examinations.exam_cell_registration_enums import ExamHallTicketStatus
from app.modules.examinations.exam_cell_incident_models import ExamIncidentRecord, ExamMalpracticeCase
from app.modules.examinations.exam_cell_marks_enums import ExamMarksSubmissionStatus
from app.modules.examinations.exam_cell_marks_models import ExamMarksSubmission
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_publication_enums import ExamPublicationStatus
from app.modules.examinations.exam_cell_publication_models import ExamResultPublication
from app.modules.examinations.exam_cell_registration_models import ExamEligibilityRecord, ExamRegistration, ExamRegistrationSubject
from app.modules.examinations.exam_cell_report_filters import ExamReportContext
from app.modules.examinations.exam_cell_revaluation_models import ExamRevaluationApplication
from app.modules.examinations.exam_cell_revaluation_models import ExamSupplementaryRegistration
from app.modules.students.arrear_backlog_enums import BacklogStatus
from app.modules.students.arrear_backlog_models import StudentArrearReference
from app.modules.students.models import StudentProfile


class ExamReportRepository:
    def _session_filter(self, ctx: ExamReportContext) -> dict:
        if not ctx.session_ids:
            return {"tenant_id": ctx.tenant_id, "exam_session_id": {"$in": []}}
        return {"tenant_id": ctx.tenant_id, "exam_session_id": {"$in": list(ctx.session_ids)}}

    async def build(self, ctx: ExamReportContext, report_type: str) -> tuple[list[dict], dict]:
        builder = {
            "session_summary": self._session_summary,
            "registration_statistics": self._registration_statistics,
            "eligibility_statistics": self._eligibility_statistics,
            "subject_candidate_counts": self._subject_candidate_counts,
            "hall_ticket_statistics": self._hall_ticket_statistics,
            "marks_entry_completion": self._marks_entry_completion,
            "pass_fail_by_subject": self._pass_fail_by_subject,
            "grade_distribution": self._grade_distribution,
            "gpa_distribution": self._gpa_distribution,
            "publication_status": self._publication_status,
            "arrear_supplementary": self._arrear_supplementary,
            "revaluation_statistics": self._revaluation_statistics,
            "incident_summary": self._incident_summary,
            "department_performance": self._department_performance,
            "processing_turnaround": self._processing_turnaround,
        }.get(report_type)
        if builder is None:
            return [], {}
        return await builder(ctx)

    async def _session_summary(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        rows = await ExamSession.find({"tenant_id": ctx.tenant_id, "_id": {"$in": list(ctx.session_ids)}}).to_list()
        by_status: Counter[str] = Counter()
        by_type: Counter[str] = Counter()
        for s in rows:
            by_status[s.status.value] += 1
            by_type[s.examination_type.value] += 1
        data = [
            {"status": k, "count": v} for k, v in sorted(by_status.items())
        ] + [{"examination_type": k, "count": v} for k, v in sorted(by_type.items())]
        return data, {"session_count": len(rows)}

    async def _registration_statistics(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        base = self._session_filter(ctx)
        regs = await ExamRegistration.find(base).to_list()
        by_status: Counter[str] = Counter(r.status.value for r in regs)
        rows = [{"status": k, "count": v} for k, v in sorted(by_status.items())]
        return rows, {"registration_count": len(regs)}

    async def _eligibility_statistics(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        base = self._session_filter(ctx)
        records = await ExamEligibilityRecord.find(base).to_list()
        eligible = sum(1 for r in records if r.overall_eligible)
        ineligible = len(records) - eligible
        return [
            {"bucket": "eligible", "count": eligible},
            {"bucket": "ineligible", "count": ineligible},
        ], {"evaluated_students": len(records)}

    async def _subject_candidate_counts(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        base = self._session_filter(ctx)
        subjects = await ExamRegistrationSubject.find(base).to_list()
        if ctx.filters.course_code:
            subjects = [s for s in subjects if s.course_code.upper() == ctx.filters.course_code.upper()]
        counts: Counter[str] = Counter(s.course_code.upper() for s in subjects)
        rows = [{"course_code": k, "candidate_count": v} for k, v in sorted(counts.items())]
        return rows, {"subject_rows": len(rows)}

    async def _hall_ticket_statistics(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        base = self._session_filter(ctx)
        tickets = await ExamHallTicket.find(base).to_list()
        published = sum(1 for t in tickets if t.status == ExamHallTicketStatus.PUBLISHED)
        return [
            {"bucket": "published", "count": published},
            {"bucket": "draft", "count": len(tickets) - published},
        ], {"ticket_count": len(tickets)}

    async def _marks_entry_completion(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        base = self._session_filter(ctx)
        subs = await ExamMarksSubmission.find(base).to_list()
        approved = sum(1 for s in subs if s.status == ExamMarksSubmissionStatus.APPROVED)
        return [
            {"status": ExamMarksSubmissionStatus.APPROVED.value, "count": approved},
            {"status": "other", "count": len(subs) - approved},
        ], {"submission_count": len(subs)}

    async def _pass_fail_by_subject(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        base = self._session_filter(ctx)
        results = await ExamStudentSubjectResult.find(base).to_list()
        if ctx.filters.course_code:
            results = [r for r in results if r.course_code.upper() == ctx.filters.course_code.upper()]
        grouped: dict[str, Counter[str]] = defaultdict(Counter)
        for r in results:
            outcome = r.outcome.value if r.outcome else "unknown"
            grouped[r.course_code.upper()][outcome] += 1
        rows = []
        for course, counter in sorted(grouped.items()):
            rows.append({"course_code": course, "pass": counter.get(ExamSubjectResultOutcome.PASS.value, 0), "fail": counter.get(ExamSubjectResultOutcome.FAIL.value, 0), "other": sum(v for k, v in counter.items() if k not in {ExamSubjectResultOutcome.PASS.value, ExamSubjectResultOutcome.FAIL.value})})
        return rows, {"result_rows": len(results)}

    async def _grade_distribution(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        base = self._session_filter(ctx)
        results = await ExamStudentSubjectResult.find(base).to_list()
        grades: Counter[str] = Counter((r.grade_letter or "NA") for r in results)
        rows = [{"grade_letter": k, "count": v} for k, v in sorted(grades.items())]
        return rows, {"graded_results": len(results)}

    async def _gpa_distribution(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        base = self._session_filter(ctx)
        calcs = await ExamGpaCalculation.find(base).to_list()
        buckets = Counter()
        for c in calcs:
            gpa = c.gpa or 0.0
            if gpa < 5:
                buckets["0-4.99"] += 1
            elif gpa < 7:
                buckets["5-6.99"] += 1
            elif gpa < 9:
                buckets["7-8.99"] += 1
            else:
                buckets["9-10"] += 1
        rows = [{"gpa_bucket": k, "count": v} for k, v in sorted(buckets.items())]
        return rows, {"students": len(calcs)}

    async def _publication_status(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        pubs = await ExamResultPublication.find(
            Eq(ExamResultPublication.tenant_id, ctx.tenant_id),
            In(ExamResultPublication.exam_session_id, list(ctx.session_ids)),
        ).to_list()
        by_status: Counter[str] = Counter(p.status.value for p in pubs)
        rows = [{"status": k, "count": v} for k, v in sorted(by_status.items())]
        published = by_status.get(ExamPublicationStatus.PUBLISHED.value, 0)
        return rows, {"publication_count": len(pubs), "published_count": published}

    async def _arrear_supplementary(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        arrears = await StudentArrearReference.find(
            Eq(StudentArrearReference.tenant_id, ctx.tenant_id),
            Eq(StudentArrearReference.backlog_status, BacklogStatus.PENDING),
        ).to_list()
        supp = await ExamSupplementaryRegistration.find(Eq(ExamSupplementaryRegistration.tenant_id, ctx.tenant_id)).to_list()
        return [
            {"metric": "pending_arrears", "count": len(arrears)},
            {"metric": "supplementary_registrations", "count": len(supp)},
        ], {"arrear_courses": len({a.course_code for a in arrears})}

    async def _revaluation_statistics(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        apps = await ExamRevaluationApplication.find(
            Eq(ExamRevaluationApplication.tenant_id, ctx.tenant_id),
            In(ExamRevaluationApplication.exam_session_id, list(ctx.session_ids)),
        ).to_list()
        by_status: Counter[str] = Counter(a.status.value for a in apps)
        rows = [{"status": k, "count": v} for k, v in sorted(by_status.items())]
        return rows, {"application_count": len(apps)}

    async def _incident_summary(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        incidents = await ExamIncidentRecord.find(
            Eq(ExamIncidentRecord.tenant_id, ctx.tenant_id),
            In(ExamIncidentRecord.exam_session_id, list(ctx.session_ids)),
        ).to_list()
        cases = await ExamMalpracticeCase.find(Eq(ExamMalpracticeCase.tenant_id, ctx.tenant_id)).to_list()
        # Omit narrative fields; counts only
        return [
            {"metric": "incidents", "count": len(incidents)},
            {"metric": "malpractice_cases", "count": len(cases)},
            {"metric": "cases_proven", "count": sum(1 for c in cases if c.proven is True)},
        ], {"incident_count": len(incidents)}

    async def _department_performance(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        base = self._session_filter(ctx)
        results = await ExamStudentSubjectResult.find(base).to_list()
        if not results:
            return [], {"departments": 0}
        student_ids = list({r.student_user_id for r in results})
        profiles = await StudentProfile.find(
            Eq(StudentProfile.tenant_id, ctx.tenant_id),
            In(StudentProfile.user_id, student_ids),
        ).to_list()
        dept_by_user = {p.user_id: (p.department_code or "UNKNOWN") for p in profiles}
        if ctx.filters.department_code:
            results = [r for r in results if dept_by_user.get(r.student_user_id) == ctx.filters.department_code]
        dept_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in results:
            dept = dept_by_user.get(r.student_user_id, "UNKNOWN")
            if r.outcome == ExamSubjectResultOutcome.PASS:
                dept_stats[dept][0] += 1
            else:
                dept_stats[dept][1] += 1
        rows = []
        for dept, (passed, failed) in sorted(dept_stats.items()):
            total = passed + failed
            rows.append({"department_code": dept, "pass_count": passed, "fail_count": failed, "pass_rate": round(passed / total, 4) if total else 0})
        return rows, {"departments": len(rows)}

    async def _processing_turnaround(self, ctx: ExamReportContext) -> tuple[list[dict], dict]:
        sessions = await ExamSession.find({"tenant_id": ctx.tenant_id, "_id": {"$in": list(ctx.session_ids)}}).to_list()
        pubs = await ExamResultPublication.find(
            Eq(ExamResultPublication.tenant_id, ctx.tenant_id),
            In(ExamResultPublication.exam_session_id, list(ctx.session_ids)),
            Eq(ExamResultPublication.status, ExamPublicationStatus.PUBLISHED),
        ).to_list()
        pub_by_session = {p.exam_session_id: p for p in pubs}
        rows = []
        days: list[int] = []
        for s in sessions:
            pub = pub_by_session.get(s.id)
            if not pub or not pub.published_at:
                continue
            end = as_utc_aware(s.examination_end_at)
            published = as_utc_aware(pub.published_at)
            delta = max(0, int((published - end).total_seconds() // 86400))
            days.append(delta)
            rows.append({"session_code": s.session_code, "days_to_publish": delta})
        avg = round(sum(days) / len(days), 2) if days else 0
        return rows, {"average_days": avg, "sessions_published": len(rows)}