"""Data access for HR dashboard metrics."""

from datetime import date, timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.hr_admin_models import EmployeeOnboardingRecord, PayrollConfiguration, RecruitmentRecord, RecruitmentStatus
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.dashboard_filters import HrDashboardContext, employee_record_match
from app.modules.hr.dashboard_schemas import (
    AttendanceOverviewStats,
    CountGroupItem,
    EmployeeOverviewStats,
    HrActivityItem,
    HrAlertItem,
    LeaveOverviewStats,
    OnboardingOverviewStats,
    PayrollOverviewStats,
    RecruitmentOverviewStats,
)
from app.modules.hr.document_models import HrEmployeeDocument
from app.modules.hr.employee_profile_models import HrEmployeeProfile, HrEmployeeProfileCorrectionRequest
from app.modules.hr.enums import HrEmployeeDocumentStatus
from app.modules.hr.enums import (
    EmployeeAttendanceCorrectionStatus,
    EmployeeAttendanceDayStatus,
    HrApplicationPipelineStage,
    HrJobOpeningStatus,
    HrOnboardingProcessStatus,
    HrRecruitmentApplicationStatus,
    LeaveRequestStatus,
    ProfileCorrectionStatus,
    ProfileVerificationStatus,
)
from app.modules.hr.onboarding_models import HrOnboardingProcess, HrOnboardingTask
from app.modules.hr.recruitment_models import HrJobApplication, HrJobOpening
from app.modules.hr.models import LeaveRequest, PayslipReference
from app.modules.hr.operational_models import EmployeeAttendanceCorrection, EmployeeDayAttendance, HrRecruitmentApplication, HrStaffActivityLog
from app.modules.tenants.models import Department


def _legacy_application_status(stage: HrApplicationPipelineStage) -> HrRecruitmentApplicationStatus:
    mapping = {
        HrApplicationPipelineStage.APPLICATION_SUBMITTED: HrRecruitmentApplicationStatus.NEW,
        HrApplicationPipelineStage.INITIAL_SCREENING: HrRecruitmentApplicationStatus.NEW,
        HrApplicationPipelineStage.UNDER_REVIEW: HrRecruitmentApplicationStatus.UNDER_REVIEW,
        HrApplicationPipelineStage.INTERVIEW_SCHEDULED: HrRecruitmentApplicationStatus.INTERVIEW_SCHEDULED,
        HrApplicationPipelineStage.INTERVIEW_COMPLETED: HrRecruitmentApplicationStatus.AWAITING_FEEDBACK,
        HrApplicationPipelineStage.SELECTED: HrRecruitmentApplicationStatus.SELECTED,
        HrApplicationPipelineStage.REJECTED: HrRecruitmentApplicationStatus.REJECTED,
        HrApplicationPipelineStage.OFFER_ISSUED: HrRecruitmentApplicationStatus.AWAITING_OFFER_ACCEPTANCE,
        HrApplicationPipelineStage.OFFER_ACCEPTED: HrRecruitmentApplicationStatus.SELECTED,
    }
    return mapping.get(stage, HrRecruitmentApplicationStatus.UNDER_REVIEW)


class HrDashboardRepository:
    async def _scoped_employees(self, ctx: HrDashboardContext) -> list[EmployeeRecord]:
        return await EmployeeRecord.find(employee_record_match(ctx)).to_list()

    async def employee_overview(self, ctx: HrDashboardContext) -> EmployeeOverviewStats:
        rows = await self._scoped_employees(ctx)
        stats = EmployeeOverviewStats(total=len(rows))
        dept_counts: dict[str, int] = {}
        desig_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        campus_counts: dict[str, int] = {}
        for row in rows:
            status = row.employment_status
            if status == FacultyEmploymentStatus.ACTIVE:
                stats.active += 1
            elif status == FacultyEmploymentStatus.INACTIVE:
                stats.inactive += 1
            elif status == FacultyEmploymentStatus.PROBATION:
                stats.probation += 1
            elif status == FacultyEmploymentStatus.AWAITING_CONFIRMATION:
                stats.awaiting_confirmation += 1
            elif status == FacultyEmploymentStatus.NOTICE_PERIOD:
                stats.notice_period += 1
            elif status == FacultyEmploymentStatus.RESIGNED:
                stats.resigned += 1
            elif status == FacultyEmploymentStatus.TERMINATED:
                stats.terminated += 1
            if row.joining_date and ctx.date_from <= row.joining_date <= ctx.date_to:
                stats.recently_joined += 1
            if row.department_id:
                dept_counts[str(row.department_id)] = dept_counts.get(str(row.department_id), 0) + 1
            if row.designation:
                desig_counts[row.designation] = desig_counts.get(row.designation, 0) + 1
            if row.employment_type:
                type_counts[row.employment_type] = type_counts.get(row.employment_type, 0) + 1
            if row.campus_id:
                campus_counts[str(row.campus_id)] = campus_counts.get(str(row.campus_id), 0) + 1

        dept_labels = await self._department_labels(ctx.tenant_id, dept_counts.keys())
        campus_labels = await self._campus_labels(ctx.tenant_id, campus_counts.keys())
        stats.by_department = [CountGroupItem(key=k, label=dept_labels.get(k), count=v) for k, v in sorted(dept_counts.items())]
        stats.by_designation = [CountGroupItem(key=k, label=k, count=v) for k, v in sorted(desig_counts.items())]
        stats.by_employment_type = [CountGroupItem(key=k, label=k, count=v) for k, v in sorted(type_counts.items())]
        stats.by_campus = [CountGroupItem(key=k, label=campus_labels.get(k), count=v) for k, v in sorted(campus_counts.items())]
        return stats

    async def _department_labels(self, tenant_id: PydanticObjectId, ids) -> dict[str, str]:
        out: dict[str, str] = {}
        for raw in ids:
            dept = await Department.get(PydanticObjectId(raw))
            if dept and dept.tenant_id == tenant_id:
                out[raw] = dept.name
            else:
                out[raw] = raw
        return out

    async def _campus_labels(self, tenant_id: PydanticObjectId, ids) -> dict[str, str]:
        out: dict[str, str] = {}
        for raw in ids:
            campus = await InstitutionCampus.get(PydanticObjectId(raw))
            if campus and campus.tenant_id == tenant_id:
                out[raw] = campus.name
            else:
                out[raw] = raw
        return out

    async def attendance_overview(self, ctx: HrDashboardContext) -> AttendanceOverviewStats:
        day = ctx.anchor_date
        match = {"tenant_id": ctx.tenant_id, "attendance_date": day}
        if ctx.department_id:
            match["department_id"] = ctx.department_id
        if ctx.campus_id:
            match["campus_id"] = ctx.campus_id
        rows = await EmployeeDayAttendance.find(match).to_list()
        stats = AttendanceOverviewStats()
        for row in rows:
            if row.status == EmployeeAttendanceDayStatus.PRESENT:
                stats.present_today += 1
            elif row.status == EmployeeAttendanceDayStatus.ABSENT:
                stats.absent_today += 1
            elif row.status == EmployeeAttendanceDayStatus.ON_LEAVE:
                stats.on_leave_today += 1
            elif row.status == EmployeeAttendanceDayStatus.LATE:
                stats.late_today += 1
            elif row.status == EmployeeAttendanceDayStatus.EARLY_DEPARTURE:
                stats.early_departure_today += 1
            elif row.status == EmployeeAttendanceDayStatus.MISSING:
                stats.missing_today += 1
        active_employees = await EmployeeRecord.find(
            employee_record_match(ctx),
            In(
                EmployeeRecord.employment_status,
                [
                    FacultyEmploymentStatus.ACTIVE,
                    FacultyEmploymentStatus.PROBATION,
                    FacultyEmploymentStatus.CONFIRMED,
                ],
            ),
        ).count()
        tracked = len(rows)
        if active_employees > tracked:
            stats.missing_today += active_employees - tracked
        stats.pending_corrections = await EmployeeAttendanceCorrection.find(
            Eq(EmployeeAttendanceCorrection.tenant_id, ctx.tenant_id),
            Eq(EmployeeAttendanceCorrection.status, EmployeeAttendanceCorrectionStatus.PENDING),
        ).count()
        return stats

    async def leave_overview(self, ctx: HrDashboardContext) -> LeaveOverviewStats:
        stats = LeaveOverviewStats()
        base = {"tenant_id": ctx.tenant_id}
        stats.pending = await LeaveRequest.find(
            {
                **base,
                "status": {
                    "$in": [
                        LeaveRequestStatus.SUBMITTED.value,
                        LeaveRequestStatus.PENDING_MANAGER.value,
                        LeaveRequestStatus.PENDING_HR.value,
                        LeaveRequestStatus.CLARIFICATION_REQUESTED.value,
                    ]
                },
            }
        ).count()
        stats.approved = await LeaveRequest.find({**base, "status": LeaveRequestStatus.APPROVED}).count()
        stats.rejected = await LeaveRequest.find({**base, "status": LeaveRequestStatus.REJECTED}).count()

        today = ctx.anchor_date
        approved_rows = await LeaveRequest.find({**base, "status": LeaveRequestStatus.APPROVED}).to_list()
        type_counts: dict[str, int] = {}
        dept_counts: dict[str, int] = {}
        employee_dept: dict[str, PydanticObjectId | None] = {}
        if ctx.department_id or ctx.campus_id:
            for emp in await self._scoped_employees(ctx):
                employee_dept[str(emp.user_id)] = emp.department_id

        for row in approved_rows:
            if ctx.department_id and employee_dept.get(str(row.employee_user_id)) != ctx.department_id:
                continue
            type_counts[row.leave_type] = type_counts.get(row.leave_type, 0) + 1
            dept_id = employee_dept.get(str(row.employee_user_id))
            if dept_id:
                dept_counts[str(dept_id)] = dept_counts.get(str(dept_id), 0) + 1
            if row.start_date <= today <= row.end_date:
                stats.currently_on_leave += 1
            if row.start_date > today:
                stats.upcoming_approved += 1

        dept_labels = await self._department_labels(ctx.tenant_id, dept_counts.keys())
        stats.by_leave_type = [CountGroupItem(key=k, label=k, count=v) for k, v in sorted(type_counts.items())]
        stats.by_department = [CountGroupItem(key=k, label=dept_labels.get(k), count=v) for k, v in sorted(dept_counts.items())]
        return stats

    async def recruitment_overview(self, ctx: HrDashboardContext) -> RecruitmentOverviewStats:
        stats = RecruitmentOverviewStats()
        req_match = {"tenant_id": ctx.tenant_id}
        if ctx.department_id:
            req_match["department_id"] = ctx.department_id
        openings = await RecruitmentRecord.find(req_match).to_list()
        stats.active_openings = sum(1 for r in openings if r.status == RecruitmentStatus.OPEN)
        hr_openings = await HrJobOpening.find(req_match).to_list()
        stats.active_openings += sum(1 for r in hr_openings if r.status == HrJobOpeningStatus.PUBLISHED)
        legacy_apps = await HrRecruitmentApplication.find(Eq(HrRecruitmentApplication.tenant_id, ctx.tenant_id)).to_list()
        hr_apps = await HrJobApplication.find(Eq(HrJobApplication.tenant_id, ctx.tenant_id)).to_list()
        stats.total_applicants = len(legacy_apps) + len(hr_apps)
        status_buckets: list[HrRecruitmentApplicationStatus] = [_legacy_application_status(a.stage) for a in hr_apps]
        status_buckets.extend(a.status for a in legacy_apps)
        for status in status_buckets:
            if status == HrRecruitmentApplicationStatus.NEW:
                stats.new_applications += 1
            elif status == HrRecruitmentApplicationStatus.UNDER_REVIEW:
                stats.under_review += 1
            elif status == HrRecruitmentApplicationStatus.INTERVIEW_SCHEDULED:
                stats.interviews_scheduled += 1
            elif status == HrRecruitmentApplicationStatus.AWAITING_FEEDBACK:
                stats.awaiting_feedback += 1
            elif status == HrRecruitmentApplicationStatus.SELECTED:
                stats.selected += 1
            elif status == HrRecruitmentApplicationStatus.REJECTED:
                stats.rejected += 1
            elif status == HrRecruitmentApplicationStatus.AWAITING_OFFER_ACCEPTANCE:
                stats.awaiting_offer_acceptance += 1
        return stats

    async def onboarding_overview(self, ctx: HrDashboardContext) -> OnboardingOverviewStats:
        stats = OnboardingOverviewStats()
        hr_processes = await HrOnboardingProcess.find(Eq(HrOnboardingProcess.tenant_id, ctx.tenant_id)).to_list()
        hr_employee_users = {p.employee_user_id for p in hr_processes if p.employee_user_id}
        today = ctx.anchor_date
        for process in hr_processes:
            if process.status == HrOnboardingProcessStatus.COMPLETED:
                stats.completed += 1
                continue
            stats.in_progress += 1
            if ctx.department_id and process.department_id != ctx.department_id:
                continue
            tasks = await HrOnboardingTask.find(Eq(HrOnboardingTask.process_id, process.id)).to_list()
            for task in tasks:
                if task.status.value != "completed":
                    stats.pending_tasks += 1
                    if task.due_date and task.due_date < today:
                        stats.overdue_tasks += 1
        rows = await EmployeeOnboardingRecord.find(Eq(EmployeeOnboardingRecord.tenant_id, ctx.tenant_id)).to_list()
        for row in rows:
            if row.user_id in hr_employee_users:
                continue
            if row.completed:
                stats.completed += 1
                continue
            stats.in_progress += 1
            employee = None
            if row.employee_record_id:
                employee = await EmployeeRecord.get(row.employee_record_id)
            if ctx.department_id and employee and employee.department_id != ctx.department_id:
                continue
            if ctx.campus_id and employee and employee.campus_id != ctx.campus_id:
                continue
            pending = 0
            overdue = 0
            for item in row.checklist:
                done = bool(item.get("completed"))
                due_raw = item.get("due_date")
                if not done:
                    pending += 1
                    stats.pending_tasks += 1
                    if due_raw:
                        try:
                            due = date.fromisoformat(str(due_raw))
                            if due < today:
                                overdue += 1
                                stats.overdue_tasks += 1
                        except ValueError:
                            pass
            if pending:
                stats.awaiting_documents += 1
            profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, ctx.tenant_id), Eq(HrEmployeeProfile.user_id, row.user_id))
            if profile and profile.profile_verification_status == ProfileVerificationStatus.PENDING_VERIFICATION:
                stats.awaiting_verification += 1
            _ = overdue
        return stats

    async def payroll_overview(self, ctx: HrDashboardContext) -> PayrollOverviewStats:
        stats = PayrollOverviewStats()
        configs = await PayrollConfiguration.find(Eq(PayrollConfiguration.tenant_id, ctx.tenant_id)).to_list()
        stats.configuration_count = len(configs)
        if configs:
            primary = sorted(configs, key=lambda c: c.updated_at, reverse=True)[0]
            stats.current_period_label = primary.label
            stats.last_run_status = primary.last_run_status
            stats.pending_approvals = 1 if primary.last_run_status in {"pending_approval", "draft"} else 0
            stats.held_or_failed_records = 1 if primary.last_run_status in {"failed", "held"} else 0
            stats.completed_periods = 1 if primary.last_run_status == "completed" else 0
        employees = await self._scoped_employees(ctx)
        active_statuses = {
            FacultyEmploymentStatus.ACTIVE,
            FacultyEmploymentStatus.PROBATION,
            FacultyEmploymentStatus.CONFIRMED,
            FacultyEmploymentStatus.NOTICE_PERIOD,
        }
        in_scope = [e for e in employees if e.employment_status in active_statuses]
        stats.employees_in_payroll_scope = len(in_scope)
        incomplete = 0
        for emp in in_scope:
            salary = (emp.confidential_hr or {}).get("salary_structure")
            if not salary:
                incomplete += 1
        stats.incomplete_salary_profiles = incomplete
        stats.completed_periods = await PayslipReference.find(Eq(PayslipReference.tenant_id, ctx.tenant_id)).count()
        return stats

    async def alerts(self, ctx: HrDashboardContext) -> list[HrAlertItem]:
        alerts: list[HrAlertItem] = []
        tenant_id = ctx.tenant_id
        pending_docs = await HrEmployeeDocument.find(
            Eq(HrEmployeeDocument.tenant_id, tenant_id),
            Eq(HrEmployeeDocument.status, HrEmployeeDocumentStatus.PENDING_VERIFICATION),
        ).count()
        if pending_docs:
            alerts.append(HrAlertItem(code="documents_pending_verification", severity="warning", message="Employee documents awaiting verification", count=pending_docs))

        expiry_limit = ctx.anchor_date + timedelta(days=30)
        expiring = await HrEmployeeDocument.find(
            {
                "tenant_id": tenant_id,
                "expires_on": {"$lte": expiry_limit, "$gte": ctx.anchor_date},
            }
        ).count()
        if expiring:
            alerts.append(HrAlertItem(code="documents_expiring", severity="warning", message="Documents approaching expiry", count=expiring))

        pending_verification = await HrEmployeeProfile.find(
            Eq(HrEmployeeProfile.tenant_id, tenant_id),
            Eq(HrEmployeeProfile.profile_verification_status, ProfileVerificationStatus.PENDING_VERIFICATION),
        ).count()
        if pending_verification:
            alerts.append(HrAlertItem(code="profiles_pending_verification", severity="info", message="Employee profiles pending verification", count=pending_verification))

        incomplete = await HrEmployeeProfile.find(
            Eq(HrEmployeeProfile.tenant_id, tenant_id),
            Eq(HrEmployeeProfile.profile_completion_status, "incomplete"),
        ).count()
        if incomplete:
            alerts.append(HrAlertItem(code="incomplete_profiles", severity="warning", message="Incomplete employee profiles", count=incomplete))

        corrections = await HrEmployeeProfileCorrectionRequest.find(
            Eq(HrEmployeeProfileCorrectionRequest.tenant_id, tenant_id),
            Eq(HrEmployeeProfileCorrectionRequest.status, ProfileCorrectionStatus.SUBMITTED),
        ).count()
        if corrections:
            alerts.append(HrAlertItem(code="pending_profile_corrections", severity="info", message="Pending employee profile correction requests", count=corrections))

        probation_due = 0
        profiles = await HrEmployeeProfile.find(Eq(HrEmployeeProfile.tenant_id, tenant_id)).to_list()
        for profile in profiles:
            if profile.probation_end_date and ctx.anchor_date <= profile.probation_end_date <= ctx.anchor_date + timedelta(days=30):
                probation_due += 1
        if probation_due:
            alerts.append(HrAlertItem(code="probation_completion", severity="info", message="Upcoming probation completion dates", count=probation_due))

        contract_due = sum(
            1
            for p in profiles
            if p.contract_end_date and ctx.anchor_date <= p.contract_end_date <= ctx.anchor_date + timedelta(days=30)
        )
        if contract_due:
            alerts.append(HrAlertItem(code="contract_expiry", severity="warning", message="Upcoming employment contract expiry dates", count=contract_due))

        missing_mandatory = await HrEmployeeDocument.find(
            Eq(HrEmployeeDocument.tenant_id, tenant_id),
            Eq(HrEmployeeDocument.is_mandatory, True),
            In(
                HrEmployeeDocument.status,
                [HrEmployeeDocumentStatus.PENDING_VERIFICATION, HrEmployeeDocumentStatus.SUBMITTED, HrEmployeeDocumentStatus.DRAFT],
            ),
        ).count()
        if missing_mandatory:
            alerts.append(HrAlertItem(code="missing_mandatory_documents", severity="warning", message="Mandatory employee documents pending", count=missing_mandatory))

        return alerts

    async def recent_activities(self, ctx: HrDashboardContext, *, limit: int = 20) -> list[HrActivityItem]:
        match: dict = {
            "tenant_id": ctx.tenant_id,
            "created_at": {"$gte": ctx.activity_from, "$lt": ctx.activity_to},
        }
        if ctx.department_id:
            match["department_id"] = ctx.department_id
        rows = await HrStaffActivityLog.find(match).sort("-created_at").limit(limit).to_list()
        return [
            HrActivityItem(
                activity_id=str(r.id),
                activity_type=r.activity_type.value,
                summary=r.summary,
                employee_user_id=str(r.employee_user_id) if r.employee_user_id else None,
                department_id=str(r.department_id) if r.department_id else None,
                status_label=r.status_label,
                created_at=r.created_at,
            )
            for r in rows
        ]