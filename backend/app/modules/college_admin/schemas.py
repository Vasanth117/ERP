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
