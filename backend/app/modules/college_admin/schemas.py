"""College admin API schemas."""

from datetime import date, datetime
from typing import Any

from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr, Field

from app.modules.college_admin.enums import DashboardDateRange, PendingApprovalCategory
from app.modules.college_admin.models import (
    InstitutionActivityLog,
    InstitutionBranding,
    InstitutionCampus,
    InstitutionConfigurationVersion,
    InstitutionProfile,
    InstitutionSettings,
)
from app.modules.tenants.platform_models import InstitutionAddress


class DashboardFilterParams(BaseModel):
    anchor_date: date | None = None
    date_range: DashboardDateRange = DashboardDateRange.WEEK
    department_id: str | None = None
    campus_id: str | None = None
    academic_year_label: str | None = None


class AcademicTermSummary(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None


class HeadcountStatistics(BaseModel):
    total_students: int = 0
    active_students: int = 0
    faculty_count: int = 0
    employee_count: int = 0
    department_count: int = 0
    programme_count: int = 0


class AttendanceDashboardSummary(BaseModel):
    sessions_submitted: int = 0
    pending_submissions: int = 0
    correction_requests_open: int = 0


class ExaminationDashboardSummary(BaseModel):
    scheduled_exams: int = 0
    pending_evaluations: int = 0
    published_results: int = 0


class FinanceDashboardSummary(BaseModel):
    collected_amount: float = 0
    outstanding_amount: float = 0
    open_demands: int = 0
    overdue_demands: int = 0


class LibraryHostelSummary(BaseModel):
    catalog_items: int = 0
    active_circulation: int = 0
    open_fines: int = 0
    hostel_allocations: int = 0
    pending_hostel_applications: int = 0


class IntegrationHealthSummary(BaseModel):
    provider_code: str
    status: str
    last_check_at: datetime | None = None
    detail: str | None = None


class NotificationSummary(BaseModel):
    title: str
    message: str
    severity: str = "info"
    created_at: datetime


class ActivitySummary(BaseModel):
    activity_id: str
    category: str
    title: str
    actor_label: str | None = None
    occurred_at: datetime
    reference_id: str | None = None


class PendingApprovalItem(BaseModel):
    category: PendingApprovalCategory
    title: str
    submitted_at: datetime
    reference_id: str
    department_id: str | None = None
    campus_id: str | None = None


class SupportRequestSummary(BaseModel):
    request_id: str
    title: str
    status: str
    category: str
    created_at: datetime


class CollegeDashboardOverview(BaseModel):
    filters: DashboardFilterParams
    academic_term: AcademicTermSummary
    statistics: HeadcountStatistics
    attendance: AttendanceDashboardSummary
    examinations: ExaminationDashboardSummary
    finance: FinanceDashboardSummary
    library_hostel: LibraryHostelSummary
    pending_approval_count: int = 0
    unresolved_support_count: int = 0
    upcoming_events: list[dict[str, Any]] = Field(default_factory=list)
    notifications: list[NotificationSummary] = Field(default_factory=list)
    integration_health: list[IntegrationHealthSummary] = Field(default_factory=list)


class CollegeDashboardStatsRead(BaseModel):
    academic_term: AcademicTermSummary
    statistics: HeadcountStatistics


class OperationalSummariesRead(BaseModel):
    attendance: AttendanceDashboardSummary
    examinations: ExaminationDashboardSummary
    finance: FinanceDashboardSummary
    library_hostel: LibraryHostelSummary
    integration_health: list[IntegrationHealthSummary] = Field(default_factory=list)


class InstitutionProfileUpdate(BaseModel):
    legal_name: str | None = Field(default=None, min_length=2, max_length=200)
    display_name: str | None = Field(default=None, min_length=2, max_length=200)
    institution_code: str | None = Field(default=None, min_length=2, max_length=32)
    secondary_codes: list[str] | None = None
    institution_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    official_website: str | None = Field(default=None, max_length=500)
    address: InstitutionAddress | None = None
    institution_type: str | None = Field(default=None, min_length=2, max_length=64)
    affiliation_name: str | None = Field(default=None, max_length=200)
    affiliation_type: str | None = Field(default=None, max_length=64)
    affiliation_id: str | None = Field(default=None, max_length=64)


class InstitutionProfileRead(BaseModel):
    tenant_id: str
    tenant_code: str
    legal_name: str
    display_name: str
    institution_code: str | None = None
    secondary_codes: list[str] = Field(default_factory=list)
    institution_email: str | None = None
    contact_phone: str | None = None
    official_website: str | None = None
    address: InstitutionAddress
    institution_type: str | None = None
    affiliation_name: str | None = None
    affiliation_type: str | None = None
    affiliation_id: str | None = None
    timezone: str
    locale: str
    version: int
    updated_at: datetime

    @classmethod
    def from_document(cls, profile: InstitutionProfile, *, tenant_code: str, timezone: str, locale: str) -> "InstitutionProfileRead":
        return cls(
            tenant_id=str(profile.tenant_id),
            tenant_code=tenant_code,
            legal_name=profile.legal_name,
            display_name=profile.display_name,
            institution_code=profile.institution_code,
            secondary_codes=profile.secondary_codes,
            institution_email=profile.institution_email,
            contact_phone=profile.contact_phone,
            official_website=profile.official_website,
            address=profile.address,
            institution_type=profile.institution_type,
            affiliation_name=profile.affiliation_name,
            affiliation_type=profile.affiliation_type,
            affiliation_id=profile.affiliation_id,
            timezone=timezone,
            locale=locale,
            version=profile.version,
            updated_at=profile.updated_at,
        )


class CampusCreate(BaseModel):
    campus_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    is_main: bool = False
    address: InstitutionAddress | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, max_length=16)


class CampusUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    is_main: bool | None = None
    is_active: bool | None = None
    address: InstitutionAddress | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, max_length=16)


class CampusRead(BaseModel):
    campus_id: str
    campus_code: str
    name: str
    is_main: bool
    is_active: bool
    address: InstitutionAddress
    contact_email: str | None = None
    contact_phone: str | None = None
    timezone: str | None = None
    locale: str | None = None
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: InstitutionCampus) -> "CampusRead":
        return cls(
            campus_id=str(doc.id),
            campus_code=doc.campus_code,
            name=doc.name,
            is_main=doc.is_main,
            is_active=doc.is_active,
            address=doc.address,
            contact_email=doc.contact_email,
            contact_phone=doc.contact_phone,
            timezone=doc.timezone,
            locale=doc.locale,
            updated_at=doc.updated_at,
        )


class InstitutionSettingsRead(BaseModel):
    tenant_id: str
    settings: dict[str, Any]
    branding: dict[str, Any] | None = None
    version: int
    updated_at: datetime

    @classmethod
    def from_parts(
        cls,
        settings: InstitutionSettings,
        branding: InstitutionBranding | None,
    ) -> "InstitutionSettingsRead":
        return cls(
            tenant_id=str(settings.tenant_id),
            settings=settings.settings,
            branding={
                "display_name": branding.display_name,
                "primary_color": branding.primary_color,
                "secondary_color": branding.secondary_color,
                "logo_file_id": branding.logo_file_id,
                "favicon_file_id": branding.favicon_file_id,
                "theme": branding.theme,
                "version": branding.version,
            }
            if branding
            else None,
            version=settings.version,
            updated_at=settings.updated_at,
        )


class InstitutionConfigurationHistoryItem(BaseModel):
    scope: str
    version_number: int
    changed_keys: list[str]
    created_at: datetime
    created_by: str | None = None

    @classmethod
    def from_document(cls, doc: InstitutionConfigurationVersion) -> "InstitutionConfigurationHistoryItem":
        return cls(
            scope=doc.scope,
            version_number=doc.version_number,
            changed_keys=doc.changed_keys,
            created_at=doc.created_at,
            created_by=str(doc.created_by) if doc.created_by else None,
        )


class CampusOverviewRow(BaseModel):
    campus_id: str
    campus_code: str
    name: str
    is_main: bool
    is_active: bool
    location_label: str
    student_count: int = 0
    department_count: int = 0


class ProgrammeLevelMixItem(BaseModel):
    level: str
    label: str
    student_count: int = 0
    programme_count: int = 0


class ComplianceStatusItem(BaseModel):
    title: str
    status_code: str
    detail: str | None = None


class KeyContactItem(BaseModel):
    name: str
    role_label: str
    email: str | None = None
    phone: str | None = None


class InstitutionalOverviewRead(BaseModel):
    profile: InstitutionProfileRead
    academic_term: AcademicTermSummary
    statistics: HeadcountStatistics
    accreditation_summary: str | None = None
    accreditation_detail: str | None = None
    campuses: list[CampusOverviewRow] = Field(default_factory=list)
    programme_mix: list[ProgrammeLevelMixItem] = Field(default_factory=list)
    compliance_items: list[ComplianceStatusItem] = Field(default_factory=list)
    key_contacts: list[KeyContactItem] = Field(default_factory=list)
    generated_at: datetime


class StudentStatisticsFilters(BaseModel):
    academic_year_label: str | None = None
    programme_code: str | None = None
    study_year: int | None = Field(default=None, ge=1, le=6)
    department_id: str | None = None
    campus_id: str | None = None


class StudentStatisticsKpiRead(BaseModel):
    total_enrolled: int = 0
    total_enrolled_change_pct: float | None = None
    total_enrolled_change_reference_year: str | None = None
    new_admissions: int = 0
    new_admissions_intake_sanctioned: int | None = None
    new_admissions_intake_fill_pct: float | None = None
    hostel_residents: int = 0
    hostel_residents_pct_of_enrolled: float | None = None
    discontinued: int = 0
    discontinued_pct_of_enrolled: float | None = None
    discontinued_this_semester: int | None = None


class DepartmentEnrolmentItem(BaseModel):
    department_id: str | None = None
    department_code: str
    department_name: str
    student_count: int = 0


class ProgrammeYearMatrixRow(BaseModel):
    group_key: str
    label: str
    year_1: int = 0
    year_2: int = 0
    year_3: int = 0
    year_4: int = 0
    total: int = 0


class DistributionItem(BaseModel):
    key: str
    label: str
    count: int = 0
    share_pct: float | None = None


class StudentStatusOverviewItem(BaseModel):
    status_key: str
    label: str
    description: str
    count: int = 0


class StudentStatisticsOverviewRead(BaseModel):
    filters: StudentStatisticsFilters
    academic_term: AcademicTermSummary
    kpis: StudentStatisticsKpiRead
    enrolment_by_department: list[DepartmentEnrolmentItem] = Field(default_factory=list)
    programme_year_matrix: list[ProgrammeYearMatrixRow] = Field(default_factory=list)
    programme_matrix_student_total: int = 0
    programme_matrix_group_count: int = 0
    gender_distribution: list[DistributionItem] = Field(default_factory=list)
    admission_category: list[DistributionItem] = Field(default_factory=list)
    student_status: list[StudentStatusOverviewItem] = Field(default_factory=list)
    generated_at: datetime


class FacultyStatisticsFilters(BaseModel):
    anchor_date: date | None = None
    date_range: DashboardDateRange = DashboardDateRange.TODAY
    department_id: str | None = None
    designation: str | None = None
    campus_id: str | None = None


class FacultyStatisticsKpiRead(BaseModel):
    teaching_faculty_total: int = 0
    teaching_faculty_regular: int = 0
    teaching_faculty_visiting: int = 0
    non_teaching_staff_total: int = 0
    non_teaching_staff_detail: str | None = None
    student_faculty_ratio_display: str | None = None
    student_faculty_ratio_students_per_faculty: float | None = None
    regulatory_ratio_max: float | None = None
    regulatory_ratio_label: str | None = None
    regulatory_ratio_meets_norm: bool | None = None
    open_positions_total: int = 0
    open_positions_teaching: int = 0
    open_positions_non_teaching: int = 0


class FacultyDepartmentCountItem(BaseModel):
    department_id: str | None = None
    department_code: str
    department_name: str
    faculty_count: int = 0


class RecentJoinerRow(BaseModel):
    user_id: str
    full_name: str
    designation: str | None = None
    department_name: str | None = None
    joined_on: date | None = None
    onboarding_status: str
    onboarding_label: str


class AvailabilityOverviewItem(BaseModel):
    status_key: str
    label: str
    description: str
    count: int = 0


class FacultyStatisticsOverviewRead(BaseModel):
    filters: FacultyStatisticsFilters
    academic_term: AcademicTermSummary
    kpis: FacultyStatisticsKpiRead
    faculty_by_department: list[FacultyDepartmentCountItem] = Field(default_factory=list)
    recently_joined: list[RecentJoinerRow] = Field(default_factory=list)
    recently_joined_count: int = 0
    recently_joined_window_days: int = 30
    qualification_mix: list[DistributionItem] = Field(default_factory=list)
    designation_mix: list[DistributionItem] = Field(default_factory=list)
    availability_today: list[AvailabilityOverviewItem] = Field(default_factory=list)
    availability_anchor_date: date | None = None
    designation_filter_options: list[str] = Field(default_factory=list)
    generated_at: datetime


class DepartmentPerformanceFilters(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None
    programme_code: str | None = None
    programme_level: str | None = Field(default=None, description="ug, pg, doctoral, or all")
    campus_id: str | None = None


class DepartmentPerformanceKpiRead(BaseModel):
    best_pass_rate_pct: float | None = None
    best_pass_rate_department_name: str | None = None
    lowest_pass_rate_pct: float | None = None
    lowest_pass_rate_department_name: str | None = None
    average_attendance_pct: float | None = None
    departments_above_attendance_threshold: int = 0
    departments_attendance_threshold_pct: float = 85.0
    departments_total_for_attendance: int = 0
    faculty_vacancies_total: int = 0
    faculty_vacancies_department_count: int = 0


class DepartmentScorecardRow(BaseModel):
    department_id: str
    department_code: str
    department_name: str
    head_of_department: str | None = None
    head_acting: bool = False
    student_count: int = 0
    faculty_count: int = 0
    pass_rate_pct: float | None = None
    attendance_pct: float | None = None
    average_cgpa: float | None = None
    status_key: str = "monitor"
    status_label: str = "Monitor"


class DepartmentPassRateBarItem(BaseModel):
    department_id: str
    department_code: str
    department_name: str
    pass_rate_pct: float | None = None
    status_key: str


class DepartmentAttentionItem(BaseModel):
    department_id: str
    department_name: str
    message: str
    status_key: str
    status_label: str


class DepartmentPerformanceOverviewRead(BaseModel):
    filters: DepartmentPerformanceFilters
    academic_term: AcademicTermSummary
    semester_display_label: str | None = None
    kpis: DepartmentPerformanceKpiRead
    scorecard: list[DepartmentScorecardRow] = Field(default_factory=list)
    scorecard_total: int = 0
    scorecard_display_limit: int = 8
    pass_rate_by_department: list[DepartmentPassRateBarItem] = Field(default_factory=list)
    needs_attention: list[DepartmentAttentionItem] = Field(default_factory=list)
    generated_at: datetime


class AcademicPerformanceFilters(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None
    programme_code: str | None = None
    study_year: int | None = Field(default=None, ge=1, le=6)


class AcademicPerformanceKpiRead(BaseModel):
    overall_pass_rate_pct: float | None = None
    overall_pass_rate_change_pts: float | None = None
    overall_pass_rate_reference_label: str | None = None
    average_cgpa: float | None = None
    average_cgpa_ug: float | None = None
    average_cgpa_pg: float | None = None
    first_class_distinction_pct: float | None = None
    first_class_distinction_student_count: int = 0
    students_with_backlogs: int = 0
    students_with_backlogs_pct: float | None = None
    students_with_three_plus_arrears: int = 0


class PassRateTrendPoint(BaseModel):
    label: str
    college_pass_rate_pct: float | None = None
    university_benchmark_pct: float | None = None


class PassRateByStudyYearBar(BaseModel):
    bucket_key: str
    label: str
    pass_rate_pct: float | None = None
    student_count: int = 0


class LowPassSubjectRow(BaseModel):
    course_code: str
    course_name: str | None = None
    department_code: str | None = None
    department_name: str | None = None
    semester_label: str | None = None
    appeared_count: int = 0
    pass_rate_pct: float | None = None
    trend_key: str = "stable"
    trend_label: str = "Stable"


class GradeDistributionItem(DistributionItem):
    grade_letter: str | None = None


class AcademicRiskItem(BaseModel):
    risk_key: str
    label: str
    description: str | None = None
    count: int = 0


class TopPerformerRow(BaseModel):
    user_id: str
    full_name: str
    programme_label: str | None = None
    study_year_label: str | None = None
    cgpa: float


class AcademicPerformanceOverviewRead(BaseModel):
    filters: AcademicPerformanceFilters
    academic_term: AcademicTermSummary
    results_display_label: str | None = None
    kpis: AcademicPerformanceKpiRead
    pass_rate_trend: list[PassRateTrendPoint] = Field(default_factory=list)
    pass_rate_by_study_year: list[PassRateByStudyYearBar] = Field(default_factory=list)
    low_pass_subjects: list[LowPassSubjectRow] = Field(default_factory=list)
    low_pass_subjects_below_pct: float = 80.0
    grade_distribution: list[GradeDistributionItem] = Field(default_factory=list)
    academic_risk: list[AcademicRiskItem] = Field(default_factory=list)
    top_performers: list[TopPerformerRow] = Field(default_factory=list)
    generated_at: datetime


class AttendanceOverviewFilters(BaseModel):
    anchor_date: date | None = None
    date_range: DashboardDateRange = DashboardDateRange.MONTH
    department_id: str | None = None
    programme_code: str | None = None
    campus_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None


class AttendanceOverviewKpiRead(BaseModel):
    today_student_attendance_pct: float | None = None
    today_students_present: int = 0
    today_students_total: int = 0
    semester_average_pct: float | None = None
    semester_target_pct: float = 85.0
    semester_minimum_pct: float = 75.0
    students_below_minimum: int = 0
    today_faculty_attendance_pct: float | None = None
    today_faculty_present: int = 0
    today_faculty_total: int = 0


class DailyAttendancePoint(BaseModel):
    label: str
    session_date: date
    attendance_pct: float | None = None
    students_present: int = 0
    students_total: int = 0


class AttendanceDepartmentRow(BaseModel):
    department_id: str
    department_code: str
    department_name: str
    student_count: int = 0
    today_pct: float | None = None
    semester_avg_pct: float | None = None
    below_minimum_count: int = 0
    status_key: str = "monitor"
    status_label: str = "Monitor"


class AttendanceByYearItem(BaseModel):
    bucket_key: str
    label: str
    attendance_pct: float | None = None
    student_count: int = 0


class AttendanceCorrectionBucket(BaseModel):
    bucket_key: str
    label: str
    count: int = 0


class AttendanceShortageAlert(BaseModel):
    alert_key: str
    label: str
    count: int = 0


class AttendanceOverviewRead(BaseModel):
    filters: AttendanceOverviewFilters
    academic_term: AcademicTermSummary
    range_display_label: str | None = None
    kpis: AttendanceOverviewKpiRead
    daily_student_attendance: list[DailyAttendancePoint] = Field(default_factory=list)
    department_rows: list[AttendanceDepartmentRow] = Field(default_factory=list)
    department_rows_total: int = 0
    department_rows_limit: int = 8
    attendance_by_year: list[AttendanceByYearItem] = Field(default_factory=list)
    correction_requests: list[AttendanceCorrectionBucket] = Field(default_factory=list)
    shortage_alerts: list[AttendanceShortageAlert] = Field(default_factory=list)
    generated_at: datetime


class ExaminationOverviewFilters(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None
    exam_session_id: str | None = None


class ExaminationUpcomingSessionKpi(BaseModel):
    session_name: str | None = None
    session_code: str | None = None
    date_range_label: str | None = None
    days_to_go: int | None = None
    exam_session_id: str | None = None


class ExaminationResultsPendingItem(BaseModel):
    exam_session_id: str
    label: str
    session_name: str


class ExaminationOverviewKpiRead(BaseModel):
    upcoming_session: ExaminationUpcomingSessionKpi = Field(default_factory=ExaminationUpcomingSessionKpi)
    papers_scheduled: int = 0
    programmes_count: int = 0
    hall_tickets_issued: int = 0
    hall_tickets_total: int = 0
    hall_tickets_issued_pct: float | None = None
    hall_tickets_withheld: int = 0
    results_pending_count: int = 0
    results_pending: list[ExaminationResultsPendingItem] = Field(default_factory=list)


class ExaminationTimetableAlert(BaseModel):
    title: str
    description: str
    submitted_at: datetime | None = None
    timetable_id: str | None = None
    review_href_note: str | None = None


class UpcomingExamScheduleRow(BaseModel):
    row_key: str
    date_session_label: str
    programme_label: str
    papers_count: int = 0
    candidates_count: int | None = None
    halls_count: int | None = None
    status_key: str = "ready"
    status_label: str = "Ready"


class ExaminationResultBarItem(BaseModel):
    bucket_key: str
    label: str
    pass_rate_pct: float | None = None
    student_count: int = 0


class ExaminationReadinessItem(BaseModel):
    step_key: str
    label: str
    description: str
    status_key: str
    status_label: str
    progress_pct: float | None = None


class ExaminationPostResultItem(BaseModel):
    item_key: str
    label: str
    description: str | None = None
    count: int = 0


class ExaminationOverviewRead(BaseModel):
    filters: ExaminationOverviewFilters
    academic_term: AcademicTermSummary
    kpis: ExaminationOverviewKpiRead
    timetable_alert: ExaminationTimetableAlert | None = None
    upcoming_schedule: list[UpcomingExamScheduleRow] = Field(default_factory=list)
    upcoming_schedule_total: int = 0
    upcoming_schedule_limit: int = 5
    result_summary_title: str | None = None
    result_summary_bars: list[ExaminationResultBarItem] = Field(default_factory=list)
    readiness_checklist: list[ExaminationReadinessItem] = Field(default_factory=list)
    post_result_activity: list[ExaminationPostResultItem] = Field(default_factory=list)
    generated_at: datetime


class FinanceOverviewFilters(BaseModel):
    academic_year_label: str | None = None
    programme_code: str | None = None
    fee_head: str | None = None


class FinanceOverviewKpiRead(BaseModel):
    total_demand_inr: float = 0
    student_count: int = 0
    fee_head_count: int = 0
    collected_inr: float = 0
    collected_pct: float | None = None
    outstanding_inr: float = 0
    students_with_dues: int = 0
    scholarships_concessions_inr: float = 0
    scholarship_beneficiaries: int = 0


class FinanceMonthlyCollectionPoint(BaseModel):
    year: int
    month: int
    label: str
    amount_inr: float = 0
    is_month_to_date: bool = False


class FinanceProgrammeDuesRow(BaseModel):
    bucket_key: str
    label: str
    demand_amount: float = 0
    collected_amount: float = 0
    outstanding_amount: float = 0
    students_with_dues: int = 0
    collection_pct: float | None = None
    status_key: str = "monitor"
    status_label: str = "—"


class FinancePaymentModeItem(BaseModel):
    mode_key: str
    label: str
    share_pct: float | None = None
    amount_inr: float = 0


class FinanceAttentionItem(BaseModel):
    item_key: str
    label: str
    count: int = 0


class FinanceScholarshipDisbursementItem(BaseModel):
    program_label: str
    amount_inr: float = 0


class FinanceOverviewRead(BaseModel):
    filters: FinanceOverviewFilters
    academic_term: AcademicTermSummary
    academic_year_display: str | None = None
    kpis: FinanceOverviewKpiRead
    monthly_collection: list[FinanceMonthlyCollectionPoint] = Field(default_factory=list)
    programme_dues_rows: list[FinanceProgrammeDuesRow] = Field(default_factory=list)
    collection_target_pct: float = 85.0
    payment_modes: list[FinancePaymentModeItem] = Field(default_factory=list)
    attention_items: list[FinanceAttentionItem] = Field(default_factory=list)
    scholarship_disbursements: list[FinanceScholarshipDisbursementItem] = Field(default_factory=list)
    fee_head_options: list[str] = Field(default_factory=list)
    generated_at: datetime


class PendingApprovalOverviewFilters(BaseModel):
    date_range: DashboardDateRange | None = None
    module_key: str | None = None
    requester_id: str | None = None


class PendingApprovalOverviewKpiRead(BaseModel):
    awaiting_action: int = 0
    modules_with_pending: int = 0
    overdue_count: int = 0
    overdue_sla_days: int = 3
    approved_this_week: int = 0
    avg_turnaround_days: float | None = None
    escalated_to_college_admin: int = 0


class PendingApprovalQueueRow(BaseModel):
    reference_id: str
    request_code: str
    title: str
    module_key: str
    module_label: str
    requested_by_label: str
    requester_user_id: str | None = None
    submitted_at: datetime
    submitted_label: str
    sla_key: str
    sla_label: str
    overdue_days: int | None = None
    review_resource_type: str
    review_resource_id: str


class PendingApprovalByModuleItem(BaseModel):
    module_key: str
    module_label: str
    count: int = 0


class PendingApprovalEscalationItem(BaseModel):
    escalation_id: str
    title: str
    escalated_by_label: str
    age_days: int = 0
    priority_key: str = "medium"
    priority_label: str = "Medium"


class PendingApprovalRecentDecisionItem(BaseModel):
    event_id: str
    title: str
    decision_key: str
    decision_label: str
    decided_at: datetime
    detail: str | None = None


class PendingApprovalModuleFilterOption(BaseModel):
    module_key: str
    module_label: str


class PendingApprovalRequesterFilterOption(BaseModel):
    user_id: str
    label: str


class RecentActivitiesOverviewFilters(BaseModel):
    anchor_date: date | None = None
    date_range: DashboardDateRange | None = None
    module_key: str | None = None
    user_id: str | None = None
    feed_offset: int = 0
    feed_limit: int = 9


class RecentActivitiesOverviewKpiRead(BaseModel):
    actions_count: int = 0
    actions_kpi_label: str = "Actions today"
    actions_period_label: str = "today"
    actions_vs_daily_avg_pct: float | None = None
    active_administrators: int = 0
    active_role_count: int = 0
    records_changed: int = 0
    records_changed_hint: str = "—"
    failed_actions: int = 0
    failed_actions_hint: str = "—"


class RecentActivityFeedRow(BaseModel):
    activity_id: str
    title: str
    module_key: str
    module_label: str
    performed_by_label: str
    actor_user_id: str | None = None
    occurred_at: datetime
    time_label: str
    result_key: str
    result_label: str


class RecentActivityByModuleItem(BaseModel):
    module_key: str
    module_label: str
    count: int = 0


class RecentActivityTopPerformerItem(BaseModel):
    performer_key: str
    performer_label: str
    module_label: str
    action_count: int = 0


class RecentActivityFollowUpItem(BaseModel):
    item_key: str
    title: str
    detail: str | None = None
    action_key: str
    action_label: str
    resource_type: str | None = None
    resource_id: str | None = None


class RecentActivityModuleFilterOption(BaseModel):
    module_key: str
    module_label: str


class RecentActivityUserFilterOption(BaseModel):
    user_id: str
    label: str


class RecentActivitiesOverviewRead(BaseModel):
    filters: RecentActivitiesOverviewFilters
    scope_label: str = "College scope"
    kpis: RecentActivitiesOverviewKpiRead
    feed_rows: list[RecentActivityFeedRow] = Field(default_factory=list)
    feed_total: int = 0
    feed_limit: int = 9
    feed_offset: int = 0
    activity_by_module: list[RecentActivityByModuleItem] = Field(default_factory=list)
    activity_by_module_max: int = 1
    top_performers: list[RecentActivityTopPerformerItem] = Field(default_factory=list)
    follow_ups: list[RecentActivityFollowUpItem] = Field(default_factory=list)
    module_filter_options: list[RecentActivityModuleFilterOption] = Field(default_factory=list)
    user_filter_options: list[RecentActivityUserFilterOption] = Field(default_factory=list)
    generated_at: datetime


class AlertsOverviewKpiRead(BaseModel):
    critical_count: int = 0
    critical_hint: str = "—"
    warning_count: int = 0
    warning_hint: str = "—"
    info_count: int = 0
    info_hint: str = "—"
    resolved_today: int = 0
    resolved_hint: str = "—"
    avg_resolution_hours: float | None = None


class DashboardAlertItem(BaseModel):
    alert_id: str
    severity_key: str
    severity_label: str
    title: str
    summary: str | None = None
    module_key: str
    module_label: str
    raised_at: datetime
    time_label: str
    action_key: str
    action_label: str
    action_href: str
    is_read: bool = False


class AlertsFeaturedBanner(BaseModel):
    alert_id: str
    title: str
    summary: str | None = None
    action_label: str
    action_href: str


class DashboardAlertByModuleItem(BaseModel):
    module_key: str
    module_label: str
    count: int = 0


class AlertsDeliveryChannelItem(BaseModel):
    channel_key: str
    label: str
    detail: str
    enabled: bool = True


class AlertsRuleItem(BaseModel):
    rule_key: str
    label: str
    value_label: str


class AlertsOverviewRead(BaseModel):
    kpis: AlertsOverviewKpiRead
    featured: AlertsFeaturedBanner | None = None
    all_alerts: list[DashboardAlertItem] = Field(default_factory=list)
    alerts_total: int = 0
    alerts_by_module: list[DashboardAlertByModuleItem] = Field(default_factory=list)
    alerts_by_module_max: int = 1
    delivery_channels: list[AlertsDeliveryChannelItem] = Field(default_factory=list)
    alert_rules: list[AlertsRuleItem] = Field(default_factory=list)
    generated_at: datetime


class PendingApprovalOverviewRead(BaseModel):
    filters: PendingApprovalOverviewFilters
    scope_label: str = "College scope"
    kpis: PendingApprovalOverviewKpiRead
    queue_rows: list[PendingApprovalQueueRow] = Field(default_factory=list)
    queue_total: int = 0
    queue_limit: int = 7
    pending_by_module: list[PendingApprovalByModuleItem] = Field(default_factory=list)
    pending_by_module_max: int = 1
    escalations: list[PendingApprovalEscalationItem] = Field(default_factory=list)
    recently_decided: list[PendingApprovalRecentDecisionItem] = Field(default_factory=list)
    module_filter_options: list[PendingApprovalModuleFilterOption] = Field(default_factory=list)
    requester_filter_options: list[PendingApprovalRequesterFilterOption] = Field(default_factory=list)
    generated_at: datetime


class InstitutionActivityRead(BaseModel):
    activity_kind: str
    summary: str
    resource_type: str
    resource_id: str | None = None
    created_at: datetime

    @classmethod
    def from_document(cls, doc: InstitutionActivityLog) -> "InstitutionActivityRead":
        return cls(
            activity_kind=doc.activity_kind.value,
            summary=doc.summary,
            resource_type=doc.resource_type,
            resource_id=doc.resource_id,
            created_at=doc.created_at,
        )
