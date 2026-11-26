"""College admin API schemas."""

from datetime import date, datetime
from typing import Any

from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr, Field, model_validator

from app.core.form_values import blank_to_none

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


class CollegeDashboardAttendanceTrendPoint(BaseModel):
    label: str
    students_pct: float | None = None
    faculty_pct: float | None = None


class CollegeDashboardFeeMonthPoint(BaseModel):
    year: int
    month: int
    label: str
    amount_inr: float = 0
    is_month_to_date: bool = False


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
    attendance_trend: list[CollegeDashboardAttendanceTrendPoint] = Field(default_factory=list)
    fee_monthly_collection: list[CollegeDashboardFeeMonthPoint] = Field(default_factory=list)


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
    short_name: str | None = Field(default=None, min_length=1, max_length=32)
    institution_code: str | None = Field(default=None, min_length=2, max_length=32)
    secondary_codes: list[str] | None = None
    institution_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    contact_fax: str | None = Field(default=None, max_length=32)
    official_website: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    address: InstitutionAddress | None = None
    institution_type: str | None = Field(default=None, min_length=2, max_length=64)
    affiliation_name: str | None = Field(default=None, max_length=200)
    affiliation_type: str | None = Field(default=None, max_length=64)
    affiliation_id: str | None = Field(default=None, max_length=64)
    aishe_code: str | None = Field(default=None, max_length=64)
    ownership_name: str | None = Field(default=None, max_length=200)
    year_established: int | None = Field(default=None, ge=1800, le=2100)
    medium_of_instruction: str | None = Field(default=None, max_length=64)
    accreditation_display: str | None = Field(default=None, max_length=200)
    autonomous_status_valid_until: date | None = None
    ugc_recognition: str | None = Field(default=None, max_length=64)

    @model_validator(mode="before")
    @classmethod
    def _coerce_blank_optional_strings(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        return {key: blank_to_none(value) for key, value in data.items()}


class InstitutionProfileRead(BaseModel):
    tenant_id: str
    tenant_code: str
    legal_name: str
    display_name: str
    short_name: str | None = None
    institution_code: str | None = None
    secondary_codes: list[str] = Field(default_factory=list)
    institution_email: str | None = None
    contact_phone: str | None = None
    contact_fax: str | None = None
    official_website: str | None = None
    description: str | None = None
    address: InstitutionAddress
    institution_type: str | None = None
    affiliation_name: str | None = None
    affiliation_type: str | None = None
    affiliation_id: str | None = None
    aishe_code: str | None = None
    ownership_name: str | None = None
    year_established: int | None = None
    medium_of_instruction: str | None = None
    accreditation_display: str | None = None
    autonomous_status_valid_until: date | None = None
    ugc_recognition: str | None = None
    has_draft: bool = False
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
            short_name=profile.short_name,
            institution_code=profile.institution_code,
            secondary_codes=profile.secondary_codes,
            institution_email=profile.institution_email,
            contact_phone=profile.contact_phone,
            contact_fax=profile.contact_fax,
            official_website=profile.official_website,
            description=profile.description,
            address=profile.address,
            institution_type=profile.institution_type,
            affiliation_name=profile.affiliation_name,
            affiliation_type=profile.affiliation_type,
            affiliation_id=profile.affiliation_id,
            aishe_code=profile.aishe_code,
            ownership_name=profile.ownership_name,
            year_established=profile.year_established,
            medium_of_instruction=profile.medium_of_instruction,
            accreditation_display=profile.accreditation_display,
            autonomous_status_valid_until=profile.autonomous_status_valid_until,
            ugc_recognition=profile.ugc_recognition,
            has_draft=bool(profile.draft_values),
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
    area_acres: float | None = Field(default=None, ge=0)
    built_up_sq_m: float | None = Field(default=None, ge=0)
    buildings_count: int | None = Field(default=None, ge=0)
    parking_slots: int | None = Field(default=None, ge=0)


class CampusUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    is_main: bool | None = None
    is_active: bool | None = None
    address: InstitutionAddress | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, max_length=16)
    area_acres: float | None = Field(default=None, ge=0)
    built_up_sq_m: float | None = Field(default=None, ge=0)
    buildings_count: int | None = Field(default=None, ge=0)
    parking_slots: int | None = Field(default=None, ge=0)


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
    area_acres: float | None = None
    built_up_sq_m: float | None = None
    buildings_count: int | None = None
    parking_slots: int | None = None
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
            area_acres=doc.area_acres,
            built_up_sq_m=doc.built_up_sq_m,
            buildings_count=doc.buildings_count,
            parking_slots=doc.parking_slots,
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


class InstitutionStatusBadge(BaseModel):
    label: str
    tone: str = "success"


class InstitutionAboutField(BaseModel):
    label: str
    value: str | None = None


class InstitutionLeadershipRow(BaseModel):
    name: str
    role_label: str
    detail_line: str | None = None


class ProfileCompletenessRow(BaseModel):
    key: str
    label: str
    completed_count: int
    total_count: int
    progress_percent: int
    status_label: str


class RelatedSettingLink(BaseModel):
    key: str
    title: str
    description: str
    href: str


class InstitutionFieldOption(BaseModel):
    value: str
    label: str


class InstitutionFieldMeta(BaseModel):
    key: str
    label: str
    required: bool = False
    locked: bool = False
    field_type: str = "text"


class CampusCreationWizardStep(BaseModel):
    key: str
    label: str
    subtitle: str = ""
    step_number: int
    status: str = "pending"


class CampusCreationFormValues(BaseModel):
    campus_code: str = ""
    name: str = ""
    is_main: str = ""
    address_line1: str = ""
    address_line2: str = ""
    city: str = ""
    district: str = ""
    state: str = ""
    country: str = ""
    postal_code: str = ""
    latitude: str = ""
    longitude: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    timezone: str = ""
    locale: str = ""
    area_acres: str = ""
    built_up_sq_m: str = ""
    buildings_count: str = ""
    parking_slots: str = ""
    planned_classrooms: str = ""
    planned_laboratories: str = ""
    hostel_blocks_planned: str = ""
    library_branches_planned: str = ""
    facilities_notes: str = ""


class CampusCreationPageRead(BaseModel):
    draft_id: str
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    save_draft_label: str
    create_label: str
    next_label: str = "Save & continue"
    back_step_label: str = "Back"
    current_step_key: str
    steps: list[CampusCreationWizardStep]
    field_meta: list[InstitutionFieldMeta] = Field(default_factory=list)
    form: CampusCreationFormValues = Field(default_factory=CampusCreationFormValues)
    timezone_options: list[InstitutionFieldOption] = Field(default_factory=list)
    locale_options: list[InstitutionFieldOption] = Field(default_factory=list)
    is_edit_mode: bool = False
    edit_campus_id: str | None = None
    has_draft: bool = False
    generated_at: datetime


class CampusCreationDraftUpdate(BaseModel):
    draft_id: str | None = None
    step_key: str | None = None
    values: dict[str, Any] = Field(default_factory=dict)
    advance: bool = False
    retreat: bool = False


class CampusCreationFinishPayload(BaseModel):
    draft_id: str
    values: dict[str, Any] = Field(default_factory=dict)


class CampusCreationFinishResult(BaseModel):
    campus_id: str
    detail_href: str
    message: str = "Campus saved successfully"


class InstitutionInformationNotice(BaseModel):
    title: str
    body: str


class InstitutionUsageContext(BaseModel):
    title: str
    description: str


class InstitutionRecentChange(BaseModel):
    change_id: str
    title: str
    detail_line: str
    tone: str = "success"
    occurred_at: datetime


class InstitutionInformationFormValues(BaseModel):
    legal_name: str
    display_name: str
    short_name: str | None = None
    institution_code: str | None = None
    year_established: int | None = None
    institution_type: str | None = None
    medium_of_instruction: str | None = None
    description: str | None = None
    affiliation_name: str | None = None
    autonomous_status_valid_until: date | None = None
    affiliation_id: str | None = None
    aishe_code: str | None = None
    ugc_recognition: str | None = None
    ownership_name: str | None = None
    institution_email: str | None = None
    contact_phone: str | None = None
    official_website: str | None = None
    contact_fax: str | None = None


class InstitutionProfileDraftUpdate(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


class InstitutionInformationPageRead(BaseModel):
    form: InstitutionInformationFormValues
    field_meta: list[InstitutionFieldMeta]
    institution_type_options: list[InstitutionFieldOption] = Field(default_factory=list)
    medium_of_instruction_options: list[InstitutionFieldOption] = Field(default_factory=list)
    ugc_recognition_options: list[InstitutionFieldOption] = Field(default_factory=list)
    affiliation_options: list[InstitutionFieldOption] = Field(default_factory=list)
    approval_notice: InstitutionInformationNotice
    usage_contexts: list[InstitutionUsageContext] = Field(default_factory=list)
    recent_changes: list[InstitutionRecentChange] = Field(default_factory=list)
    history_href: str
    footer_note: str
    has_draft: bool = False
    generated_at: datetime


class BrandingColorField(BaseModel):
    key: str
    label: str
    value: str | None = None
    required: bool = False


class BrandingPrimaryLogoPanel(BaseModel):
    upload_hint: str
    current_summary: str | None = None
    file_id: str | None = None


class BrandingAssetRow(BaseModel):
    asset_key: str
    label: str
    detail_line: str
    status: str
    status_label: str
    editable: bool = True
    file_name: str | None = None
    file_id: str | None = None


class BrandingDocumentTemplateRow(BaseModel):
    template_key: str
    title: str
    used_for: str
    last_updated_label: str
    status: str
    status_label: str


class BrandingPreviewItem(BaseModel):
    title: str
    description: str


class InstitutionBrandingFormValues(BaseModel):
    primary_color: str
    secondary_color: str
    text_on_primary: str | None = None
    accent_status: str | None = None
    display_name: str | None = None


class InstitutionBrandingPageRead(BaseModel):
    form: InstitutionBrandingFormValues
    primary_logo: BrandingPrimaryLogoPanel
    color_fields: list[BrandingColorField]
    document_templates: list[BrandingDocumentTemplateRow]
    template_count_label: str
    templates_manage_href: str
    brand_assets: list[BrandingAssetRow]
    preview_items: list[BrandingPreviewItem]
    preview_portal_href: str
    footer_note: str
    has_draft: bool = False
    generated_at: datetime


class InstitutionBrandingDraftUpdate(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


class InstitutionBrandingAssetRead(BaseModel):
    asset_key: str
    file_id: str | None
    file_name: str | None
    uploaded_at: datetime | None


class AcademicYearTableRow(BaseModel):
    year_id: str
    label: str
    start_label: str
    end_label: str
    semesters_label: str
    status_code: str
    status_label: str
    status_tone: str


class AcademicYearManagementTableRow(BaseModel):
    year_id: str
    label: str
    start_label: str
    end_label: str
    student_count: int
    status_code: str
    status_label: str
    status_tone: str
    detail_href: str


class AcademicYearClosingChecklistItem(BaseModel):
    key: str
    title: str
    detail: str | None = None
    completed: bool


class AcademicYearRuleToggle(BaseModel):
    key: str
    title: str
    description: str
    enabled: bool


class AcademicYearCreateFormField(BaseModel):
    key: str
    label: str
    required: bool = False
    field_type: str = "text"


class AcademicYearCreateFormOption(BaseModel):
    value: str
    label: str


class YearsSemestersSubNavItem(BaseModel):
    key: str
    label: str
    href: str
    active: bool


class AcademicYearManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    close_current_year_label: str
    close_current_year_enabled: bool
    close_target_year_label: str | None = None
    new_academic_year_label: str
    new_academic_year_href: str
    academic_years_table_title: str
    table_headers: list[str]
    academic_years: list[AcademicYearManagementTableRow]
    academic_year_count_label: str
    page: int
    page_size: int
    total_pages: int
    total_years: int
    create_section_title: str
    create_form_note: str
    create_submit_label: str
    cancel_label: str
    create_fields: list[AcademicYearCreateFormField]
    copy_from_options: list[AcademicYearCreateFormOption]
    semester_count_options: list[AcademicYearCreateFormOption]
    checklist_title: str
    checklist_items: list[AcademicYearClosingChecklistItem]
    rules_section_title: str
    rules: list[AcademicYearRuleToggle]
    sub_nav: list[YearsSemestersSubNavItem]
    semesters_button_label: str
    semesters_button_href: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AcademicYearManagementCreate(BaseModel):
    label: str = Field(min_length=4, max_length=64)
    copy_from_year_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    semester_count: int = Field(default=2, ge=1, le=4)
    admission_intake_opens: date | None = None
    summer_term_start: date | None = None
    summer_term_end: date | None = None
    year_end_closing: date | None = None

    @model_validator(mode="after")
    def _validate_date_order(self) -> "AcademicYearManagementCreate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("End date must be on or after the start date.")
        return self


class AcademicYearManagementRulesSave(BaseModel):
    only_one_current_year: bool = True
    lock_closed_years: bool = True


class AcademicYearWizardStep(BaseModel):
    key: str
    label: str
    step_number: int
    status: str = "pending"


class AcademicYearWizardFormSection(BaseModel):
    key: str
    title: str


class AcademicYearWizardSummaryItem(BaseModel):
    key: str
    label: str
    value: str


class AcademicYearWizardFormValues(BaseModel):
    label: str = ""
    copy_from_year_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    admission_intake_opens: str | None = None
    summer_term_start: str | None = None
    summer_term_end: str | None = None
    year_end_closing: str | None = None
    semester_count: str = "2"


class NewAcademicYearWizardPageRead(BaseModel):
    draft_id: str
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    save_draft_label: str
    continue_label: str
    finalize_label: str
    current_step_key: str
    step_position_label: str
    steps: list[AcademicYearWizardStep]
    sections: list[AcademicYearWizardFormSection]
    field_meta: list[InstitutionFieldMeta]
    copy_from_options: list[AcademicYearCreateFormOption]
    semester_count_options: list[AcademicYearCreateFormOption]
    form: AcademicYearWizardFormValues
    summary_title: str
    summary_items: list[AcademicYearWizardSummaryItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AcademicYearWizardDraftUpdate(BaseModel):
    draft_id: str
    step_key: str | None = None
    advance: bool = False
    finalize: bool = False
    values: dict[str, Any] = Field(default_factory=dict)


class NewAcademicYearWizardSaveResult(BaseModel):
    page: NewAcademicYearWizardPageRead | None = None
    created_year_id: str | None = None
    details_href: str | None = None


class AcademicYearDetailsKeyValueRow(BaseModel):
    key: str
    label: str
    value: str


class AcademicYearDetailsTermRow(BaseModel):
    term_id: str
    label: str
    period_label: str
    status_label: str
    status_tone: str


class AcademicYearDetailsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    year_id: str
    year_label: str
    status_label: str
    status_tone: str
    is_current: bool
    overview_section_title: str
    overview_rows: list[AcademicYearDetailsKeyValueRow]
    terms_section_title: str
    terms_table_headers: list[str]
    term_rows: list[AcademicYearDetailsTermRow]
    manage_semesters_label: str
    manage_semesters_href: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class SemesterManagementTableRow(BaseModel):
    term_id: str
    label: str
    period_label: str
    week_label: str
    course_count: int
    status_code: str
    status_label: str
    status_tone: str
    is_current: bool


class SemesterSettingsForm(BaseModel):
    teaching_starts: date | None = None
    last_instruction_day: date | None = None
    mid_semester_exam_date: date | None = None
    end_semester_exam_date: date | None = None
    course_registration_opens: date | None = None
    add_drop_deadline: date | None = None


class SemesterSettingsFieldMeta(BaseModel):
    key: str
    label: str
    required: bool = False


class SemesterProgressItem(BaseModel):
    key: str
    label: str
    progress_percent: int


class SemesterLinkedItem(BaseModel):
    key: str
    title: str
    subtitle: str
    status_label: str
    status_tone: str


class SemesterManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    new_semester_label: str
    year_filter_options: list[AcademicYearCreateFormOption]
    selected_academic_year_id: str | None
    selected_academic_year_label: str
    semesters_panel_title: str
    table_headers: list[str]
    semester_rows: list[SemesterManagementTableRow]
    semester_count_label: str
    manage_terms_href: str
    manage_terms_label: str
    selected_term_id: str | None
    settings_panel_title: str
    settings_form: SemesterSettingsForm | None
    settings_field_meta: list[SemesterSettingsFieldMeta]
    save_label: str
    cancel_label: str
    settings_form_note: str
    progress_section_title: str
    progress_items: list[SemesterProgressItem]
    linked_section_title: str
    linked_items: list[SemesterLinkedItem]
    sub_nav: list[YearsSemestersSubNavItem]
    years_button_label: str
    years_button_href: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class SemesterManagementSettingsSave(BaseModel):
    term_id: str
    settings: SemesterSettingsForm


class SemesterManagementCreate(BaseModel):
    academic_year_id: str
    label: str = Field(min_length=2, max_length=64)
    term_code: str | None = Field(default=None, max_length=32)


class ProgrammeManagementTableRow(BaseModel):
    programme_id: str
    programme_name: str
    programme_code: str
    level_label: str
    department_label: str
    duration_label: str
    intake_label: str
    regulation_label: str
    status_code: str
    status_label: str
    status_tone: str
    detail_href: str


class ProgrammeManagementCreate(BaseModel):
    programme_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    short_name: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=2000)
    department_id: str | None = None
    programme_level: str | None = Field(default=None, max_length=32)
    regulation_code: str | None = Field(default=None, max_length=32)
    mode_of_study: str = Field(default="full_time", max_length=32)
    approved_intake: int | None = Field(default=None, ge=0, le=9999)
    entry_qualification: str | None = Field(default=None, max_length=500)
    duration_semesters: int = Field(default=8, ge=1, le=20)
    credits_required: float = Field(default=160, ge=0)


class ProgrammeManagementCreateResult(BaseModel):
    programme_id: str
    detail_href: str
    message: str = "Programme created"


class ProgrammeDetailsSummaryRow(BaseModel):
    label: str
    value: str


class AcademicYearSemesterForm(BaseModel):
    odd_semester_start: date | None = None
    odd_semester_end: date | None = None
    even_semester_start: date | None = None
    even_semester_end: date | None = None
    summer_term_start: date | None = None
    summer_term_end: date | None = None
    year_end_closing: date | None = None

    @model_validator(mode="before")
    @classmethod
    def empty_strings_to_none(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        for key in (
            "odd_semester_start",
            "odd_semester_end",
            "even_semester_start",
            "even_semester_end",
            "summer_term_start",
            "summer_term_end",
            "year_end_closing",
        ):
            if key in out and (out[key] == "" or out[key] is None):
                out[key] = None
        return out


class AcademicYearSemesterFieldMeta(BaseModel):
    key: str
    label: str
    required: bool = False
    field_type: str = "date"


class AcademicYearTimelineItem(BaseModel):
    item_id: str
    title: str
    date_label: str
    status_code: str
    status_label: str
    status_tone: str


class AcademicYearLinkedConfig(BaseModel):
    key: str
    title: str
    description: str
    href: str
    icon_slug: str


class ProgrammeDetailsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    programme_name: str
    programme_code: str
    status_label: str
    status_tone: str
    back_href: str
    edit_note: str
    summary_rows: list[ProgrammeDetailsSummaryRow]
    description: str | None
    checklist_title: str
    checklist_items: list[AcademicYearRuleToggle]
    linked_title: str
    linked_items: list[AcademicYearLinkedConfig]
    generated_at: datetime


class AcademicYearConfigurationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    copy_from_previous_label: str
    new_academic_year_label: str
    save_label: str
    cancel_label: str
    academic_years_table_title: str
    archive_view_href: str
    archive_view_label: str
    academic_year_count_label: str
    academic_years: list[AcademicYearTableRow]
    selected_year_id: str | None
    semester_section_title: str
    semester_form: AcademicYearSemesterForm | None
    semester_field_meta: list[AcademicYearSemesterFieldMeta]
    year_timeline_title: str
    timeline: list[AcademicYearTimelineItem]
    linked_configuration_title: str
    linked_configuration: list[AcademicYearLinkedConfig]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AcademicYearConfigurationSave(BaseModel):
    semester_form: AcademicYearSemesterForm


class InstitutionPolicyFilterOption(BaseModel):
    value: str
    label: str


class InstitutionPolicyRow(BaseModel):
    policy_id: str
    title: str
    audience_label: str
    version_label: str
    effective_label: str
    status_code: str
    status_label: str
    status_tone: str


class InstitutionPolicySelectedDetail(BaseModel):
    policy_id: str
    title: str
    open_href: str
    open_label: str
    owner_label: str | None = None
    approved_by_label: str | None = None
    acknowledgement_requirement: str | None = None
    acknowledgement_progress_label: str | None = None


class InstitutionPolicyReviewItem(BaseModel):
    review_id: str
    title: str
    subtitle: str
    status_code: str
    status_label: str
    status_tone: str


class InstitutionPolicyCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=64)
    audience: str = Field(min_length=2, max_length=64)
    version_label: str = Field(default="1.0", min_length=1, max_length=32)
    effective_from: date | None = None
    status: str = Field(default="draft", max_length=32)
    owner_label: str | None = Field(default=None, max_length=200)
    approved_by_label: str | None = Field(default=None, max_length=300)
    acknowledgement_requirement: str | None = Field(default=None, max_length=200)


class InstitutionPolicyCreateResult(BaseModel):
    policy_id: str
    title: str
    message: str = "Policy created successfully"


class PoliciesPagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    page_numbers: list[int]
    has_previous: bool
    has_next: bool


class ProgrammeManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    add_programme_label: str
    new_programme_href: str
    create_level_options: list[AcademicYearCreateFormOption]
    create_regulation_options: list[AcademicYearCreateFormOption]
    create_mode_options: list[AcademicYearCreateFormOption]
    search_placeholder: str
    level_filter_label: str
    department_filter_label: str
    regulation_filter_label: str
    status_filter_label: str
    level_options: list[InstitutionPolicyFilterOption]
    department_options: list[InstitutionPolicyFilterOption]
    regulation_options: list[InstitutionPolicyFilterOption]
    status_options: list[InstitutionPolicyFilterOption]
    programmes_section_title: str
    programmes_count_label: str
    table_headers: list[str]
    programmes: list[ProgrammeManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    create_section_title: str
    create_form_note: str
    create_submit_label: str
    create_cancel_label: str
    create_fields: list[AcademicYearCreateFormField]
    create_department_options: list[AcademicYearCreateFormOption]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class SubjectManagementTableRow(BaseModel):
    course_id: str
    subject_name: str
    subject_code: str
    department_label: str
    type_label: str
    credits_label: str
    semester_label: str
    status_code: str
    status_label: str
    status_tone: str
    configuration_href: str


class SubjectManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    import_label: str
    add_subject_label: str
    add_subject_href: str
    search_placeholder: str
    department_filter_label: str
    type_filter_label: str
    regulation_filter_label: str
    semester_filter_label: str
    department_options: list[InstitutionPolicyFilterOption]
    type_options: list[InstitutionPolicyFilterOption]
    regulation_options: list[InstitutionPolicyFilterOption]
    semester_options: list[InstitutionPolicyFilterOption]
    subjects_section_title: str
    subjects_count_label: str
    table_headers: list[str]
    subjects: list[SubjectManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    sub_nav: list[YearsSemestersSubNavItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class CurriculumSemesterTab(BaseModel):
    semester_number: int
    tab_label: str
    is_selected: bool = False


class CurriculumManagementCourseRow(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    type_label: str
    ltp_label: str
    credits_label: str
    status_code: str
    status_label: str
    status_tone: str
    configuration_href: str


class CurriculumCreditCategoryRow(BaseModel):
    category_key: str
    category_label: str
    credits: float
    share_pct: float | None = None


class CurriculumSummaryField(BaseModel):
    key: str
    label: str
    value: str


class CurriculumManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    download_pdf_label: str
    subjects_button_label: str
    subjects_button_href: str
    edit_curriculum_label: str
    edit_curriculum_href: str
    programme_options: list[AcademicYearCreateFormOption]
    selected_programme_id: str | None
    selected_programme_label: str
    regulation_label: str
    semester_tabs: list[CurriculumSemesterTab]
    selected_semester: int
    courses_panel_title: str
    courses_panel_meta: str
    table_headers: list[str]
    courses: list[CurriculumManagementCourseRow]
    approval_footer_label: str
    version_history_label: str
    version_history_href: str
    credits_panel_title: str
    credit_categories: list[CurriculumCreditCategoryRow]
    summary_panel_title: str
    summary_fields: list[CurriculumSummaryField]
    sub_nav: list[YearsSemestersSubNavItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class CourseConfigurationPrerequisiteRow(BaseModel):
    prerequisite_id: str
    title: str
    semester_hint: str | None = None
    requirement_type: str
    requirement_label: str
    requirement_tone: str


class CourseConfigurationOfferedRow(BaseModel):
    programme_label: str
    detail_label: str


class CourseConfigurationForm(BaseModel):
    course_id: str | None = None
    course_code: str
    course_title: str
    department_id: str | None = None
    course_type: str | None = None
    semester_number: int | None = None
    regulation_label: str | None = None
    description: str | None = None
    lecture_hours: int = 0
    tutorial_hours: int = 0
    practical_hours: int = 0
    credit_units: float = 0
    internal_assessment_label: str | None = None
    end_semester_exam_label: str | None = None
    exam_duration_label: str | None = None
    exam_type_label: str | None = None


class CourseConfigurationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    status_label: str
    status_tone: str
    cancel_label: str
    save_label: str
    form_note: str
    details_section_title: str
    hours_section_title: str
    assessment_section_title: str
    prerequisites_section_title: str
    offered_section_title: str
    outcomes_section_title: str
    outcomes_edit_label: str
    outcomes_edit_href: str
    field_meta: list[AcademicYearCreateFormField]
    department_options: list[AcademicYearCreateFormOption]
    course_type_options: list[AcademicYearCreateFormOption]
    semester_options: list[AcademicYearCreateFormOption]
    regulation_options: list[AcademicYearCreateFormOption]
    exam_duration_options: list[AcademicYearCreateFormOption]
    exam_type_options: list[AcademicYearCreateFormOption]
    form: CourseConfigurationForm
    prerequisites: list[CourseConfigurationPrerequisiteRow]
    offered_to: list[CourseConfigurationOfferedRow]
    outcomes_text: str | None = None
    sub_nav: list[YearsSemestersSubNavItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class CourseConfigurationSave(BaseModel):
    course_id: str | None = None
    form: CourseConfigurationForm


class CreditLevelRequirementRow(BaseModel):
    level_key: str
    level_label: str
    min_graduate_credits: float
    max_per_semester: float
    min_per_semester: float
    status_label: str
    status_tone: str


class CreditCalculationField(BaseModel):
    key: str
    label: str
    value: str
    field_type: str = "text"
    options: list[AcademicYearCreateFormOption] = Field(default_factory=list)


class CreditLimitStatItem(BaseModel):
    key: str
    title: str
    description: str
    count: int
    count_tone: str


class CreditConfigurationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    reset_label: str
    save_rules_label: str
    cancel_label: str
    requirements_section_title: str
    requirements_table_headers: list[str]
    requirements_footer_label: str
    requirements_edit_label: str
    requirements_edit_href: str
    level_rows: list[CreditLevelRequirementRow]
    calculation_section_title: str
    calculation_fields: list[CreditCalculationField]
    rules_section_title: str
    rules: list[AcademicYearRuleToggle]
    limits_section_title: str
    limit_stats: list[CreditLimitStatItem]
    form_note: str
    sub_nav: list[YearsSemestersSubNavItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class CreditConfigurationSave(BaseModel):
    calculation: dict[str, str]
    rules: dict[str, bool]
    level_rows: list[CreditLevelRequirementRow] = Field(default_factory=list)


class GradingScaleRow(BaseModel):
    grade_id: str
    grade: str
    grade_point: float
    marks_range_label: str
    description: str


class GradingClassificationRow(BaseModel):
    class_id: str
    class_label: str
    cgpa_label: str
    condition_label: str


class GradingCalculationField(BaseModel):
    key: str
    label: str
    value: str
    required: bool = False
    field_type: str = "select"
    options: list[AcademicYearCreateFormOption]


class GradingSystemConfigurationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    preview_transcript_label: str
    preview_transcript_href: str
    save_grading_label: str
    cancel_label: str
    grade_scale_title: str
    grade_table_headers: list[str]
    grade_rows: list[GradingScaleRow]
    grade_scale_footer: str
    add_grade_label: str
    classification_section_title: str
    classification_table_headers: list[str]
    classification_rows: list[GradingClassificationRow]
    classification_footer: str
    classification_edit_label: str
    calculation_section_title: str
    calculation_fields: list[GradingCalculationField]
    rules_section_title: str
    rules: list[AcademicYearRuleToggle]
    form_note: str
    sub_nav: list[YearsSemestersSubNavItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class GradingSystemConfigurationSave(BaseModel):
    grade_rows: list[GradingScaleRow]
    classification_rows: list[GradingClassificationRow]
    calculation: dict[str, str]
    rules: dict[str, bool]


class RegulationManagementTableRow(BaseModel):
    regulation_id: str
    regulation_code: str
    regulation_label: str
    effective_from_label: str
    batch_range_label: str
    student_count: int
    programme_count: int
    status_code: str
    status_label: str
    status_tone: str
    is_selected: bool = False


class RegulationHighlightRow(BaseModel):
    key: str
    label: str
    value: str


class RegulationPhaseOutStepRow(BaseModel):
    step_id: str
    title: str
    date_label: str
    is_active: bool = False


class RegulationDocumentRow(BaseModel):
    document_id: str
    title: str
    size_label: str
    download_label: str
    download_href: str | None = None


class RegulationManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    compare_label: str
    compare_href: str
    new_regulation_label: str
    regulations_section_title: str
    regulations_count_label: str
    table_headers: list[str]
    regulations: list[RegulationManagementTableRow]
    view_documents_label: str
    view_documents_href: str
    selected_regulation_code: str
    highlights_section_title: str
    highlight_rows: list[RegulationHighlightRow]
    phase_out_section_title: str
    phase_out_steps: list[RegulationPhaseOutStepRow]
    documents_section_title: str
    documents: list[RegulationDocumentRow]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class RegulationManagementCreate(BaseModel):
    regulation_code: str = Field(min_length=2, max_length=32)
    display_label: str | None = Field(default=None, max_length=64)


class AcademicCalendarViewTab(BaseModel):
    key: str
    label: str
    active: bool = False


class AcademicCalendarEventTableRow(BaseModel):
    event_id: str
    title: str
    date_label: str
    type_label: str
    audience_label: str
    status_label: str
    status_tone: str


class AcademicCalendarTypeStatRow(BaseModel):
    type_label: str
    count: int
    bar_percent: float = Field(ge=0, le=100)


class AcademicCalendarAddEventForm(BaseModel):
    title_meta: InstitutionFieldMeta
    title_placeholder: str
    type_meta: InstitutionFieldMeta
    type_options: list[InstitutionFieldOption]
    type_default_value: str
    from_meta: InstitutionFieldMeta
    to_meta: InstitutionFieldMeta
    audience_meta: InstitutionFieldMeta
    audience_options: list[InstitutionFieldOption]
    audience_default_value: str
    submit_label: str


class AcademicCalendarConfigurationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    publish_button_label: str
    add_event_button_label: str
    can_publish: bool
    primary_calendar_id: str | None
    active_view: str
    view_tabs: list[AcademicCalendarViewTab]
    list_panel_title: str
    table_headers: list[str]
    event_rows: list[AcademicCalendarEventTableRow]
    year_event_count_label: str
    pagination: PoliciesPagination
    add_event_form: AcademicCalendarAddEventForm
    type_stats_title: str
    type_stats: list[AcademicCalendarTypeStatRow]
    selected_academic_year_id: str
    selected_term_id: str | None = None
    sub_nav: list[YearsSemestersSubNavItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AcademicCalendarAddEventSave(BaseModel):
    academic_year_id: str
    title: str = Field(min_length=2, max_length=200)
    event_type: str = Field(min_length=2, max_length=32)
    from_date: date
    to_date: date | None = None
    audience: str = Field(min_length=2, max_length=32)


class AcademicCalendarPublishSave(BaseModel):
    academic_year_id: str
    calendar_id: str | None = None


class BatchSectionBatchTab(BaseModel):
    batch_year: str
    label: str
    active: bool = False


class BatchSectionTableRow(BaseModel):
    section_id: str
    section_label: str
    advisor_label: str
    capacity_label: str
    allocated_count: int | None
    room_label: str
    status_label: str
    status_tone: str


class BatchSectionOverviewRow(BaseModel):
    batch_label: str
    seats_filled_label: str
    bar_percent: float


class BatchSectionPendingTaskRow(BaseModel):
    task_id: str
    title: str
    subtitle: str
    action_label: str
    action_kind: str
    action_href: str | None = None
    status_tone: str


class BatchSectionAllocationField(BaseModel):
    key: str
    label: str
    required: bool = False
    field_type: str = "text"
    options: list[InstitutionFieldOption] = Field(default_factory=list)
    value: str


class BatchSectionAllocationRulesForm(BaseModel):
    section_title: str
    fields: list[BatchSectionAllocationField]


class BatchSectionConfigurationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    auto_allocate_label: str
    add_section_label: str
    batch_tabs: list[BatchSectionBatchTab]
    selected_batch_year: str
    selected_programme_code: str
    programme_options: list[InstitutionFieldOption]
    sections_panel_title: str
    table_headers: list[str]
    section_rows: list[BatchSectionTableRow]
    section_summary_label: str
    pagination: PoliciesPagination
    allocation_rules: BatchSectionAllocationRulesForm
    overview_title: str
    overview_rows: list[BatchSectionOverviewRow]
    pending_tasks_title: str
    pending_tasks: list[BatchSectionPendingTaskRow]
    footer_note: str
    cancel_label: str
    save_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class BatchSectionAllocationRulesSave(BaseModel):
    default_section_size: int = Field(ge=1, le=500)
    allocation_method: str = Field(min_length=2, max_length=32)
    balance_by_gender: str = Field(min_length=2, max_length=16)
    lateral_entry_handling: str = Field(min_length=2, max_length=32)


class BatchSectionAddSectionSave(BaseModel):
    programme_code: str = Field(min_length=2, max_length=32)
    batch_label: str = Field(min_length=2, max_length=64)
    section_code: str = Field(min_length=1, max_length=16)
    section_name: str = Field(min_length=1, max_length=120)
    capacity: int = Field(default=60, ge=1, le=500)
    room_label: str | None = Field(default=None, max_length=64)


class BatchSectionAutoAllocateSave(BaseModel):
    programme_code: str = Field(min_length=2, max_length=32)
    batch_label: str = Field(min_length=2, max_length=64)


class InstitutionCalendarHolidayRow(BaseModel):
    holiday_id: str
    title: str
    date_label: str
    type_label: str
    applies_to_label: str


class InstitutionHolidayCreate(BaseModel):
    academic_year_id: str
    title: str = Field(min_length=2, max_length=200)
    start_date: date
    end_date: date | None = None
    holiday_type: str = Field(default="institution", max_length=32)
    applies_to: str = Field(default="all", max_length=32)


class InstitutionHolidayCreateResult(BaseModel):
    holiday_id: str
    title: str
    message: str = "Holiday added successfully"


class InstitutionCalendarFormValues(BaseModel):
    working_days: str
    saturday_pattern: str
    day_start: str
    day_end: str
    publish_student_portal: bool = True
    publish_parent_app: bool = True
    send_reminders_day_before: bool = True
    sync_external_calendars: bool = False


class InstitutionCalendarToggleRule(BaseModel):
    key: str
    label: str
    description: str | None = None
    enabled: bool = False


class InstitutionCalendarTimeOption(BaseModel):
    value: str
    label: str


class InstitutionCalendarSettingsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    import_holidays_label: str
    save_label: str
    cancel_label: str
    holidays_section_title: str
    add_holiday_label: str
    add_holiday_href: str
    add_holiday_dialog_title: str = "Add holiday"
    add_holiday_dialog_subtitle: str = "Register a holiday for the selected academic year"
    create_holiday_save_label: str = "Add holiday"
    create_holiday_cancel_label: str = "Cancel"
    create_holiday_type_options: list[InstitutionFieldOption] = Field(default_factory=list)
    create_holiday_applies_options: list[InstitutionFieldOption] = Field(default_factory=list)
    holiday_table_headers: list[str]
    holidays: list[InstitutionCalendarHolidayRow]
    holiday_count_label: str
    pagination: PoliciesPagination
    selected_academic_year_id: str | None
    working_week_title: str
    publishing_title: str
    form: InstitutionCalendarFormValues
    working_days_options: list[InstitutionFieldOption]
    saturday_pattern_options: list[InstitutionFieldOption]
    time_options: list[InstitutionCalendarTimeOption]
    working_days_meta: InstitutionFieldMeta
    saturday_pattern_meta: InstitutionFieldMeta
    day_start_meta: InstitutionFieldMeta
    day_end_meta: InstitutionFieldMeta
    publishing_toggles: list[InstitutionCalendarToggleRule]
    footer_note: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class InstitutionCalendarSettingsSave(BaseModel):
    form: InstitutionCalendarFormValues
    page: int = 1
    academic_year_id: str | None = None


class ConfigurationChangeRow(BaseModel):
    change_id: str
    change_summary: str
    setting_label: str
    changed_by_label: str
    when_label: str
    status_code: str
    status_label: str
    status_tone: str


class ConfigurationChangeDetail(BaseModel):
    change_id: str
    setting_line: str
    previous_value: str | None = None
    new_value: str | None = None
    approved_by_label: str | None = None
    reason_line: str | None = None
    applies_to_line: str | None = None
    ip_line: str | None = None
    open_href: str
    open_label: str


class ConfigurationAreaSummary(BaseModel):
    area_key: str
    title: str
    count: int
    progress_percent: int


class ConfigurationHistoryFilterOption(BaseModel):
    value: str
    label: str


class UserDashboardFilterOption(BaseModel):
    value: str
    label: str


class UserDashboardKpi(BaseModel):
    key: str
    label: str
    value: str
    hint_line: str
    hint_tone: str


class UserDashboardDailyPoint(BaseModel):
    date_label: str
    active_users: int


class UserDashboardRoleBar(BaseModel):
    key: str
    label: str
    count: int
    progress_percent: int


class UserDashboardRecentRow(BaseModel):
    user_id: str
    user_name: str
    role_label: str
    department_label: str
    created_label: str
    status_code: str
    status_label: str
    status_tone: str
    detail_href: str


class UserDashboardSecurityItem(BaseModel):
    key: str
    title: str
    description: str
    count: int
    tone: str


class UserListFilterOption(BaseModel):
    value: str
    label: str


class UserListTableRow(BaseModel):
    user_id: str
    full_name: str
    public_id: str
    role_label: str
    department_label: str
    last_login_label: str
    mfa_label: str
    mfa_tone: str
    status_code: str
    status_label: str
    status_tone: str
    detail_href: str


class UserAllUsersListPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    create_user_label: str
    create_user_href: str
    bulk_actions_label: str
    bulk_actions_href: str
    search_placeholder: str
    role_filter_label: str
    department_filter_label: str
    status_filter_label: str
    role_options: list[UserListFilterOption]
    department_options: list[UserListFilterOption]
    status_options: list[UserListFilterOption]
    users_section_title: str
    accounts_count_label: str
    table_headers: list[str]
    users: list[UserListTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class UserDetailsProfileBadge(BaseModel):
    key: str
    label: str
    tone: str


class UserDetailsAccountField(BaseModel):
    key: str
    label: str
    value: str
    tone: str | None = None


class UserDetailsAssignedRoleRow(BaseModel):
    role_name: str
    scope_label: str
    assigned_by_label: str
    since_label: str


class UserDetailsPermissionBar(BaseModel):
    key: str
    label: str
    description: str
    progress_percent: int


class UserDetailsActivityItem(BaseModel):
    key: str
    title: str
    subtitle: str
    tone: str


class CreateNewUserWizardStep(BaseModel):
    key: str
    label: str
    step_number: int


class CreateNewUserFormSection(BaseModel):
    key: str
    title: str


class CreateNewUserToggleSetting(BaseModel):
    key: str
    label: str
    description: str | None = None
    default_on: bool = True


class CreateNewUserValidationCheck(BaseModel):
    key: str
    title: str
    subtitle: str
    status_code: str
    status_label: str
    tone: str


class CreateNewUserReviewLine(BaseModel):
    label: str
    value: str


class CreateNewUserFormValues(BaseModel):
    first_name: str = ""
    last_name: str = ""
    official_email: str = ""
    mobile_number: str = ""
    public_id: str = ""
    joining_date: date | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    user_type: str = "teaching_staff"
    department_id: str | None = None
    designation: str | None = None
    campus_id: str | None = None
    institution_role_id: str | None = None
    initial_password: str = ""
    send_invitation_email: bool = False
    send_sms_login_link: bool = False
    require_mfa_first_login: bool = True
    allow_sso_login: bool = True
    previous_school: str = ""
    programme_code: str = ""
    batch_label: str = ""
    section_code: str = ""
    permanent_address: str = ""
    current_address: str = ""
    guardian_name: str = ""
    guardian_relationship: str = ""
    guardian_mobile: str = ""
    blood_group: str | None = None
    nationality: str | None = None
    specialization: str = ""
    experience_years: str = ""
    profile_photo_ref: str | None = None
    identity_document_ref: str | None = None
    supporting_document_ref: str | None = None


class CreateNewUserPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    cancel_href: str
    cancel_label: str
    create_invite_label: str
    save_draft_label: str
    next_step_prefix: str
    audit_footer_note: str
    current_step_key: str
    steps: list[CreateNewUserWizardStep]
    sections: list[CreateNewUserFormSection]
    field_meta: list[InstitutionFieldMeta]
    gender_options: list[InstitutionFieldOption]
    user_type_options: list[InstitutionFieldOption]
    department_options: list[InstitutionFieldOption]
    designation_options: list[InstitutionFieldOption]
    campus_options: list[InstitutionFieldOption]
    institution_role_options: list[InstitutionFieldOption]
    student_field_meta: list[InstitutionFieldMeta] = Field(default_factory=list)
    staff_field_meta: list[InstitutionFieldMeta] = Field(default_factory=list)
    document_field_meta: list[InstitutionFieldMeta] = Field(default_factory=list)
    guardian_relationship_options: list[InstitutionFieldOption] = Field(default_factory=list)
    blood_group_options: list[InstitutionFieldOption] = Field(default_factory=list)
    nationality_options: list[InstitutionFieldOption] = Field(default_factory=list)
    invitation_settings: list[CreateNewUserToggleSetting]
    validation_checks: list[CreateNewUserValidationCheck]
    review_lines: list[CreateNewUserReviewLine] = Field(default_factory=list)
    form: CreateNewUserFormValues
    has_draft: bool = False
    footer_disclaimer: str
    generated_at: datetime


class CreateNewUserDraftUpdate(BaseModel):
    step_key: str | None = None
    values: dict[str, Any] = Field(default_factory=dict)


class CreateNewUserValidatePayload(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


class CreateNewUserValidateResponse(BaseModel):
    validation_checks: list[CreateNewUserValidationCheck]
    review_lines: list[CreateNewUserReviewLine]


class CreateNewUserSubmitPayload(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)
    finalize: bool = True


class CreateNewUserSubmitResponse(BaseModel):
    status: str
    message: str
    user_id: str | None = None
    invitation_id: str | None = None
    detail_href: str | None = None
    accept_token: str | None = None


class CreateNewUserProvisioningUploadRead(BaseModel):
    file_id: str
    file_name: str
    kind: str


class EditUserInformationFormValues(BaseModel):
    full_name: str
    display_name: str | None = None
    official_email: str
    personal_email: str | None = None
    mobile_number: str | None = None
    alternate_phone: str | None = None
    department_id: str | None = None
    designation: str | None = None
    username: str
    login_method: str
    mfa_requirement: str
    session_timeout_minutes: int


class EditUserAccountStatusCard(BaseModel):
    status_label: str
    status_tone: str
    created_label: str
    last_modified_label: str


class EditUserDangerAction(BaseModel):
    key: str
    title: str
    description: str
    href: str
    action_label: str
    icon: str
    api_action: str | None = None


class EditUserInformationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    detail_href: str
    discard_label: str
    save_label: str
    cancel_label: str
    profile_section_title: str
    login_section_title: str
    account_status_section_title: str
    danger_zone_title: str
    profile_field_meta: list[InstitutionFieldMeta]
    login_field_meta: list[InstitutionFieldMeta]
    department_options: list[InstitutionFieldOption]
    designation_options: list[InstitutionFieldOption]
    login_method_options: list[InstitutionFieldOption]
    mfa_options: list[InstitutionFieldOption]
    session_timeout_options: list[InstitutionFieldOption]
    account_status: EditUserAccountStatusCard
    danger_actions: list[EditUserDangerAction]
    form: EditUserInformationFormValues
    audit_footer_note: str
    footer_disclaimer: str
    footer_snapshot_label: str
    user_id: str
    generated_at: datetime


class EditUserInformationSavePayload(BaseModel):
    user_id: str
    values: dict[str, Any] = Field(default_factory=dict)


class BulkUserInvitationWizardStep(BaseModel):
    key: str
    label: str
    step_number: int


class BulkUserInvitationToggle(BaseModel):
    key: str
    label: str
    description: str
    default_on: bool = True


class BulkUserInvitationSummaryStat(BaseModel):
    key: str
    label: str
    count: int
    description: str
    tone: str


class BulkUserInvitationPreviewRow(BaseModel):
    row_id: str
    full_name: str
    email: str
    role_label: str
    department_label: str
    status_code: str
    status_label: str
    status_tone: str


class BulkUserInvitationPagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    page_numbers: list[int]
    has_previous: bool
    has_next: bool
    showing_label: str


class BulkUserInvitationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    download_template_label: str
    send_invitations_label: str
    cancel_href: str
    cancel_label: str
    audit_footer_note: str
    back_label: str
    fix_errors_label: str
    send_ready_label: str
    browse_files_label: str
    upload_drop_hint: str
    preview_section_title: str
    preview_summary_label: str | None
    validation_summary_title: str
    invitation_options_title: str
    table_headers: list[str]
    current_step_key: str
    steps: list[BulkUserInvitationWizardStep]
    file_name: str | None
    file_meta_label: str | None
    summary_stats: list[BulkUserInvitationSummaryStat]
    invitation_toggles: list[BulkUserInvitationToggle]
    preview_rows: list[BulkUserInvitationPreviewRow]
    pagination: BulkUserInvitationPagination
    ready_to_send_count: int
    footer_disclaimer: str
    generated_at: datetime


class BulkUserInvitationUploadPayload(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_content: str = Field(min_length=1, description="CSV text content")
    file_size_bytes: int | None = None


class BulkUserInvitationStepPayload(BaseModel):
    step_key: str | None = None
    skip_rows_with_errors: bool | None = None
    require_mfa_first_login: bool | None = None
    use_admin_password: bool | None = None


class BulkUserInvitationSendResponse(BaseModel):
    status: str
    message: str
    sent_count: int
    skipped_count: int
    href: str


class RoleManagementTableRow(BaseModel):
    role_id: str
    role_name: str
    role_code: str
    type_label: str
    users_count: int
    modules_label: str
    last_changed_label: str
    status_code: str
    status_label: str
    status_tone: str
    detail_href: str


class RoleManagementDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    compare_roles_label: str
    compare_roles_href: str
    create_role_label: str
    create_role_href: str
    kpis: list[UserDashboardKpi]
    roles_section_title: str
    roles_count_label: str
    table_headers: list[str]
    roles: list[RoleManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class CreateEditRoleFormValues(BaseModel):
    name: str = ""
    role_code: str = ""
    base_role: str
    scope: str
    description: str | None = None
    require_mfa: bool = False
    restrict_campus_network: bool = False
    time_bound_access: bool = False


class CreateEditRolePermissionCell(BaseModel):
    column_key: str
    applicable: bool
    checked: bool


class CreateEditRolePermissionRow(BaseModel):
    row_key: str
    label: str
    cells: list[CreateEditRolePermissionCell]


class CreateEditRolePermissionGroup(BaseModel):
    group_key: str
    group_label: str
    rows: list[CreateEditRolePermissionRow]


class CreateEditRoleAccessToggle(BaseModel):
    key: str
    label: str
    description: str
    checked: bool


class CreateEditRoleAssignedUser(BaseModel):
    user_id: str
    name: str
    subtitle: str
    detail_href: str


class CreateEditRolePermissionToggle(BaseModel):
    row_key: str
    column_key: str
    checked: bool


class CreateEditRoleSavePayload(BaseModel):
    role_id: str | None = None
    form: CreateEditRoleFormValues
    permission_toggles: list[CreateEditRolePermissionToggle]


class CreateEditRolePageRead(BaseModel):
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    cancel_href: str
    cancel_label: str
    save_label: str
    type_badge_label: str
    type_badge_tone: str
    role_details_section_title: str
    module_permissions_section_title: str
    access_rules_section_title: str
    users_with_role_section_title: str
    assign_users_label: str
    assign_users_href: str
    permission_columns: list[str]
    permission_groups: list[CreateEditRolePermissionGroup]
    access_toggles: list[CreateEditRoleAccessToggle]
    assigned_users: list[CreateEditRoleAssignedUser]
    more_users_label: str | None
    base_role_options: list[InstitutionFieldOption]
    scope_options: list[InstitutionFieldOption]
    role_details_field_meta: list[InstitutionFieldMeta]
    form: CreateEditRoleFormValues
    role_id: str | None
    is_create: bool
    can_save: bool
    footer_note: str
    generated_at: datetime


class PermissionMatrixColumn(BaseModel):
    column_key: str
    institution_role_id: str | None
    label: str
    editable: bool


class PermissionMatrixCell(BaseModel):
    column_key: str
    checked: bool
    editable: bool


class PermissionMatrixRow(BaseModel):
    row_key: str
    label: str
    permission_code: str
    cells: list[PermissionMatrixCell]


class PermissionMatrixGroup(BaseModel):
    group_key: str
    group_label: str
    rows: list[PermissionMatrixRow]


class PermissionManagementMatrixChange(BaseModel):
    institution_role_id: str
    permission_code: str
    granted: bool


class PermissionManagementSavePayload(BaseModel):
    changes: list[PermissionManagementMatrixChange]


class PermissionManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_matrix_label: str
    save_changes_label: str
    matrix_section_title: str
    matrix_legend: str
    permission_columns: list[str]
    columns: list[PermissionMatrixColumn]
    groups: list[PermissionMatrixGroup]
    unsaved_changes_title: str
    unsaved_changes_note: str
    change_on_label: str
    change_off_label: str
    can_save: bool
    matrix_read_only_reason: str | None = None
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class RoleAssignmentFormValues(BaseModel):
    user_id: str
    institution_role_id: str
    scope_key: str
    valid_from: str
    valid_until: str = ""
    reason: str = ""


class RoleAssignmentUserOption(BaseModel):
    value: str
    label: str


class RoleAssignmentRoleOption(BaseModel):
    value: str
    label: str
    requires_approval: bool
    approval_notice: str | None = None


class RoleAssignmentCurrentRoleCard(BaseModel):
    role_name: str
    status_code: str
    status_label: str
    status_tone: str
    detail_line: str


class RoleAssignmentRecentRow(BaseModel):
    user_name: str
    role_name: str
    scope_label: str
    until_label: str
    status_code: str
    status_label: str
    status_tone: str


class RoleAssignmentPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    assignment_history_label: str
    assignment_history_href: str
    assign_role_label: str
    form_section_title: str
    form_field_meta: list[InstitutionFieldMeta]
    user_options: list[RoleAssignmentUserOption]
    role_options: list[RoleAssignmentRoleOption]
    scope_options: list[InstitutionFieldOption]
    form: RoleAssignmentFormValues
    approval_notice: str | None
    current_roles_section_title: str
    current_roles: list[RoleAssignmentCurrentRoleCard]
    recent_section_title: str
    recent_table_headers: list[str]
    recent_rows: list[RoleAssignmentRecentRow]
    view_history_label: str
    view_history_href: str
    cancel_href: str
    cancel_label: str
    submit_label: str
    submit_direct_label: str
    footer_note: str
    footer_snapshot_label: str
    can_submit: bool
    generated_at: datetime


class RoleAssignmentSubmitPayload(BaseModel):
    form: RoleAssignmentFormValues


class RoleAssignmentSubmitResponse(BaseModel):
    page: RoleAssignmentPageRead
    assignment_id: str
    status: str
    message: str


class AccountStatusTab(BaseModel):
    key: str
    label: str
    count: int
    active: bool


class AccountStatusTableRow(BaseModel):
    user_id: str
    user_name: str
    role_label: str
    reason_label: str
    since_label: str
    review_label: str
    review_tone: str
    department_label: str = "—"
    detail_href: str


class AccountStatusSuspendFormValues(BaseModel):
    user_id: str
    reason_code: str
    effective_from: str
    review_date: str = ""
    notes: str = ""


class AccountStatusInfoCard(BaseModel):
    key: str
    title: str
    description: str
    icon_key: str


class AccountStatusPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    suspend_account_label: str
    tabs: list[AccountStatusTab]
    active_tab: str
    table_headers: list[str]
    table_rows: list[AccountStatusTableRow]
    table_footer_label: str
    pagination: PoliciesPagination
    suspend_form_section_title: str
    suspend_field_meta: list[InstitutionFieldMeta]
    reason_options: list[InstitutionFieldOption]
    user_options: list[InstitutionFieldOption]
    suspend_form: AccountStatusSuspendFormValues
    what_happens_title: str
    what_happens_cards: list[AccountStatusInfoCard]
    cancel_href: str
    cancel_label: str
    submit_suspend_label: str
    footer_note: str
    footer_snapshot_label: str
    can_suspend: bool
    generated_at: datetime


class AccountStatusSuspendPayload(BaseModel):
    form: AccountStatusSuspendFormValues


class AccountStatusSuspendResponse(BaseModel):
    page: AccountStatusPageRead
    message: str


class LoginAccountActivityDailyBar(BaseModel):
    day_key: str
    day_label: str
    login_count: int


class LoginAccountActivityMethodBar(BaseModel):
    method_key: str
    method_label: str
    percent: int


class LoginAccountActivityRecentRow(BaseModel):
    user_name: str
    method_label: str
    device_label: str
    location_label: str
    result_code: str
    result_label: str
    result_tone: str


class LoginAccountActivityLockedCard(BaseModel):
    user_id: str
    user_name: str
    subtitle: str
    status_code: str
    status_label: str
    status_tone: str
    unlock_href: str


class LoginAccountActivityPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    date_range_options: list[UserDashboardFilterOption]
    role_filter_options: list[UserDashboardFilterOption]
    location_filter_options: list[UserDashboardFilterOption]
    selected_date_range: str
    selected_role_filter: str
    selected_location_filter: str
    scope_badge_label: str
    updated_label: str
    kpis: list[UserDashboardKpi]
    logins_per_day_title: str
    daily_bars: list[LoginAccountActivityDailyBar]
    daily_bars_max: int
    login_methods_title: str
    method_bars: list[LoginAccountActivityMethodBar]
    recent_section_title: str
    recent_live_label: str
    view_all_label: str
    view_all_href: str
    recent_table_headers: list[str]
    recent_rows: list[LoginAccountActivityRecentRow]
    locked_section_title: str
    unlock_label: str
    locked_accounts: list[LoginAccountActivityLockedCard]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class UserDetailsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    user_id: str
    reset_password_label: str
    suspend_label: str
    edit_user_label: str
    reset_password_action_user_id: str
    suspend_href: str
    edit_user_href: str
    show_suspend_action: bool
    profile_initials: str
    profile_name: str
    profile_badges: list[UserDetailsProfileBadge]
    designation_line: str
    email: str
    phone_label: str
    last_login_summary: str
    account_section_title: str
    account_edit_href: str
    account_edit_label: str
    account_fields: list[UserDetailsAccountField]
    roles_section_title: str
    assign_role_href: str
    assign_role_label: str
    roles_table_headers: list[str]
    assigned_roles: list[UserDetailsAssignedRoleRow]
    active_roles_footer_label: str
    role_assignment_href: str
    role_assignment_label: str
    permissions_section_title: str
    permission_bars: list[UserDetailsPermissionBar]
    activity_section_title: str
    access_history_href: str
    access_history_label: str
    recent_activity: list[UserDetailsActivityItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class UserDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    bulk_invite_label: str
    bulk_invite_href: str
    create_user_label: str
    create_user_href: str
    date_range_filter_label: str
    role_filter_label: str
    department_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    date_range_options: list[UserDashboardFilterOption]
    role_options: list[UserDashboardFilterOption]
    department_options: list[UserDashboardFilterOption]
    kpis: list[UserDashboardKpi]
    daily_active_title: str
    daily_active_points: list[UserDashboardDailyPoint]
    accounts_by_role_title: str
    role_bars: list[UserDashboardRoleBar]
    recent_accounts_title: str
    recent_accounts: list[UserDashboardRecentRow]
    recent_accounts_footer_label: str
    view_all_href: str
    view_all_label: str
    security_checks_title: str
    security_audit_href: str
    security_audit_label: str
    security_items: list[UserDashboardSecurityItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ConfigurationHistoryPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    date_range_filter_label: str
    setting_filter_label: str
    user_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    date_range_options: list[ConfigurationHistoryFilterOption]
    setting_options: list[ConfigurationHistoryFilterOption]
    user_options: list[ConfigurationHistoryFilterOption]
    change_log_title: str
    table_headers: list[str]
    changes: list[ConfigurationChangeRow]
    showing_label: str
    pagination: PoliciesPagination
    selected_change: ConfigurationChangeDetail | None
    change_details_title: str
    changes_by_area_title: str
    changes_by_area: list[ConfigurationAreaSummary]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class InstitutionPoliciesPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    add_policy_label: str
    add_policy_href: str
    create_dialog_title: str = "Add policy"
    create_dialog_subtitle: str = "Define title, audience, version and publish status"
    create_save_label: str = "Create policy"
    create_cancel_label: str = "Cancel"
    create_category_options: list[InstitutionPolicyFilterOption] = Field(default_factory=list)
    create_audience_options: list[InstitutionPolicyFilterOption] = Field(default_factory=list)
    create_status_options: list[InstitutionPolicyFilterOption] = Field(default_factory=list)
    search_placeholder: str
    category_filter_label: str
    audience_filter_label: str
    status_filter_label: str
    category_options: list[InstitutionPolicyFilterOption]
    audience_options: list[InstitutionPolicyFilterOption]
    status_options: list[InstitutionPolicyFilterOption]
    policies: list[InstitutionPolicyRow]
    policy_count_label: str
    pagination: PoliciesPagination
    selected_policy: InstitutionPolicySelectedDetail | None = None
    review_schedule: list[InstitutionPolicyReviewItem]
    review_schedule_title: str
    selected_panel_prefix: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AcademicInstitutionFormValues(BaseModel):
    academic_pattern: str
    credit_system: str
    working_days_per_semester: str
    teaching_week: str
    periods_per_day: str
    period_duration_minutes: str
    minimum_attendance_for_exams: str
    condonation_band: str
    attendance_calculation: str
    medical_leave_counted_present: str
    internal_external_weightage: str
    pass_mark_external: str
    pass_mark_overall: str
    grading_scheme: str
    allow_re_registration_failed_courses: bool = True
    enable_grace_marks: bool = True
    auto_detain_below_attendance: bool = False
    lock_marks_after_result_approval: bool = True


class AcademicInstitutionFieldGroup(BaseModel):
    key: str
    title: str
    field_keys: list[str]


class AcademicInstitutionToggleRule(BaseModel):
    key: str
    label: str
    description: str
    enabled: bool


class AcademicInstitutionAppliesRow(BaseModel):
    key: str
    title: str
    description: str
    href: str | None = None
    icon_slug: str = "landmark"
    badge_label: str | None = None
    badge_tone: str | None = None


class AcademicInstitutionSettingsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    reset_label: str
    save_label: str
    footer_note: str
    form: AcademicInstitutionFormValues
    field_meta: list[InstitutionFieldMeta]
    field_options: dict[str, list[InstitutionFieldOption]]
    field_groups: list[AcademicInstitutionFieldGroup]
    toggle_rules: list[AcademicInstitutionToggleRule]
    applies_to: list[AcademicInstitutionAppliesRow]
    generated_at: datetime


class AcademicInstitutionSettingsSave(BaseModel):
    form: AcademicInstitutionFormValues


class CampusBuildingRow(BaseModel):
    building_id: str
    name: str
    floors: int
    classroom_count: int
    laboratory_count: int
    departments_label: str


class CampusSummaryStat(BaseModel):
    key: str
    label: str
    value: str


class CampusFacilityStatusRow(BaseModel):
    showcase_id: str
    title: str
    subtitle: str
    status_code: str
    status_label: str
    icon_slug: str


class CampusDetailPageRead(BaseModel):
    page_title: str
    campus_id: str
    campus_name: str
    back_href: str
    contact_href: str
    buildings: list[CampusBuildingRow]
    buildings_total: int
    buildings_shown: int
    buildings_footer_label: str
    manage_buildings_href: str
    view_all_buildings_href: str
    summary_stats: list[CampusSummaryStat]
    facility_statuses: list[CampusFacilityStatusRow]
    generated_at: datetime


class CampusTabLink(BaseModel):
    campus_id: str
    name: str
    href: str
    is_active: bool


class CampusOfficialContactRow(BaseModel):
    contact_id: str
    role_label: str
    name: str
    phone: str | None = None
    email: str | None = None


class CampusEmergencyContactRow(BaseModel):
    contact_id: str
    label: str
    phone: str


class CampusContactOfficialInput(BaseModel):
    contact_id: str | None = None
    role_label: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None


class CampusContactEmergencyInput(BaseModel):
    contact_id: str | None = None
    label: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=1, max_length=64)


class CampusContactPageSave(BaseModel):
    address: InstitutionAddress
    official_contacts: list[CampusContactOfficialInput] = Field(default_factory=list)
    emergency_contacts: list[CampusContactEmergencyInput] = Field(default_factory=list)


class CampusContactPageRead(BaseModel):
    page_title: str
    campus_tabs: list[CampusTabLink]
    address: InstitutionAddress
    address_field_meta: list[InstitutionFieldMeta]
    state_options: list[InstitutionFieldOption]
    district_options: list[InstitutionFieldOption]
    official_contacts: list[CampusOfficialContactRow]
    contact_count_label: str
    add_contact_enabled: bool
    usage_contexts: list[InstitutionUsageContext]
    emergency_contacts: list[CampusEmergencyContactRow]
    footer_note: str
    cancel_href: str
    generated_at: datetime


class CampusDashboardKpi(BaseModel):
    key: str
    label: str
    value: str
    hint: str
    hint_tone: str = "muted"


class CampusDashboardRow(BaseModel):
    campus_id: str
    name: str
    location_label: str
    student_count: int
    buildings_count: int
    status_code: str
    status_label: str
    detail_href: str


class ClassroomUtilizationBar(BaseModel):
    building_label: str
    utilization_percent: int
    tone: str = "primary"


class CampusFacilitySummary(BaseModel):
    key: str
    title: str
    description: str
    icon_slug: str


class CampusOpenIssue(BaseModel):
    issue_id: str
    title: str
    raised_label: str
    status_code: str
    status_label: str
    tone: str = "warning"


class CampusManagementDashboardRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    add_campus_label: str
    kpis: list[CampusDashboardKpi]
    campuses: list[CampusDashboardRow]
    campus_count_label: str
    campuses_view_all_href: str
    campus_details_href: str
    classroom_utilization: list[ClassroomUtilizationBar]
    classroom_utilization_hint: str | None = None
    facilities: list[CampusFacilitySummary]
    open_issues: list[CampusOpenIssue]
    operations_href: str
    add_campus_href: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class InstitutionProfilePageRead(BaseModel):
    profile: InstitutionProfileRead
    display_name: str
    subtitle_line: str | None = None
    location_label: str | None = None
    status_badges: list[InstitutionStatusBadge] = Field(default_factory=list)
    about_fields: list[InstitutionAboutField] = Field(default_factory=list)
    leadership: list[InstitutionLeadershipRow] = Field(default_factory=list)
    profile_completeness: list[ProfileCompletenessRow] = Field(default_factory=list)
    related_settings: list[RelatedSettingLink] = Field(default_factory=list)
    branding_primary_color: str | None = None
    branding_logo_file_id: str | None = None
    footer_disclaimer: str
    generated_at: datetime


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


class DepartmentEnrollmentBarItem(BaseModel):
    department_id: str
    department_code: str
    student_count: int = 0
    faculty_count: int = 0


class DepartmentAttentionTableRow(BaseModel):
    department_id: str
    department_name: str
    issue: str
    owner_label: str
    status_code: str
    status_label: str
    status_tone: str
    detail_href: str


class DepartmentSchoolBarItem(BaseModel):
    school_id: str
    school_name: str
    department_count: int = 0
    share_percent: int = 0


class DepartmentQuickActionItem(BaseModel):
    key: str
    title: str
    subtitle: str
    action_label: str
    href: str
    icon_slug: str = "circle"


class AllDepartmentsTableRow(BaseModel):
    department_id: str
    department_name: str
    department_code: str
    head_label: str
    programme_count: int = 0
    student_count: int = 0
    faculty_count: int = 0
    status_code: str
    status_label: str
    status_tone: str
    detail_href: str


class CreateEditDepartmentFormValues(BaseModel):
    name: str = ""
    department_code: str = ""
    department_kind: str = "academic"
    organization_unit_id: str = ""
    campus_id: str = ""
    establishment_year: int | None = None
    building_floor_label: str = ""
    contact_email: str = ""
    vision_mission: str = ""
    head_user_id: str = ""
    approved_intake_ug: int | None = None
    aicte_approval_reference: str = ""
    cost_centre_code: str = ""
    settings_template_department_id: str = ""


class CreateEditDepartmentTemplateOption(BaseModel):
    template_key: str
    title: str
    subtitle: str
    action_label: str
    department_id: str


class CreateEditDepartmentChecklistStep(BaseModel):
    key: str
    label: str
    hint: str
    state: str


class CreateEditDepartmentPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    cancel_href: str
    cancel_label: str
    save_label: str
    save_draft_label: str
    create_label: str
    details_section_title: str
    setup_section_title: str
    copy_settings_title: str
    checklist_title: str
    details_field_meta: list[InstitutionFieldMeta]
    setup_field_meta: list[InstitutionFieldMeta]
    department_kind_options: list[InstitutionFieldOption]
    school_options: list[InstitutionFieldOption]
    campus_options: list[InstitutionFieldOption]
    building_options: list[InstitutionFieldOption]
    cost_centre_options: list[InstitutionFieldOption]
    head_options: list[InstitutionFieldOption]
    template_options: list[CreateEditDepartmentTemplateOption]
    checklist_steps: list[CreateEditDepartmentChecklistStep]
    form: CreateEditDepartmentFormValues
    department_id: str | None
    is_create: bool
    can_save: bool
    footer_note: str
    footer_disclaimer: str
    generated_at: datetime


class CreateEditDepartmentSavePayload(BaseModel):
    department_id: str | None = None
    mode: str = "create"
    form: CreateEditDepartmentFormValues


class DepartmentDetailsProfileBadge(BaseModel):
    key: str
    label: str
    tone: str


class DepartmentDetailsProgrammeRow(BaseModel):
    programme_id: str
    programme_name: str
    level_label: str
    intake: int | None = None
    student_count: int = 0
    status_code: str
    status_label: str
    status_tone: str


class DepartmentDetailsFacultyRow(BaseModel):
    user_id: str
    name: str
    designation: str
    workload_label: str
    status_code: str
    status_label: str
    status_tone: str


class DepartmentDetailsResourceItem(BaseModel):
    key: str
    title: str
    value: str


class DepartmentDetailsActivityItem(BaseModel):
    activity_id: str
    title: str
    occurred_label: str
    tone: str


class DepartmentDetailsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    view_report_label: str
    view_report_href: str
    edit_department_label: str
    edit_department_href: str
    department_id: str
    department_name: str
    department_code: str
    metadata_line: str
    head_label: str
    email_label: str
    phone_label: str
    profile_badges: list[DepartmentDetailsProfileBadge]
    kpis: list[UserDashboardKpi]
    programmes_section_title: str
    programme_mapping_href: str
    programme_mapping_label: str
    programmes: list[DepartmentDetailsProgrammeRow]
    programmes_total: int
    programmes_footer_label: str
    programmes_view_all_href: str
    faculty_section_title: str
    faculty_allocation_href: str
    faculty_allocation_label: str
    faculty: list[DepartmentDetailsFacultyRow]
    faculty_total: int
    faculty_footer_label: str
    faculty_view_all_href: str
    resources_section_title: str
    resources: list[DepartmentDetailsResourceItem]
    activity_section_title: str
    activities: list[DepartmentDetailsActivityItem]
    table_programme_headers: list[str]
    table_faculty_headers: list[str]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AllDepartmentsListPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    create_department_label: str
    create_department_href: str
    search_placeholder: str
    school_filter_label: str
    type_filter_label: str
    status_filter_label: str
    school_options: list[UserListFilterOption]
    type_options: list[UserListFilterOption]
    status_options: list[UserListFilterOption]
    departments_section_title: str
    departments_count_label: str
    table_headers: list[str]
    departments: list[AllDepartmentsTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class DepartmentHeadAssignmentTableRow(BaseModel):
    department_id: str
    department_label: str
    head_name: str
    since_label: str
    term_ends_label: str
    status_code: str
    status_label: str
    status_tone: str
    is_selected: bool = False


class DepartmentHeadEligibilityRow(BaseModel):
    key: str
    label: str
    detail: str
    status_code: str
    status_label: str
    status_tone: str


class DepartmentHeadAssignmentFormValues(BaseModel):
    faculty_user_id: str = ""
    appointment_type: str = "regular"
    effective_from: str = ""
    term_end: str = ""
    order_reference: str = ""


class OrganizationModuleEmptyState(BaseModel):
    title: str
    description: str
    highlights: list[str] = Field(default_factory=list)
    primary_label: str
    primary_href: str
    secondary_label: str | None = None
    secondary_href: str | None = None


class DepartmentHeadAssignmentPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    rotation_policy_label: str
    rotation_policy_href: str
    assign_head_label: str
    current_heads_section_title: str
    table_headers: list[str]
    table_rows: list[DepartmentHeadAssignmentTableRow]
    departments_count_label: str
    pagination: PoliciesPagination
    assign_panel_title: str
    assign_panel_subtitle: str
    faculty_field_label: str
    faculty_options: list[InstitutionFieldOption]
    appointment_type_field_label: str
    appointment_type_options: list[InstitutionFieldOption]
    effective_from_field_label: str
    term_end_field_label: str
    order_reference_field_label: str
    eligibility_section_title: str
    eligibility_rows: list[DepartmentHeadEligibilityRow]
    form: DepartmentHeadAssignmentFormValues
    selected_department_id: str | None
    cancel_label: str
    submit_label: str
    footer_note: str
    footer_disclaimer: str
    footer_snapshot_label: str
    can_submit: bool
    assign_head_enabled: bool = True
    form_interactive: bool = True
    setup_empty_state: OrganizationModuleEmptyState | None = None
    generated_at: datetime


class DepartmentHeadAssignmentSavePayload(BaseModel):
    department_id: str
    form: DepartmentHeadAssignmentFormValues


class DepartmentHeadAssignmentSaveResult(BaseModel):
    message: str
    approval_status: str
    page: DepartmentHeadAssignmentPageRead


class OrganizationalHierarchyNodeRead(BaseModel):
    node_id: str
    node_type: str
    title: str
    subtitle: str = ""
    depth: int = 0
    icon_slug: str = "users"
    badge_label: str | None = None
    badge_tone: str | None = None
    status_label: str | None = None
    status_tone: str | None = None
    default_expanded: bool = False
    children: list["OrganizationalHierarchyNodeRead"] = Field(default_factory=list)


class OrganizationalHierarchyEditAction(BaseModel):
    action_key: str
    label: str
    href: str
    action_type: str = "outline"


class OrganizationalHierarchySelectedUnitRead(BaseModel):
    node_id: str
    unit_label: str
    reports_to_label: str
    head_label: str
    members_label: str
    edit_actions: list[OrganizationalHierarchyEditAction] = Field(default_factory=list)


class OrganizationalHierarchySummaryItem(BaseModel):
    key: str
    label: str
    value: str


class OrganizationalHierarchyPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    edit_structure_label: str
    edit_structure_href: str
    edit_mode: bool = False
    edit_panel_title: str = ""
    edit_panel_hint: str = ""
    setup_edit_actions: list[OrganizationalHierarchyEditAction] = Field(default_factory=list)
    structure_section_title: str
    structure_section_hint: str
    tree: list[OrganizationalHierarchyNodeRead]
    selected_unit: OrganizationalHierarchySelectedUnitRead | None
    summary_section_title: str
    summary_items: list[OrganizationalHierarchySummaryItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ProgrammeCourseMappingDepartmentTab(BaseModel):
    department_id: str
    tab_label: str
    is_selected: bool = False


class ProgrammeOwnedRow(BaseModel):
    programme_id: str
    programme_name: str
    level_label: str
    duration_label: str
    intake_label: str
    regulation_label: str
    status_code: str
    status_label: str
    status_tone: str


class ServiceCourseRow(BaseModel):
    course_id: str
    course_label: str
    taught_to_label: str
    semester_label: str
    student_count: int


class UnmappedCourseItem(BaseModel):
    course_id: str
    course_label: str
    detail: str
    action_code: str
    action_label: str
    action_tone: str


class CourseLoadBarItem(BaseModel):
    key: str
    label: str
    value: int
    max_value: int


class ProgrammeCourseMappingPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    map_programme_label: str
    map_programme_href: str
    department_tabs: list[ProgrammeCourseMappingDepartmentTab]
    more_departments: list[ProgrammeCourseMappingDepartmentTab]
    selected_department_id: str
    selected_department_name: str
    programmes_section_title: str
    programmes_table_headers: list[str]
    programmes: list[ProgrammeOwnedRow]
    programmes_count_label: str
    academic_configuration_label: str
    academic_configuration_href: str
    service_courses_section_title: str
    service_table_headers: list[str]
    service_courses: list[ServiceCourseRow]
    service_courses_count_label: str
    service_view_all_label: str
    service_view_all_href: str
    unmapped_section_title: str
    unmapped_items: list[UnmappedCourseItem]
    course_load_section_title: str
    course_load_bars: list[CourseLoadBarItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    setup_empty_state: OrganizationModuleEmptyState | None = None
    generated_at: datetime


class DepartmentFacultyCapacityRow(BaseModel):
    department_id: str
    department_label: str
    sanctioned: int
    in_position: int
    vacant: int
    workload_pct: int | None
    status_code: str
    status_label: str
    status_tone: str


class DepartmentFacultyVacancyItem(BaseModel):
    department_id: str
    department_label: str
    detail: str
    count: int
    badge_tone: str


class DepartmentFacultyDesignationBar(BaseModel):
    key: str
    label: str
    value: int
    max_value: int


class DepartmentFacultyAllocationFormValues(BaseModel):
    faculty_user_id: str = ""
    allocate_to_department_id: str = ""
    allocation_type: str = "shared_50"
    effective_from: str = ""
    effective_to: str = ""
    order_reference: str = ""
    semester_label: str = ""


class DepartmentFacultyAllocationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    allocate_faculty_label: str
    allocate_faculty_href: str
    semester_filter_label: str
    department_filter_label: str
    designation_filter_label: str
    resources_nav_label: str
    resources_nav_href: str
    updated_at_label: str
    semester_options: list[InstitutionFieldOption]
    department_options: list[InstitutionFieldOption]
    designation_options: list[InstitutionFieldOption]
    selected_semester: str
    selected_department_id: str
    selected_designation: str
    capacity_section_title: str
    capacity_table_headers: list[str]
    capacity_table_footer_note: str
    capacity_rows: list[DepartmentFacultyCapacityRow]
    pagination: PoliciesPagination
    move_share_section_title: str
    move_share_section_subtitle: str = ""
    faculty_field_label: str
    faculty_options: list[InstitutionFieldOption]
    allocate_to_field_label: str
    department_allocate_options: list[InstitutionFieldOption]
    allocation_type_field_label: str
    allocation_type_options: list[InstitutionFieldOption]
    allocation_type_hint: str = ""
    effective_from_field_label: str
    effective_to_field_label: str = "Effective to"
    order_reference_field_label: str = "Order / reference"
    form: DepartmentFacultyAllocationFormValues
    move_footer_note: str
    cancel_label: str
    save_label: str
    allocate_faculty_enabled: bool = True
    form_interactive: bool = True
    vacancies_section_title: str
    hr_recruitment_label: str
    hr_recruitment_href: str
    vacancy_items: list[DepartmentFacultyVacancyItem]
    designation_mix_section_title: str
    designation_bars: list[DepartmentFacultyDesignationBar]
    can_save: bool
    footer_disclaimer: str
    footer_snapshot_label: str
    setup_empty_state: OrganizationModuleEmptyState | None = None
    generated_at: datetime


class DepartmentFacultyAllocationSavePayload(BaseModel):
    form: DepartmentFacultyAllocationFormValues
    page: int = 1
    semester_label: str | None = None
    department_id: str | None = None
    designation_filter: str | None = None


class DepartmentFacultyAllocationSaveResult(BaseModel):
    message: str
    page: DepartmentFacultyAllocationPageRead


class DepartmentStatusHistoryEventRow(BaseModel):
    event_id: str
    department_id: str
    event_label: str
    department_label: str
    by_label: str
    date_label: str
    status_code: str
    status_label: str
    status_tone: str


class DepartmentStatusHistoryStatusSummaryItem(BaseModel):
    key: str
    title: str
    subtitle: str
    count: int
    badge_tone: str
    detail_count: int | None = None


class DepartmentStatusHistoryTimelineItem(BaseModel):
    event_id: str
    title: str
    date_label: str
    tone: str
    nested_status_label: str | None = None


class DepartmentResourceKpiCard(BaseModel):
    key: str
    title: str
    value: str
    subtitle: str
    subtitle_tone: str


class DepartmentResourceTab(BaseModel):
    department_id: str
    label: str
    short_label: str


class DepartmentResourceLabRow(BaseModel):
    lab_id: str
    lab_name: str
    room_label: str
    capacity: int
    systems_label: str
    status_code: str
    status_label: str
    status_tone: str


class DepartmentResourceBudgetBar(BaseModel):
    key: str
    label: str
    spent_label: str
    cap_label: str
    spent_amount: float
    cap_amount: float


class DepartmentResourceOpenRequestItem(BaseModel):
    request_id: str
    title: str
    detail_line: str
    status_tag: str
    status_tone: str


class DepartmentResourceManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    request_resource_label: str
    request_resource_href: str
    faculty_nav_label: str
    faculty_nav_href: str
    updated_at_label: str
    department_tabs: list[DepartmentResourceTab]
    more_departments_label: str
    more_department_options: list[InstitutionFieldOption]
    selected_department_id: str
    kpi_cards: list[DepartmentResourceKpiCard]
    laboratories_section_title: str
    laboratories_table_headers: list[str]
    laboratory_rows: list[DepartmentResourceLabRow]
    laboratories_footer_count_label: str
    laboratories_view_all_label: str
    laboratories_view_all_href: str | None
    budget_section_title: str
    budget_bars: list[DepartmentResourceBudgetBar]
    open_requests_section_title: str
    open_requests: list[DepartmentResourceOpenRequestItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class DepartmentStatusHistoryPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    since_year_filter_label: str
    department_filter_label: str
    change_type_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    since_year_options: list[InstitutionFieldOption]
    department_options: list[InstitutionFieldOption]
    change_type_options: list[InstitutionFieldOption]
    selected_since_year: str
    selected_department_id: str
    selected_change_type: str
    table_headers: list[str]
    events: list[DepartmentStatusHistoryEventRow]
    pagination: PoliciesPagination
    showing_label: str
    status_summary_title: str
    status_summary_items: list[DepartmentStatusHistoryStatusSummaryItem]
    timeline_section_title: str
    selected_timeline_department_id: str
    timeline_items: list[DepartmentStatusHistoryTimelineItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AcademicConfigAreaTableRow(BaseModel):
    area_key: str
    area_label: str
    owner_label: str
    last_updated_label: str
    progress_percent: int
    status_code: str
    status_label: str
    status_tone: str
    detail_href: str


class AcademicRegulationUsageItem(BaseModel):
    regulation_key: str
    regulation_label: str
    student_count: int
    share_percent: int
    tone: str


class AcademicConfigShortcutItem(BaseModel):
    key: str
    title: str
    subtitle: str
    action_label: str
    href: str
    icon_slug: str = "circle"


class AcademicConfigSetupAlert(BaseModel):
    title: str
    description: str
    continue_label: str
    continue_href: str
    deadline_label: str | None = None


class AcademicConfigurationDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    checklist_label: str
    checklist_href: str
    open_current_year_label: str
    open_current_year_href: str
    kpis: list[UserDashboardKpi]
    setup_alert: AcademicConfigSetupAlert | None = None
    config_section_title: str
    config_table_headers: list[str]
    config_area_rows: list[AcademicConfigAreaTableRow]
    config_footer_count_label: str
    config_checklist_href: str
    config_checklist_label: str
    regulations_section_title: str
    regulation_items: list[AcademicRegulationUsageItem]
    shortcuts_section_title: str
    shortcuts: list[AcademicConfigShortcutItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class DepartmentManagementDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    create_department_label: str
    create_department_href: str
    academic_year_filter_label: str
    campus_filter_label: str
    school_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    academic_year_options: list[UserDashboardFilterOption]
    campus_options: list[UserDashboardFilterOption]
    school_options: list[UserDashboardFilterOption]
    selected_academic_year: str
    selected_campus_id: str
    selected_school_id: str
    kpis: list[UserDashboardKpi]
    enrollment_chart_title: str
    enrollment_bars: list[DepartmentEnrollmentBarItem]
    attention_section_title: str
    attention_table_headers: list[str]
    attention_rows: list[DepartmentAttentionTableRow]
    attention_footer_label: str
    attention_view_all_href: str
    attention_view_all_label: str
    schools_section_title: str
    school_bars: list[DepartmentSchoolBarItem]
    quick_actions_title: str
    quick_actions: list[DepartmentQuickActionItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


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


class StudentAdminDashboardFilterOption(BaseModel):
    value: str
    label: str


class StudentAdminWeeklySeriesPoint(BaseModel):
    week_label: str
    current_year_count: int
    previous_year_count: int


class StudentAdminRecentAdmissionRow(BaseModel):
    admission_id: str
    student_name: str
    programme_label: str
    quota_label: str
    admitted_label: str
    documents_status_label: str
    documents_status_tone: str
    detail_href: str


class StudentAdminEnrollmentYearBar(BaseModel):
    year_key: str
    year_label: str
    student_count: int
    share_percent: int


class StudentAdminWorkQueueItem(BaseModel):
    key: str
    title: str
    subtitle: str
    count: int
    href: str
    action_label: str
    icon_slug: str


class StudentAdminStatusItem(BaseModel):
    status_key: str
    status_label: str
    student_count: int


class StudentAdminDocumentAlert(BaseModel):
    title: str
    description: str
    continue_label: str
    continue_href: str


class StudentDetailsBadge(BaseModel):
    key: str
    label: str
    tone: str


class StudentDetailsKeyValueRow(BaseModel):
    key: str
    label: str
    value: str


class StudentDetailsDocumentRow(BaseModel):
    document_key: str
    document_label: str
    uploaded_label: str
    status_label: str
    status_tone: str
    verified_by_label: str


class StudentDetailsStandingField(BaseModel):
    key: str
    label: str
    value: str
    value_tone: str | None = None


class StudentDetailsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    record_id: str
    edit_profile_label: str
    edit_profile_href: str
    academic_history_label: str
    academic_history_href: str
    profile_initials: str
    profile_name: str
    profile_badges: list[StudentDetailsBadge]
    profile_summary_line: str
    email: str
    phone: str
    admitted_label: str
    enrollment_section_title: str
    enrollment_rows: list[StudentDetailsKeyValueRow]
    documents_section_title: str
    documents_table_headers: list[str]
    document_rows: list[StudentDetailsDocumentRow]
    documents_footer_label: str
    contact_section_title: str
    contact_rows: list[StudentDetailsKeyValueRow]
    standing_section_title: str
    standing_fields: list[StudentDetailsStandingField]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AllStudentsListTableRow(BaseModel):
    record_id: str
    student_name: str
    register_number: str
    programme_label: str
    year_section_label: str
    attendance_label: str
    attendance_tone: str | None = None
    fee_status_label: str
    fee_status_tone: str
    status_label: str
    status_tone: str
    detail_href: str


class AllStudentsListPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    add_student_label: str
    add_student_href: str
    bulk_actions_label: str
    bulk_actions_href: str
    search_placeholder: str
    programme_filter_label: str
    year_filter_label: str
    section_filter_label: str
    status_filter_label: str
    programme_options: list[UserListFilterOption]
    year_options: list[UserListFilterOption]
    section_options: list[UserListFilterOption]
    status_options: list[UserListFilterOption]
    students_section_title: str
    students_count_label: str
    table_headers: list[str]
    students: list[AllStudentsListTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentAdmissionListTableRow(BaseModel):
    admission_id: str
    applicant_name: str
    application_number: str
    programme_label: str
    quota_label: str
    marks_label: str
    status_label: str
    status_tone: str
    detail_href: str


class NewStudentRegistrationWizardStep(BaseModel):
    key: str
    label: str
    step_number: int
    status: str = "pending"


class NewStudentRegistrationFormSection(BaseModel):
    key: str
    title: str


class NewStudentRegistrationSummaryItem(BaseModel):
    key: str
    label: str
    value: str


class NewStudentRegistrationNextStep(BaseModel):
    key: str
    label: str
    status_label: str
    tone: str


class NewStudentRegistrationFormValues(BaseModel):
    programme_code: str = ""
    academic_year_code: str = ""
    marks_percentage: str = ""
    full_name: str = ""
    date_of_birth: str | None = None
    gender: str | None = None
    blood_group: str | None = None
    mobile: str = ""
    email: str = ""
    nationality: str | None = None
    community: str | None = None
    guardian_name: str = ""
    relationship: str | None = None
    guardian_mobile: str = ""
    occupation: str = ""


class NewStudentRegistrationPageRead(BaseModel):
    admission_id: str
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    save_draft_label: str
    continue_label: str
    current_step_key: str
    step_position_label: str
    steps: list[NewStudentRegistrationWizardStep]
    sections: list[NewStudentRegistrationFormSection]
    field_meta: list[InstitutionFieldMeta]
    gender_options: list[InstitutionFieldOption]
    blood_group_options: list[InstitutionFieldOption]
    nationality_options: list[InstitutionFieldOption]
    community_options: list[InstitutionFieldOption]
    relationship_options: list[InstitutionFieldOption]
    programme_options: list[InstitutionFieldOption] = Field(default_factory=list)
    academic_year_options: list[InstitutionFieldOption] = Field(default_factory=list)
    form: NewStudentRegistrationFormValues
    admission_summary_title: str
    admission_summary: list[NewStudentRegistrationSummaryItem]
    next_steps_title: str
    next_steps: list[NewStudentRegistrationNextStep]
    has_draft: bool = False
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class NewStudentRegistrationDraftUpdate(BaseModel):
    admission_id: str
    step_key: str | None = None
    advance: bool = False
    values: dict[str, Any] = Field(default_factory=dict)


class StudentProfileManagementFormValues(BaseModel):
    full_name: str = ""
    mobile: str = ""
    email: str = ""
    guardian_mobile: str = ""
    address: str = ""
    reason_for_change: str = ""


class StudentProfileManagementLockedField(BaseModel):
    key: str
    label: str
    value: str
    hint: str


class StudentProfileManagementLastUpdated(BaseModel):
    by_label: str
    on_label: str


class StudentProfilePickerRow(BaseModel):
    record_id: str
    student_name: str
    register_number: str
    manage_href: str


class StudentProfileManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    discard_label: str
    save_changes_label: str
    requires_record: bool = False
    select_student_title: str | None = None
    select_student_hint: str | None = None
    all_students_href: str | None = None
    all_students_label: str | None = None
    picker_rows: list[StudentProfilePickerRow] = Field(default_factory=list)
    record_id: str | None = None
    detail_href: str | None = None
    profile_initials: str | None = None
    profile_name: str | None = None
    profile_badges: list[StudentDetailsBadge] = Field(default_factory=list)
    profile_summary_line: str | None = None
    email_display: str | None = None
    phone_display: str | None = None
    admitted_label: str | None = None
    editable_section_title: str = "Editable profile"
    field_meta: list[InstitutionFieldMeta] = Field(default_factory=list)
    form: StudentProfileManagementFormValues = Field(default_factory=StudentProfileManagementFormValues)
    locked_fields_title: str = "Locked fields"
    locked_fields: list[StudentProfileManagementLockedField] = Field(default_factory=list)
    transfer_workflow_href: str | None = None
    last_updated_title: str = "Last updated"
    last_updated: StudentProfileManagementLastUpdated | None = None
    document_verification_href: str | None = None
    audit_footer_note: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentProfileManagementSavePayload(BaseModel):
    record_id: str
    values: dict[str, Any] = Field(default_factory=dict)


class StudentDocumentVerificationTableRow(BaseModel):
    document_key: str
    document_label: str
    uploaded_label: str
    status_label: str
    status_tone: str
    verified_by_label: str
    file_name: str | None = None
    file_size_label: str | None = None
    is_selected: bool = False


class StudentDocumentVerificationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    request_document_label: str
    request_document_href: str
    verify_all_label: str
    record_id: str | None = None
    student_name: str | None = None
    profile_href: str | None = None
    kpis: list[UserDashboardKpi]
    documents_section_title: str
    documents_footer_label: str
    table_headers: list[str]
    document_rows: list[StudentDocumentVerificationTableRow]
    preview_title: str
    preview_empty_label: str
    preview_file_name: str | None = None
    preview_meta_label: str | None = None
    browse_files_label: str
    browse_files_href: str | None = None
    decision_section_title: str
    result_field_label: str
    remarks_field_label: str
    result_options: list[InstitutionFieldOption]
    selected_document_key: str | None = None
    decision_result: str = ""
    decision_remarks: str = ""
    submit_decision_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentDocumentVerificationDecisionPayload(BaseModel):
    record_id: str
    document_key: str
    result: str
    remarks: str | None = None


class StudentDocumentVerificationVerifyAllPayload(BaseModel):
    record_id: str


class StudentAdmissionPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    new_admission_label: str
    new_admission_href: str
    academic_year_filter_label: str
    programme_filter_label: str
    quota_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    academic_year_options: list[StudentAdminDashboardFilterOption]
    programme_options: list[StudentAdminDashboardFilterOption]
    quota_options: list[StudentAdminDashboardFilterOption]
    status_filter_label: str
    status_options: list[StudentAdminDashboardFilterOption]
    selected_academic_year: str
    selected_programme_code: str
    selected_quota: str
    selected_status: str
    kpis: list[UserDashboardKpi]
    applications_section_title: str
    applications_count_label: str
    table_headers: list[str]
    applications: list[StudentAdmissionListTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentAdministrationDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    new_admission_label: str
    new_admission_href: str
    academic_year_filter_label: str
    programme_filter_label: str
    study_year_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    academic_year_options: list[StudentAdminDashboardFilterOption]
    programme_options: list[StudentAdminDashboardFilterOption]
    study_year_options: list[StudentAdminDashboardFilterOption]
    selected_academic_year: str
    selected_programme_code: str
    selected_study_year: str
    kpis: list[UserDashboardKpi]
    document_alert: StudentAdminDocumentAlert | None = None
    admissions_chart_title: str
    admissions_chart_current_label: str
    admissions_chart_previous_label: str
    admissions_weekly_series: list[StudentAdminWeeklySeriesPoint]
    recent_admissions_title: str
    recent_admissions_headers: list[str]
    recent_admissions_rows: list[StudentAdminRecentAdmissionRow]
    recent_admissions_footer_label: str
    recent_admissions_view_all_href: str
    recent_admissions_view_all_label: str
    enrollment_by_year_title: str
    enrollment_year_bars: list[StudentAdminEnrollmentYearBar]
    work_queue_title: str
    work_queue_items: list[StudentAdminWorkQueueItem]
    student_status_title: str
    student_status_items: list[StudentAdminStatusItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class FacultyEmployeeDashboardFacultyRow(BaseModel):
    record_id: str
    faculty_name: str
    employee_id_label: str
    department_label: str
    designation_label: str
    workload_label: str
    status_label: str
    status_tone: str
    detail_href: str


class FacultyDirectoryTableRow(BaseModel):
    record_id: str
    faculty_name: str
    employee_id_label: str
    department_label: str
    designation_label: str
    workload_label: str
    status_label: str
    status_tone: str
    detail_href: str


class FacultyProfileQualificationRow(BaseModel):
    degree: str
    institution: str
    year_label: str


class FacultyProfileSubjectRow(BaseModel):
    subject_name: str
    subject_code: str
    programme_sem_label: str
    hours_label: str
    type_label: str


class FacultyProfilePageRead(BaseModel):
    page_title: str
    page_subtitle: str
    edit_label: str
    edit_href: str
    timetable_label: str
    timetable_href: str
    back_href: str
    back_label: str
    record_id: str
    profile_initials: str
    profile_name: str
    status_badge: StudentDetailsBadge
    employment_type_badge: StudentDetailsBadge | None = None
    profile_summary_line: str
    email: str
    phone: str
    joined_label: str
    qualifications_section_title: str
    qualifications_headers: list[str]
    qualification_rows: list[FacultyProfileQualificationRow]
    qualifications_footer_label: str
    subjects_section_title: str
    subjects_headers: list[str]
    subject_rows: list[FacultyProfileSubjectRow]
    subjects_footer_label: str
    employment_section_title: str
    employment_rows: list[StudentDetailsKeyValueRow]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class FacultyDirectoryPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    add_faculty_label: str
    add_faculty_href: str
    search_placeholder: str
    department_filter_label: str
    designation_filter_label: str
    status_filter_label: str
    department_options: list[UserListFilterOption]
    designation_options: list[UserListFilterOption]
    status_options: list[UserListFilterOption]
    faculty_section_title: str
    faculty_count_label: str
    table_headers: list[str]
    faculty_rows: list[FacultyDirectoryTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class EmployeeDirectoryTableRow(BaseModel):
    record_id: str
    employee_name: str
    employee_id_label: str
    unit_label: str
    role_label: str
    type_label: str
    status_label: str
    status_tone: str
    detail_href: str


class EmployeeDirectoryPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    add_employee_label: str
    add_employee_href: str
    search_placeholder: str
    unit_filter_label: str
    role_filter_label: str
    type_filter_label: str
    status_filter_label: str
    unit_options: list[UserListFilterOption]
    role_options: list[UserListFilterOption]
    type_options: list[UserListFilterOption]
    status_options: list[UserListFilterOption]
    employees_section_title: str
    employees_count_label: str
    table_headers: list[str]
    employee_rows: list[EmployeeDirectoryTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AddNewFacultyEmployeeWizardStep(BaseModel):
    key: str
    label: str
    step_number: int
    status: str = "pending"


class AddNewFacultyEmployeeFormValues(BaseModel):
    full_name: str = ""
    mobile: str = ""
    date_of_birth: str = ""
    gender: str = ""
    residential_address: str = ""
    employee_type: str = ""
    department_id: str = ""
    designation: str = ""
    joining_date: str = ""
    reporting_to: str = ""
    employment_status: str = ""
    contract_end_date: str = ""
    official_email: str = ""
    degree: str = ""
    institution: str = ""
    qualification_year: str = ""
    specialization: str = ""
    experience_years: str = ""
    document_ids_verified: str = ""
    document_degree_certificates: str = ""
    document_experience: str = ""
    password: str = ""
    confirm_password: str = ""


class AddNewFacultyEmployeeAccessCard(BaseModel):
    title: str = "Access"
    role_label: str = ""
    role_icon_key: str = "user"
    login_created_label: str = ""
    login_icon_key: str = "key"


class AddNewFacultyEmployeeIdCard(BaseModel):
    title: str = "Employee ID"
    next_id_label: str = "Next ID"
    next_id_value: str = ""
    format_label: str = "Format"
    format_value: str = "EMP-####"


class AddNewFacultyEmployeePageRead(BaseModel):
    draft_id: str
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    save_draft_label: str
    create_label: str
    current_step_key: str
    steps: list[AddNewFacultyEmployeeWizardStep]
    employment_section_title: str = "Employment details"
    field_meta: list[InstitutionFieldMeta] = Field(default_factory=list)
    form: AddNewFacultyEmployeeFormValues = Field(default_factory=AddNewFacultyEmployeeFormValues)
    employee_type_options: list[InstitutionFieldOption] = Field(default_factory=list)
    department_options: list[InstitutionFieldOption] = Field(default_factory=list)
    designation_options: list[InstitutionFieldOption] = Field(default_factory=list)
    employment_status_options: list[InstitutionFieldOption] = Field(default_factory=list)
    reporting_to_options: list[InstitutionFieldOption] = Field(default_factory=list)
    gender_options: list[InstitutionFieldOption] = Field(default_factory=list)
    document_checklist: list[InstitutionFieldOption] = Field(default_factory=list)
    access_card: AddNewFacultyEmployeeAccessCard = Field(default_factory=AddNewFacultyEmployeeAccessCard)
    employee_id_card: AddNewFacultyEmployeeIdCard = Field(default_factory=AddNewFacultyEmployeeIdCard)
    has_draft: bool = False
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AddNewFacultyEmployeeDraftUpdate(BaseModel):
    draft_id: str
    step_key: str | None = None
    values: dict[str, Any] = Field(default_factory=dict)


class AddNewFacultyEmployeeCreatePayload(BaseModel):
    draft_id: str
    values: dict[str, Any] | None = None


class AddNewFacultyEmployeeCreateResult(BaseModel):
    record_id: str
    employee_id: str | None = None
    detail_href: str
    message: str = "Employee record created"


class EmployeeProfileManagementFormValues(BaseModel):
    full_name: str = ""
    mobile: str = ""
    official_email: str = ""
    emergency_contact: str = ""
    address: str = ""
    reason_for_change: str = ""


class EmployeeProfileManagementLockedField(BaseModel):
    label: str
    subtitle: str
    icon_key: str = "lock"


class EmployeeProfileManagementLastUpdated(BaseModel):
    updated_by_label: str
    updated_at_label: str
    reason_label: str | None = None


class EmployeeProfilePickerRow(BaseModel):
    record_id: str
    employee_name: str
    employee_id_label: str
    manage_href: str


class EmployeeProfileManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    discard_label: str
    save_changes_label: str
    requires_record: bool = False
    select_employee_title: str | None = None
    select_employee_hint: str | None = None
    employee_directory_href: str | None = None
    employee_directory_label: str | None = None
    picker_rows: list[EmployeeProfilePickerRow] = Field(default_factory=list)
    record_id: str | None = None
    faculty_record_id: str | None = None
    detail_href: str | None = None
    profile_initials: str | None = None
    profile_name: str | None = None
    profile_badges: list[StudentDetailsBadge] = Field(default_factory=list)
    profile_summary_line: str | None = None
    email_display: str | None = None
    phone_display: str | None = None
    joined_label: str | None = None
    editable_section_title: str = "Editable profile"
    field_meta: list[InstitutionFieldMeta] = Field(default_factory=list)
    form: EmployeeProfileManagementFormValues = Field(default_factory=EmployeeProfileManagementFormValues)
    locked_fields_title: str = "Controlled by HR"
    locked_fields: list[EmployeeProfileManagementLockedField] = Field(default_factory=list)
    last_updated_title: str = "Last updated"
    last_updated: EmployeeProfileManagementLastUpdated | None = None
    audit_footer_note: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class EmployeeProfileManagementSavePayload(BaseModel):
    record_id: str
    values: dict[str, Any] = Field(default_factory=dict)


class DepartmentDesignationAssignmentFormValues(BaseModel):
    record_id: str = ""
    department_id: str = ""
    designation: str = ""
    reporting_to: str = ""
    effective_from: str = ""
    reason: str = ""


class DepartmentDesignationHistoryItem(BaseModel):
    key: str
    title: str
    date_label: str
    tone: str = "success"


class DepartmentDesignationApprovalStep(BaseModel):
    key: str
    label: str
    status_label: str
    tone: str


class FacultyAssignmentEmployeeOption(BaseModel):
    record_id: str
    label: str
    employee_id_label: str


class DepartmentDesignationAssignmentPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    cancel_label: str
    cancel_href: str
    save_label: str
    requires_record: bool = False
    select_employee_title: str | None = None
    select_employee_hint: str | None = None
    faculty_directory_href: str | None = None
    faculty_directory_label: str | None = None
    picker_rows: list[FacultyAssignmentEmployeeOption] = Field(default_factory=list)
    employee_display: str | None = None
    assignment_section_title: str = "Assignment"
    field_meta: list[InstitutionFieldMeta] = Field(default_factory=list)
    form: DepartmentDesignationAssignmentFormValues = Field(
        default_factory=DepartmentDesignationAssignmentFormValues
    )
    employee_options: list[InstitutionFieldOption] = Field(default_factory=list)
    department_options: list[InstitutionFieldOption] = Field(default_factory=list)
    designation_options: list[InstitutionFieldOption] = Field(default_factory=list)
    reporting_to_options: list[InstitutionFieldOption] = Field(default_factory=list)
    history_section_title: str = "Assignment history"
    history_items: list[DepartmentDesignationHistoryItem] = Field(default_factory=list)
    approval_section_title: str = "Approval"
    approval_steps: list[DepartmentDesignationApprovalStep] = Field(default_factory=list)
    has_unsaved_changes: bool = False
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class DepartmentDesignationAssignmentSavePayload(BaseModel):
    record_id: str
    values: dict[str, Any] = Field(default_factory=dict)


class FacultyAssignmentWorkflowStep(BaseModel):
    key: str
    label: str
    step_number: int
    status: str
    href: str | None = None


class FacultySubjectAllocationTableRow(BaseModel):
    course_id: str
    subject_name: str
    subject_code: str
    semester_label: str
    hours_label: str
    faculty_label: str
    faculty_record_id: str | None = None
    status_label: str | None = None
    status_tone: str | None = None


class FacultySubjectCapacityRow(BaseModel):
    faculty_record_id: str
    faculty_name: str
    hours_assigned_label: str
    hours_capacity_label: str
    assigned_hours: float
    capacity_hours: float
    load_tone: str


class FacultySubjectAllocationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    auto_suggest_label: str
    confirm_label: str
    semester_filter_label: str
    department_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    academic_year_options: list[StudentAdminDashboardFilterOption]
    department_options: list[StudentAdminDashboardFilterOption]
    semester_options: list[StudentAdminDashboardFilterOption]
    selected_academic_year: str
    selected_department_id: str
    selected_semester_label: str
    workflow_steps: list[FacultyAssignmentWorkflowStep]
    subjects_section_title: str
    table_headers: list[str]
    subject_rows: list[FacultySubjectAllocationTableRow]
    subjects_footer_label: str
    capacity_section_title: str
    capacity_rows: list[FacultySubjectCapacityRow]
    has_pending_suggestions: bool = False
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class FacultySubjectAllocationRowPayload(BaseModel):
    course_id: str
    faculty_record_id: str


class FacultySubjectAllocationConfirmPayload(BaseModel):
    academic_year_label: str
    semester_label: str
    department_id: str
    allocations: list[FacultySubjectAllocationRowPayload] = Field(default_factory=list)


class FacultySubjectAllocationFilterPayload(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None
    department_id: str | None = None


class FacultyWorkloadManagementTableRow(BaseModel):
    record_id: str
    faculty_name: str
    department_label: str
    theory_hours_label: str
    lab_hours_label: str
    total_hours_label: str
    policy_hours_label: str
    status_label: str
    status_tone: str
    timetable_href: str


class FacultyWorkloadManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    rebalance_label: str
    workload_section_title: str
    table_headers: list[str]
    workload_rows: list[FacultyWorkloadManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    kpis: list[UserDashboardKpi]
    selected_academic_year: str
    selected_semester_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class FacultyWorkloadRebalancePayload(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None


class FacultyTimetableGridColumn(BaseModel):
    key: str
    label: str


class FacultyTimetableGridCell(BaseModel):
    label: str
    is_empty: bool = False


class FacultyTimetableDayRow(BaseModel):
    day_key: str
    day_label: str
    cells: list[FacultyTimetableGridCell]


class FacultyTimetablePickerRow(BaseModel):
    record_id: str
    faculty_name: str
    employee_id_label: str
    timetable_href: str


class FacultyTimetablePageRead(BaseModel):
    page_title: str
    page_subtitle: str
    context_line: str
    print_label: str
    edit_slots_label: str
    edit_slots_href: str
    requires_record: bool = False
    select_faculty_title: str | None = None
    select_faculty_hint: str | None = None
    faculty_directory_href: str | None = None
    faculty_directory_label: str | None = None
    picker_rows: list[FacultyTimetablePickerRow] = Field(default_factory=list)
    record_id: str | None = None
    profile_initials: str | None = None
    profile_name: str | None = None
    profile_badges: list[StudentDetailsBadge] = Field(default_factory=list)
    profile_summary_line: str | None = None
    email_display: str | None = None
    phone_display: str | None = None
    joined_label: str | None = None
    weekly_section_title: str = "Weekly timetable"
    column_headers: list[str]
    time_columns: list[FacultyTimetableGridColumn]
    day_rows: list[FacultyTimetableDayRow]
    timetable_footer_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class EmployeeDocumentVerificationTableRow(BaseModel):
    document_id: str
    employee_name: str
    document_label: str
    uploaded_label: str
    status_label: str
    status_tone: str
    is_selected: bool = False


class EmployeeDocumentVerificationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    request_document_label: str
    request_document_href: str
    verify_all_label: str
    kpis: list[UserDashboardKpi]
    documents_section_title: str
    documents_footer_label: str
    table_headers: list[str]
    document_rows: list[EmployeeDocumentVerificationTableRow]
    preview_title: str
    preview_empty_label: str
    preview_file_name: str | None = None
    preview_meta_label: str | None = None
    browse_files_label: str
    browse_files_href: str | None = None
    decision_section_title: str
    result_field_label: str
    remarks_field_label: str
    result_options: list[InstitutionFieldOption]
    selected_document_id: str | None = None
    decision_result: str = ""
    decision_remarks: str = ""
    submit_decision_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class EmployeeDocumentVerificationDecisionPayload(BaseModel):
    document_id: str
    result: str
    remarks: str | None = None


class EmployeeDocumentVerificationVerifyAllPayload(BaseModel):
    pass


class EmployeeStatusManagementTableRow(BaseModel):
    request_id: str
    employee_name: str
    current_status_label: str
    new_status_label: str
    effective_label: str
    reason_label: str
    approval_status_label: str
    approval_status_tone: str


class EmployeeStatusManagementMixItem(BaseModel):
    status_key: str
    status_label: str
    count: int
    bar_percent: float
    tone: str


class EmployeeStatusPickerOption(BaseModel):
    record_id: str
    label: str


class EmployeeStatusManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    change_status_label: str
    change_status_href: str
    status_changes_section_title: str
    table_headers: list[str]
    status_change_rows: list[EmployeeStatusManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    status_mix_title: str
    status_mix_items: list[EmployeeStatusManagementMixItem]
    update_status_section_title: str
    employee_field_label: str
    new_status_field_label: str
    reason_field_label: str
    effective_date_field_label: str
    submit_status_label: str
    approve_status_label: str
    employee_picker_options: list[EmployeeStatusPickerOption]
    new_status_options: list[InstitutionFieldOption]
    selected_request_id: str | None = None
    form_record_id: str
    form_new_status: str
    form_reason: str
    form_effective_date: str
    updated_at_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class EmployeeStatusChangeSubmitPayload(BaseModel):
    record_id: str
    new_status: str
    reason: str = Field(min_length=2, max_length=500)
    effective_date: date | None = None
    approve_immediately: bool = False
    page: int = 1


class EmployeeStatusApprovePayload(BaseModel):
    request_id: str
    page: int = 1


class FacultyEmployeeHistoryTableRow(BaseModel):
    row_id: str
    date_label: str
    employee_name: str
    change_label: str
    actor_label: str
    reference_label: str


class FacultyEmployeeHistoryPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    history_section_title: str
    table_headers: list[str]
    history_rows: list[FacultyEmployeeHistoryTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AttendanceDashboardTrendPoint(BaseModel):
    date_label: str
    attendance_pct: float | None = None


class AttendanceDashboardDepartmentRow(BaseModel):
    department_id: str
    department_name: str
    student_count: int
    average_pct: float | None = None
    below_minimum_count: int = 0
    trend_direction: str = "flat"
    trend_label: str = "—"
    trend_tone: str = "muted"


class StudentAttendanceProgrammeRow(BaseModel):
    programme_code: str
    programme_label: str
    student_count: int
    average_pct: float | None = None
    below_minimum_count: int = 0


class StudentAttendanceDistributionBar(BaseModel):
    bucket_key: str
    label: str
    student_count: int
    share_pct: float = 0.0
    bar_tone: str = "info"


class StudentAttendanceOverviewPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    term_filter_label: str
    programme_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    term_options: list[StudentAdminDashboardFilterOption]
    programme_options: list[StudentAdminDashboardFilterOption]
    selected_term_key: str
    selected_programme_code: str
    kpis: list[UserDashboardKpi]
    programme_table_title: str
    programme_table_headers: list[str]
    programme_rows: list[StudentAttendanceProgrammeRow]
    programme_table_footer_label: str
    distribution_title: str
    distribution_bars: list[StudentAttendanceDistributionBar]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class DepartmentWiseAttendanceBarItem(BaseModel):
    department_code: str
    department_name: str
    average_pct: float | None = None


class DepartmentWiseAttendancePageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    term_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    term_options: list[StudentAdminDashboardFilterOption]
    selected_term_key: str
    department_table_title: str
    department_table_headers: list[str]
    department_rows: list[AttendanceDashboardDepartmentRow]
    department_table_footer_label: str
    bars_section_title: str
    department_bars: list[DepartmentWiseAttendanceBarItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class SubjectWiseAttendanceRow(BaseModel):
    subject_name: str
    subject_code: str
    faculty_label: str
    classes_held: int
    average_pct: float | None = None
    below_minimum_count: int = 0


class FacultyAttendanceTableRow(BaseModel):
    faculty_user_id: str
    faculty_name: str
    department_label: str
    present_count: int
    leave_count: int
    absent_count: int
    attendance_rate_pct: float | None = None


class FacultyAttendanceOverviewPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    scope_indicator_label: str
    updated_at_label: str
    late_arrivals_hint: str
    kpis: list[UserDashboardKpi]
    faculty_table_title: str
    faculty_table_headers: list[str]
    faculty_rows: list[FacultyAttendanceTableRow]
    table_footer_label: str
    table_pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AttendanceMonitoringTableRow(BaseModel):
    row_key: str
    class_label: str
    faculty_label: str
    time_label: str
    room_label: str
    delay_label: str
    action_label: str
    action_tone: str


class AttendanceMonitoringPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    notify_faculty_label: str
    scope_indicator_label: str
    updated_at_label: str
    not_marked_after_label: str
    kpis: list[UserDashboardKpi]
    not_marked_table_title: str
    not_marked_table_headers: list[str]
    not_marked_rows: list[AttendanceMonitoringTableRow]
    not_marked_table_footer_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AttendanceCorrectionApprovalStep(BaseModel):
    key: str
    label: str
    status_label: str
    tone: str


class AttendanceCorrectionRequestTableRow(BaseModel):
    row_key: str
    request_code: str
    faculty_label: str
    class_label: str
    session_date_label: str
    change_summary: str
    status_label: str
    status_tone: str
    review_href: str
    review_label: str


class AttendanceCorrectionRequestsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    updated_at_label: str
    kpis: list[UserDashboardKpi]
    requests_table_title: str
    requests_table_headers: list[str]
    request_rows: list[AttendanceCorrectionRequestTableRow]
    requests_table_footer_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AttendanceConfigurationFieldMeta(BaseModel):
    key: str
    label: str
    field_type: str = "select"


class AttendanceConfigurationToggleRule(BaseModel):
    key: str
    label: str
    description: str
    enabled: bool = False


class AttendanceConfigurationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    cancel_label: str
    save_label: str
    rules_policies_href: str
    rules_policies_link_label: str
    marking_section_title: str
    behaviour_section_title: str
    marking_window_key: str
    correction_window_key: str
    late_mark_after_key: str
    session_length_key: str
    marking_window_options: list[InstitutionFieldOption]
    correction_window_options: list[InstitutionFieldOption]
    late_mark_after_options: list[InstitutionFieldOption]
    session_length_options: list[InstitutionFieldOption]
    field_meta: list[AttendanceConfigurationFieldMeta]
    toggle_rules: list[AttendanceConfigurationToggleRule]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AttendanceConfigurationSave(BaseModel):
    marking_window_key: str
    correction_window_key: str
    late_mark_after_key: str
    session_length_key: str
    toggle_rules: dict[str, bool] = Field(default_factory=dict)


class AttendanceRulesPolicyTableRow(BaseModel):
    row_key: str
    policy_title: str
    value_label: str
    applies_to_label: str
    effective_label: str
    status_label: str
    status_tone: str


class AttendanceReportsTableRow(BaseModel):
    row_key: str
    report_title: str
    period_label: str
    format_label: str
    last_run_label: str
    schedule_label: str


class AttendanceReportsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    create_report_label: str
    reports_section_title: str
    reports_table_headers: list[str]
    report_rows: list[AttendanceReportsTableRow]
    reports_table_footer_label: str
    create_report_templates: list[InstitutionFieldOption]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AttendanceReportCreate(BaseModel):
    template_key: str
    title: str | None = Field(default=None, max_length=200)


class AttendanceRulesPoliciesPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    configuration_href: str
    back_label: str
    cancel_label: str
    save_label: str
    policies_section_title: str
    policies_table_headers: list[str]
    policy_rows: list[AttendanceRulesPolicyTableRow]
    policies_table_footer_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AttendanceApprovalPageRead(BaseModel):
    page_title: str
    selected_request_id: str | None = None
    request_code: str
    back_href: str
    back_label: str
    reject_label: str
    approve_label: str
    request_card_title: str
    faculty_field_label: str
    faculty_label: str
    class_field_label: str
    class_label: str
    date_field_label: str
    session_date_label: str
    change_field_label: str
    change_summary: str
    reason_field_label: str
    reason_text: str
    decision_card_title: str
    decision_field_label: str
    decision_required: bool
    decision_options: list[InstitutionFieldOption]
    selected_decision: str
    remarks_field_label: str
    remarks_placeholder: str
    remarks_value: str
    approval_route_title: str
    approval_steps: list[AttendanceCorrectionApprovalStep]
    can_decide: bool
    decide_blocked_message: str | None = None
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class SubjectWiseAttendancePageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    term_filter_label: str
    scope_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    term_options: list[StudentAdminDashboardFilterOption]
    scope_options: list[StudentAdminDashboardFilterOption]
    selected_term_key: str
    selected_scope_key: str
    subjects_table_title: str
    subjects_table_headers: list[str]
    subject_rows: list[SubjectWiseAttendanceRow]
    subjects_footer_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class AttendanceDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    open_reports_label: str
    open_reports_href: str
    term_filter_label: str
    department_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    term_options: list[StudentAdminDashboardFilterOption]
    department_options: list[StudentAdminDashboardFilterOption]
    selected_term_key: str
    selected_department_id: str
    kpis: list[UserDashboardKpi]
    department_table_title: str
    department_table_headers: list[str]
    department_rows: list[AttendanceDashboardDepartmentRow]
    department_table_footer_label: str
    trend_chart_title: str
    trend_series: list[AttendanceDashboardTrendPoint]
    needs_attention_title: str
    needs_attention_items: list[StudentAdminWorkQueueItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class FacultyEmployeeDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    add_faculty_label: str
    add_faculty_href: str
    academic_year_filter_label: str
    department_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    academic_year_options: list[StudentAdminDashboardFilterOption]
    department_options: list[StudentAdminDashboardFilterOption]
    selected_academic_year: str
    selected_department_id: str
    kpis: list[UserDashboardKpi]
    faculty_table_title: str
    faculty_table_headers: list[str]
    faculty_rows: list[FacultyEmployeeDashboardFacultyRow]
    faculty_table_pagination: PoliciesPagination
    faculty_view_all_href: str
    faculty_view_all_label: str
    designation_section_title: str
    designation_bars: list[DepartmentFacultyDesignationBar]
    needs_attention_title: str
    needs_attention_items: list[StudentAdminWorkQueueItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrDashboardLeaveRow(BaseModel):
    leave_request_id: str
    employee_name: str
    leave_type_label: str
    dates_label: str
    days_label: str
    approver_label: str
    status_label: str
    status_tone: str
    detail_href: str


class HrDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    open_portal_label: str
    open_portal_href: str
    kpis: list[UserDashboardKpi]
    leave_section_title: str
    leave_view_all_href: str
    leave_view_all_label: str
    table_headers: list[str]
    leave_rows: list[HrDashboardLeaveRow]
    showing_label: str
    pagination: PoliciesPagination
    needs_attention_title: str
    needs_attention_items: list[StudentAdminWorkQueueItem]
    generated_at: datetime


class LibraryDashboardIssueReturnRow(BaseModel):
    circulation_id: str
    member_name: str
    book_title: str
    issued_label: str
    due_label: str
    fine_label: str
    status_label: str
    status_tone: str
    detail_href: str


class LibraryDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    open_portal_label: str
    open_portal_href: str
    kpis: list[UserDashboardKpi]
    issue_return_section_title: str
    issue_return_view_all_href: str
    issue_return_view_all_label: str
    table_headers: list[str]
    issue_return_rows: list[LibraryDashboardIssueReturnRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    needs_attention_title: str
    needs_attention_items: list[StudentAdminWorkQueueItem]
    generated_at: datetime


class LibraryBranchManagementTableRow(BaseModel):
    branch_code: str
    branch_name: str
    location_label: str
    titles_label: str
    seats_label: str
    hours_label: str
    status_label: str
    status_tone: str
    detail_href: str


class LibraryBranchManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    add_branch_label: str
    add_branch_href: str
    branches_section_title: str
    branches_count_label: str
    table_headers: list[str]
    branch_rows: list[LibraryBranchManagementTableRow]
    empty_table_message: str
    generated_at: datetime


class LibraryBookCatalogueTableRow(BaseModel):
    book_id: str
    title: str
    isbn_label: str
    author_label: str
    category_label: str
    copies_label: str
    available_label: str
    detail_href: str


class LibraryBookCataloguePageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    add_title_label: str
    add_title_href: str
    search_placeholder: str
    category_filter_label: str
    branch_filter_label: str
    category_options: list[UserListFilterOption]
    branch_options: list[UserListFilterOption]
    catalogue_section_title: str
    table_headers: list[str]
    catalogue_rows: list[LibraryBookCatalogueTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibraryBookInventoryCopyRow(BaseModel):
    copy_id: str
    accession_label: str
    title: str
    branch_label: str
    shelf_label: str
    condition_label: str
    status_label: str
    status_tone: str
    detail_href: str


class LibraryBookInventoryPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    stock_verification_label: str
    stock_verification_href: str
    kpis: list[UserDashboardKpi]
    copies_section_title: str
    table_headers: list[str]
    copy_rows: list[LibraryBookInventoryCopyRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibraryBookAcquisitionTableRow(BaseModel):
    acquisition_id: str
    title: str
    requested_by_label: str
    copies_label: str
    cost_label: str
    status_label: str
    status_tone: str
    detail_href: str


class LibraryBookAcquisitionPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_request_label: str
    new_request_href: str
    acquisitions_section_title: str
    table_headers: list[str]
    acquisition_rows: list[LibraryBookAcquisitionTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibraryCirculationIssueReturnPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    issue_book_label: str
    issue_book_href: str
    issue_return_section_title: str
    table_headers: list[str]
    issue_return_rows: list[LibraryDashboardIssueReturnRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibraryReservationManagementTableRow(BaseModel):
    reservation_id: str
    title: str
    member_name: str
    queue_label: str
    reserved_label: str
    expires_label: str
    status_label: str
    status_tone: str
    detail_href: str


class LibraryReservationManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    reservations_section_title: str
    table_headers: list[str]
    reservation_rows: list[LibraryReservationManagementTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibraryMemberManagementTableRow(BaseModel):
    member_user_id: str
    member_name: str
    member_id_label: str
    type_label: str
    borrowing_limit_label: str
    on_loan_label: str
    status_label: str
    status_tone: str
    detail_href: str


class LibraryMemberManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    add_member_label: str
    add_member_href: str
    kpis: list[UserDashboardKpi]
    members_section_title: str
    table_headers: list[str]
    member_rows: list[LibraryMemberManagementTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibraryFineManagementTableRow(BaseModel):
    fine_id: str
    member_name: str
    book_title: str
    days_late_label: str
    fine_label: str
    status_label: str
    status_tone: str
    detail_href: str


class LibraryFineManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    kpis: list[UserDashboardKpi]
    fines_section_title: str
    table_headers: list[str]
    fine_rows: list[LibraryFineManagementTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibraryLostDamagedTableRow(BaseModel):
    report_id: str
    book_title: str
    member_name: str
    type_label: str
    recovery_label: str
    status_label: str
    status_tone: str
    detail_href: str


class LibraryLostDamagedPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    report_loss_label: str
    report_loss_href: str
    lost_damaged_section_title: str
    table_headers: list[str]
    report_rows: list[LibraryLostDamagedTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibrarySectionSubNavItem(BaseModel):
    key: str
    label: str
    href: str
    icon_key: str
    active: bool


class LibrarySectionSubNavRead(BaseModel):
    path: str
    section_key: str | None
    items: list[LibrarySectionSubNavItem]


class LibraryDigitalResourceTableRow(BaseModel):
    resource_id: str
    title: str
    type_label: str
    licence_label: str
    users_label: str
    expires_label: str
    status_label: str
    status_tone: str
    detail_href: str


class LibraryDigitalLibraryPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    add_resource_label: str
    add_resource_href: str
    digital_resources_section_title: str
    table_headers: list[str]
    resource_rows: list[LibraryDigitalResourceTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibraryReportsTableRow(BaseModel):
    report_type: str
    report_label: str
    period_label: str
    format_label: str
    last_run_label: str
    schedule_label: str
    detail_href: str


class LibraryReportsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    create_report_label: str
    create_report_href: str
    reports_section_title: str
    table_headers: list[str]
    report_rows: list[LibraryReportsTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class LibrarySettingsFormValues(BaseModel):
    student_borrow_limit: str
    faculty_borrow_limit: str
    loan_period_days: str
    renewals_allowed: str
    fine_per_day: str
    reservation_hold_days: str
    block_unpaid_fines: bool = True
    send_due_reminders: bool = True
    allow_external_members: bool = False


class LibrarySettingsToggleRule(BaseModel):
    key: str
    label: str
    description: str = ""
    badge_label: str = ""
    enabled: bool


class LibrarySettingsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    cancel_label: str
    save_label: str
    borrowing_rules_section_title: str
    controls_section_title: str
    field_meta: list[InstitutionFieldMeta]
    field_options: dict[str, list[InstitutionFieldOption]]
    form: LibrarySettingsFormValues
    toggle_rules: list[LibrarySettingsToggleRule]
    generated_at: datetime


class LibrarySettingsSave(BaseModel):
    form: LibrarySettingsFormValues


class HostelSectionSubNavItem(BaseModel):
    key: str
    label: str
    href: str
    icon_key: str
    active: bool


class HostelSectionSubNavRead(BaseModel):
    path: str
    section_key: str | None
    items: list[HostelSectionSubNavItem]


class HostelDashboardOutpassRow(BaseModel):
    request_id: str
    resident_label: str
    type_label: str
    from_label: str
    to_label: str
    guardian_label: str
    guardian_tone: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    open_portal_label: str
    open_portal_href: str
    kpis: list[UserDashboardKpi]
    outpass_section_title: str
    outpass_view_all_href: str
    outpass_view_all_label: str
    table_headers: list[str]
    outpass_rows: list[HostelDashboardOutpassRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    needs_attention_title: str
    needs_attention_items: list[StudentAdminWorkQueueItem]
    generated_at: datetime


class HostelManagementTableRow(BaseModel):
    row_id: str
    cells: list[str]
    status_label: str | None = None
    status_tone: str | None = None
    detail_href: str | None = None


class HostelManagementPageRead(BaseModel):
    screen_slug: str
    figma_frame: str
    page_title: str
    page_subtitle: str
    primary_action_label: str | None = None
    primary_action_href: str | None = None
    section_title: str
    count_label: str
    table_headers: list[str]
    rows: list[HostelManagementTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class HostelBuildingManagementTableRow(BaseModel):
    block_key: str
    block_label: str
    type_label: str
    floors_label: str
    rooms_label: str
    beds_label: str
    warden_label: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelBuildingManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    add_building_label: str
    add_building_href: str
    buildings_section_title: str
    table_headers: list[str]
    block_rows: list[HostelBuildingManagementTableRow]
    empty_table_message: str
    count_label: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class HostelRoomManagementTableRow(BaseModel):
    room_code: str
    room_label: str
    block_label: str
    floor_label: str
    type_label: str
    beds_label: str
    occupied_label: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelRoomManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    add_room_label: str
    add_room_href: str
    search_placeholder: str
    block_filter_label: str
    floor_filter_label: str
    type_filter_label: str
    block_options: list[UserListFilterOption]
    floor_options: list[UserListFilterOption]
    type_options: list[UserListFilterOption]
    rooms_section_title: str
    table_headers: list[str]
    room_rows: list[HostelRoomManagementTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class HostelAdmissionApplicationsTableRow(BaseModel):
    application_id: str
    application_label: str
    student_label: str
    year_label: str
    distance_label: str
    submitted_label: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelAdmissionApplicationsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    export_href: str
    kpis: list[UserDashboardKpi]
    applications_section_title: str
    table_headers: list[str]
    application_rows: list[HostelAdmissionApplicationsTableRow]
    empty_table_message: str
    count_label: str
    showing_label: str
    pagination: PoliciesPagination
    academic_year_label: str | None = None
    generated_at: datetime


class HostelBedAllocationTableRow(BaseModel):
    row_key: str
    student_label: str
    year_label: str
    preference_label: str
    allocated_bed_label: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelBedAllocationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    auto_allocate_label: str
    auto_allocate_href: str
    allocate_bed_label: str
    allocate_bed_href: str
    kpis: list[UserDashboardKpi]
    allocation_section_title: str
    table_headers: list[str]
    allocation_rows: list[HostelBedAllocationTableRow]
    empty_table_message: str
    count_label: str
    showing_label: str
    pagination: PoliciesPagination
    academic_year_label: str | None = None
    generated_at: datetime


class HostelResidentManagementTableRow(BaseModel):
    resident_key: str
    resident_label: str
    register_label: str
    room_label: str
    block_label: str
    fee_label: str
    fee_tone: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelResidentManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    export_href: str
    search_placeholder: str
    block_filter_label: str
    status_filter_label: str
    block_options: list[UserListFilterOption]
    status_options: list[UserListFilterOption]
    residents_section_title: str
    table_headers: list[str]
    resident_rows: list[HostelResidentManagementTableRow]
    empty_table_message: str
    count_label: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class HostelCheckInCheckoutTableRow(BaseModel):
    movement_key: str
    student_label: str
    room_label: str
    type_label: str
    date_label: str
    handover_label: str
    handover_tone: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelCheckInCheckoutPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    check_in_label: str
    check_in_href: str
    kpis: list[UserDashboardKpi]
    movements_section_title: str
    table_headers: list[str]
    movement_rows: list[HostelCheckInCheckoutTableRow]
    empty_table_message: str
    count_label: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class HostelFeeManagementTableRow(BaseModel):
    row_key: str
    resident_label: str
    room_label: str
    billed_label: str
    paid_label: str
    balance_label: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelFeeManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    generate_fees_label: str
    generate_fees_href: str
    kpis: list[UserDashboardKpi]
    fees_section_title: str
    table_headers: list[str]
    fee_rows: list[HostelFeeManagementTableRow]
    empty_table_message: str
    count_label: str
    showing_label: str
    pagination: PoliciesPagination
    academic_year_label: str | None = None
    generated_at: datetime


class HostelMessMenuRow(BaseModel):
    meal_key: str
    meal_label: str
    menu_label: str
    served_label: str


class HostelMessFeedbackDimension(BaseModel):
    key: str
    label: str
    score_label: str
    progress_percent: int
    tone: str


class HostelMessManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    edit_menu_label: str
    edit_menu_href: str
    kpis: list[UserDashboardKpi]
    menu_section_title: str
    menu_table_headers: list[str]
    menu_rows: list[HostelMessMenuRow]
    empty_menu_message: str
    feedback_section_title: str
    feedback_dimensions: list[HostelMessFeedbackDimension]
    generated_at: datetime


class HostelVisitorManagementTableRow(BaseModel):
    visit_key: str
    visitor_label: str
    visiting_label: str
    relation_label: str
    in_label: str
    out_label: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelVisitorManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    register_visitor_label: str
    register_visitor_href: str
    visitors_section_title: str
    table_headers: list[str]
    visitor_rows: list[HostelVisitorManagementTableRow]
    empty_table_message: str
    count_label: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class HostelLeaveOutpassApprovalTableRow(BaseModel):
    request_id: str
    resident_label: str
    type_label: str
    from_label: str
    to_label: str
    guardian_label: str
    guardian_tone: str
    status_label: str
    status_tone: str
    detail_href: str


class HostelLeaveOutpassApprovalPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    export_href: str
    outpass_section_title: str
    table_headers: list[str]
    outpass_rows: list[HostelLeaveOutpassApprovalTableRow]
    empty_table_message: str
    count_label: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class HostelReportsTableRow(BaseModel):
    report_key: str
    report_label: str
    period_label: str
    format_label: str
    last_run_label: str
    schedule_label: str
    detail_href: str


class HostelReportsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    create_report_label: str
    create_report_href: str
    reports_section_title: str
    table_headers: list[str]
    report_rows: list[HostelReportsTableRow]
    empty_table_message: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class HostelSettingsFormValues(BaseModel):
    gate_closing_boys: str = ""
    gate_closing_girls: str = ""
    visiting_hours: str = ""
    security_deposit: str = ""
    outpass_approver: str = ""
    mess_plans: str = ""
    notify_guardian_on_outpass: bool = False
    block_check_in_unpaid_fees: bool = False
    allow_visitors_after_hours: bool = False


class HostelSettingsToggleRule(BaseModel):
    key: str
    label: str
    description: str = ""
    badge_label: str = ""
    enabled: bool


class HostelSettingsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    cancel_label: str
    save_label: str
    hostel_rules_section_title: str
    controls_section_title: str
    field_meta: list[InstitutionFieldMeta]
    field_options: dict[str, list[InstitutionFieldOption]]
    form: HostelSettingsFormValues
    toggle_rules: list[HostelSettingsToggleRule]
    generated_at: datetime


class HostelSettingsSave(BaseModel):
    form: HostelSettingsFormValues


class HrRecruitmentSubNavItem(BaseModel):
    key: str
    label: str
    href: str


class HrRecruitmentVacancyRow(BaseModel):
    opening_id: str
    position_label: str
    department_label: str
    openings_count: int
    applicants_count: int
    closes_label: str
    status_label: str
    status_tone: str
    detail_href: str


class HrRecruitmentManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_vacancy_label: str
    new_vacancy_href: str
    kpis: list[UserDashboardKpi]
    sub_nav: list[HrRecruitmentSubNavItem]
    vacancies_section_title: str
    table_headers: list[str]
    vacancy_rows: list[HrRecruitmentVacancyRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrOnboardingStatusCell(BaseModel):
    label: str
    tone: str


class HrOnboardingTableRow(BaseModel):
    process_id: str
    employee_name: str
    joining_label: str
    documents: HrOnboardingStatusCell
    it_account: HrOnboardingStatusCell
    id_card: HrOnboardingStatusCell
    progress: HrOnboardingStatusCell
    detail_href: str


class HrEmployeeOnboardingPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_onboarding_label: str
    new_onboarding_href: str
    sub_nav: list[HrRecruitmentSubNavItem]
    onboarding_section_title: str
    table_headers: list[str]
    onboarding_rows: list[HrOnboardingTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrEmployeeAttendanceTableRow(BaseModel):
    employee_user_id: str
    employee_name: str
    department_label: str
    present_count: int
    leave_count: int
    absent_count: int
    attendance_rate_pct: float | None = None


class HrEmployeeAttendancePageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    sub_nav: list[HrRecruitmentSubNavItem]
    kpis: list[UserDashboardKpi]
    attendance_table_title: str
    attendance_table_headers: list[str]
    attendance_rows: list[HrEmployeeAttendanceTableRow]
    table_footer_label: str
    table_pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrLeaveManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    leave_policy_label: str
    leave_policy_href: str
    sub_nav: list[HrRecruitmentSubNavItem]
    kpis: list[UserDashboardKpi]
    applications_section_title: str
    table_headers: list[str]
    application_rows: list[HrDashboardLeaveRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrLeaveApprovalStep(BaseModel):
    key: str
    label: str
    status_label: str
    tone: str


class HrPayrollWorkflowStep(BaseModel):
    key: str
    label: str
    state: str


class HrSalaryStructureTableRow(BaseModel):
    structure_id: str
    structure_label: str
    applies_to_label: str
    components_count: int
    employees_count: int
    effective_label: str
    status_label: str
    status_tone: str
    detail_href: str


class HrSalaryStructureManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_structure_label: str
    new_structure_href: str
    sub_nav: list[HrRecruitmentSubNavItem]
    structures_section_title: str
    table_headers: list[str]
    structure_rows: list[HrSalaryStructureTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrPayrollExceptionRow(BaseModel):
    row_key: str
    employee_label: str
    issue_label: str
    impact_label: str
    owner_label: str
    status_label: str
    status_tone: str


class HrPayrollProcessingPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    validate_label: str
    process_payroll_label: str
    can_validate: bool
    can_process: bool
    action_blocked_message: str | None = None
    payroll_period_id: str | None = None
    payroll_run_id: str | None = None
    sub_nav: list[HrRecruitmentSubNavItem]
    workflow_steps: list[HrPayrollWorkflowStep]
    kpis: list[UserDashboardKpi]
    exceptions_section_title: str
    exception_table_headers: list[str]
    exception_rows: list[HrPayrollExceptionRow]
    exceptions_showing_label: str
    exceptions_pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrSalarySlipMonthRow(BaseModel):
    period_id: str
    month_label: str
    payroll_run_id: str | None = None
    employees_count: int
    generated_count: int | None = None
    published_count: int | None = None
    failed_count: int | None = None
    status_label: str
    status_tone: str


class HrSalarySlipManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    generate_label: str
    publish_label: str
    can_generate: bool
    can_publish: bool
    generate_blocked_message: str | None = None
    publish_blocked_message: str | None = None
    selected_payroll_run_id: str | None = None
    sub_nav: list[HrRecruitmentSubNavItem]
    slips_section_title: str
    table_headers: list[str]
    slip_rows: list[HrSalarySlipMonthRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrBenefitClaimTableRow(BaseModel):
    claim_id: str
    employee_name: str
    benefit_label: str
    category_label: str
    amount_label: str
    submitted_label: str
    status_label: str
    status_tone: str
    review_href: str


class HrEmployeeBenefitsClaimsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_program_label: str
    new_program_href: str
    sub_nav: list[HrRecruitmentSubNavItem]
    kpis: list[UserDashboardKpi]
    claims_section_title: str
    table_headers: list[str]
    claim_rows: list[HrBenefitClaimTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrPerformanceProgressRow(BaseModel):
    key: str
    label: str
    completed_count: int
    total_count: int
    progress_pct: float
    tone: str


class HrPerformanceManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    open_cycle_label: str
    can_open_cycle: bool
    open_cycle_blocked_message: str | None = None
    selected_cycle_id: str | None = None
    sub_nav: list[HrRecruitmentSubNavItem]
    kpis: list[UserDashboardKpi]
    progress_section_title: str
    progress_rows: list[HrPerformanceProgressRow]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrReportTableRow(BaseModel):
    row_id: str
    report_key: str
    report_label: str
    period_label: str
    format_label: str
    last_run_label: str
    schedule_label: str
    detail_href: str


class HrReportsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    create_report_label: str
    sub_nav: list[HrRecruitmentSubNavItem]
    reports_section_title: str
    table_headers: list[str]
    report_rows: list[HrReportTableRow]
    create_report_templates: list[InstitutionFieldOption]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrReportScheduleCreate(BaseModel):
    report_key: str = Field(min_length=1, max_length=64)


class HrSettingsPoliciesFormValues(BaseModel):
    working_week: str = "mon_sat"
    earned_leave_per_year: str = ""
    casual_leave_per_year: str = ""
    leave_approver: str = "hod_hr"
    probation_period_months: str = "12"
    payroll_cutoff_day: str = "25"
    carry_forward_earned_leave: bool = True
    auto_lock_attendance_before_payroll: bool = True
    self_service_salary_slips: bool = True


class HrSettingsPoliciesToggleRule(BaseModel):
    key: str
    label: str
    description: str = ""
    badge_label: str = ""
    enabled: bool


class HrSettingsPoliciesPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    cancel_label: str
    save_label: str
    policies_section_title: str
    controls_section_title: str
    sub_nav: list[HrRecruitmentSubNavItem]
    form: HrSettingsPoliciesFormValues
    field_meta: list[InstitutionFieldMeta]
    field_options: dict[str, list[InstitutionFieldOption]]
    toggle_rules: list[HrSettingsPoliciesToggleRule]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HrSettingsPoliciesSave(BaseModel):
    form: HrSettingsPoliciesFormValues


class HrLeaveApprovalPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    selected_leave_request_id: str | None = None
    back_href: str
    back_label: str
    return_label: str
    return_href: str
    reject_label: str
    approve_label: str
    application_card_title: str
    employee_field_label: str
    employee_label: str
    leave_type_field_label: str
    leave_type_label: str
    dates_field_label: str
    dates_label: str
    balance_after_field_label: str
    balance_after_label: str
    cover_field_label: str
    cover_label: str
    decision_card_title: str
    decision_field_label: str
    decision_required: bool
    decision_options: list[InstitutionFieldOption]
    selected_decision: str
    remarks_field_label: str
    remarks_placeholder: str
    remarks_value: str
    approval_timeline_title: str
    approval_steps: list[HrLeaveApprovalStep]
    can_decide: bool
    decide_blocked_message: str | None = None
    footer_disclaimer: str
    footer_snapshot_label: str
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


class StudentEnrollmentManagementTableRow(BaseModel):
    record_id: str
    student_name: str
    register_number: str
    programme_label: str
    semester_label: str
    fee_status_label: str
    fee_status_tone: str
    enrollment_status_label: str
    enrollment_status_tone: str
    detail_href: str
    is_selectable: bool = False


class StudentEnrollmentManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    enroll_selected_label: str
    term_filter_label: str
    programme_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    term_options: list[StudentAdminDashboardFilterOption]
    programme_options: list[StudentAdminDashboardFilterOption]
    selected_term_key: str
    selected_programme_code: str
    kpis: list[UserDashboardKpi]
    enrollment_section_title: str
    enrollment_count_label: str
    table_headers: list[str]
    enrollment_rows: list[StudentEnrollmentManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentEnrollmentBulkEnrollPayload(BaseModel):
    record_ids: list[str] = Field(default_factory=list)
    term_key: str
    programme_code: str | None = None
    page: int = 1


class BatchSectionAllocationSectionRow(BaseModel):
    section_id: str
    section_label: str
    programme_label: str
    semester_label: str
    strength_count: int
    capacity_count: int
    status_label: str
    status_tone: str


class BatchSectionAllocationUnallocatedRow(BaseModel):
    record_id: str
    student_name: str
    register_number: str
    programme_label: str
    detail_href: str


class BatchSectionAllocationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    auto_allocate_label: str
    confirm_label: str
    section_strength_title: str
    section_summary_label: str
    section_table_headers: list[str]
    section_rows: list[BatchSectionAllocationSectionRow]
    section_pagination: PoliciesPagination
    allocation_rules_title: str
    allocation_rules_fields: list[BatchSectionAllocationField]
    unallocated_title: str
    unallocated_summary_label: str
    unallocated_table_headers: list[str]
    unallocated_rows: list[BatchSectionAllocationUnallocatedRow]
    unallocated_pagination: PoliciesPagination
    updated_at_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class BatchSectionAllocationRulesSubmit(BaseModel):
    allocation_method: str = Field(min_length=2, max_length=32)
    max_per_section: int = Field(ge=1, le=500)
    keep_groups_together: str = Field(min_length=2, max_length=32)
    section_page: int = 1
    unallocated_page: int = 1


class StudentTransferManagementTableRow(BaseModel):
    request_key: str
    request_number: str
    student_name: str
    from_label: str
    to_label: str
    type_label: str
    status_label: str
    status_tone: str


class StudentTransferApprovalStep(BaseModel):
    key: str
    label: str
    status_label: str
    tone: str


class StudentTransferManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_transfer_label: str
    new_transfer_href: str
    requests_section_title: str
    table_headers: list[str]
    transfer_rows: list[StudentTransferManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    selected_request_key: str | None = None
    review_section_title: str
    review_student_field_label: str
    review_student_line: str
    review_transfer_type_field_label: str
    review_transfer_type_options: list[InstitutionFieldOption]
    review_transfer_type: str
    review_effective_field_label: str
    review_effective_options: list[InstitutionFieldOption]
    review_effective_semester: str
    review_reason_field_label: str
    review_reason: str
    save_review_label: str
    approve_college_label: str
    approval_route_title: str
    approval_steps: list[StudentTransferApprovalStep]
    updated_at_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentTransferReviewSavePayload(BaseModel):
    request_key: str
    transfer_type: str | None = None
    effective_semester: str | None = None
    reason: str | None = Field(default=None, max_length=1000)
    approve_college: bool = False
    page: int = 1


class StudentTransferCreatePageRead(BaseModel):
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    submit_label: str
    student_field_label: str
    transfer_type_field_label: str
    programme_field_label: str
    section_field_label: str
    institution_field_label: str
    effective_field_label: str
    reason_field_label: str
    student_options: list[InstitutionFieldOption]
    transfer_type_options: list[InstitutionFieldOption]
    programme_options: list[InstitutionFieldOption]
    effective_options: list[InstitutionFieldOption]
    generated_at: datetime


class StudentTransferRequestCreate(BaseModel):
    student_record_id: str
    transfer_type: str = Field(pattern=r"^(programme|section|outgoing)$")
    to_programme_code: str | None = None
    to_section_code: str | None = Field(default=None, max_length=32)
    to_institution_label: str | None = Field(default=None, max_length=200)
    effective_semester: str | None = Field(default=None, max_length=64)
    reason: str = Field(min_length=3, max_length=1000)


class StudentTransferRequestCreateResult(BaseModel):
    request_key: str
    transfer_href: str


class StudentPromotionRuleRow(BaseModel):
    rule_key: str
    rule_label: str
    requirement_label: str
    affected_label: str


class StudentPromotionManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    preview_label: str
    promote_eligible_label: str
    transition_filter_label: str
    programme_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    transition_options: list[StudentAdminDashboardFilterOption]
    programme_options: list[StudentAdminDashboardFilterOption]
    selected_transition_key: str
    selected_programme_code: str
    kpis: list[UserDashboardKpi]
    promotion_rules_section_title: str
    promotion_rules_footer_label: str
    promotion_rules_table_headers: list[str]
    promotion_rules_rows: list[StudentPromotionRuleRow]
    preview_note: str | None = None
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentPromotionPromotePayload(BaseModel):
    transition_key: str
    programme_code: str | None = None


class StudentStatusManagementTableRow(BaseModel):
    request_id: str
    student_name: str
    register_number: str
    current_status_label: str
    new_status_label: str
    reason_label: str
    approval_status_label: str
    approval_status_tone: str


class StudentStatusManagementMixItem(BaseModel):
    status_key: str
    status_label: str
    count: int
    bar_percent: float
    tone: str


class StudentStatusPickerOption(BaseModel):
    record_id: str
    label: str


class StudentStatusManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    change_status_label: str
    change_status_href: str
    status_changes_section_title: str
    table_headers: list[str]
    status_change_rows: list[StudentStatusManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    status_mix_title: str
    status_mix_items: list[StudentStatusManagementMixItem]
    update_status_section_title: str
    student_field_label: str
    new_status_field_label: str
    reason_field_label: str
    submit_status_label: str
    approve_status_label: str
    student_picker_options: list[StudentStatusPickerOption]
    new_status_options: list[InstitutionFieldOption]
    selected_request_id: str | None = None
    form_record_id: str
    form_new_status: str
    form_reason: str
    updated_at_label: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentStatusChangeSubmitPayload(BaseModel):
    record_id: str
    new_status_bucket: str
    reason: str = Field(min_length=2, max_length=500)
    approve_immediately: bool = False
    page: int = 1


class StudentStatusApprovePayload(BaseModel):
    request_id: str
    page: int = 1


class StudentWithdrawalWizardStep(BaseModel):
    key: str
    label: str
    step_number: int


class StudentWithdrawalClearanceRow(BaseModel):
    department_key: str
    department_label: str
    status_label: str
    status_tone: str
    cleared_on_label: str


class StudentWithdrawalProcessStep(BaseModel):
    key: str
    label: str
    status_label: str
    tone: str


class StudentWithdrawalDiscontinuationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    cancel_label: str
    cancel_href: str
    submit_for_approval_label: str
    wizard_steps: list[StudentWithdrawalWizardStep]
    active_step_key: str
    active_step_index: int
    withdrawal_request_section_title: str
    student_field_label: str
    type_field_label: str
    last_attendance_field_label: str
    reason_field_label: str
    student_line: str
    selected_record_id: str
    withdrawal_type: str
    last_attendance_date: str
    reason: str
    withdrawal_type_options: list[InstitutionFieldOption]
    clearances_section_title: str
    clearance_table_headers: list[str]
    clearance_rows: list[StudentWithdrawalClearanceRow]
    clearances_summary_label: str
    process_section_title: str
    process_steps: list[StudentWithdrawalProcessStep]
    request_id: str | None = None
    can_submit: bool
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentWithdrawalSavePayload(BaseModel):
    record_id: str
    request_id: str | None = None
    withdrawal_type: str | None = None
    last_attendance_date: str | None = None
    reason: str | None = None


class StudentWithdrawalSubmitPayload(BaseModel):
    record_id: str
    request_id: str | None = None
    withdrawal_type: str | None = None
    last_attendance_date: str | None = None
    reason: str | None = None


class StudentIdCardManagementTableRow(BaseModel):
    record_id: str
    card_id: str
    student_name: str
    card_number_label: str
    issued_label: str
    valid_until_label: str
    status_label: str
    status_tone: str


class StudentIdCardManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    bulk_print_label: str
    issue_card_label: str
    issue_card_href: str
    kpis: list[UserDashboardKpi]
    id_cards_section_title: str
    table_headers: list[str]
    card_rows: list[StudentIdCardManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentIdCardIssuePayload(BaseModel):
    record_id: str | None = None
    page: int = 1


class StudentIdCardBulkPrintPayload(BaseModel):
    record_ids: list[str] = Field(default_factory=list)
    page: int = 1


class StudentAcademicHistorySemesterRow(BaseModel):
    term_key: str
    semester_label: str
    year_label: str
    sgpa_label: str
    credits_label: str
    result_label: str
    result_tone: str
    attendance_label: str


class StudentAcademicHistoryChangeStep(BaseModel):
    key: str
    label: str
    date_label: str
    tone: str


class StudentAcademicHistoryPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    back_href: str
    back_label: str
    export_label: str
    selected_record_id: str
    profile_initials: str
    profile_name: str
    profile_badges: list[StudentDetailsBadge]
    profile_summary_line: str
    email: str
    phone: str
    admitted_label: str
    semester_record_section_title: str
    semester_table_headers: list[str]
    semester_rows: list[StudentAcademicHistorySemesterRow]
    semester_footer_label: str
    record_changes_section_title: str
    record_change_steps: list[StudentAcademicHistoryChangeStep]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ExaminationRegistrationSubNavItem(BaseModel):
    key: str
    label: str
    href: str
    active_slug: str
    active: bool = False


class ExamRegistrationManagementTableRow(BaseModel):
    registration_id: str
    student_name: str
    register_number: str
    programme_label: str
    subjects_count: int
    fee_status_label: str
    fee_status_tone: str
    eligibility_status_label: str
    eligibility_status_tone: str
    registration_status_label: str
    registration_status_tone: str
    submitted_at_label: str
    detail_href: str
    is_selectable: bool


class ExamRegistrationManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    confirm_selected_label: str
    search_placeholder: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    session_filter_label: str
    status_filter_label: str
    programme_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    session_options: list[StudentAdminDashboardFilterOption]
    status_options: list[StudentAdminDashboardFilterOption]
    programme_options: list[StudentAdminDashboardFilterOption]
    selected_session_id: str
    selected_status: str
    selected_programme_code: str
    registration_window_title: str
    registration_window_open_label: str
    registration_window_close_label: str
    registration_window_status_label: str
    registration_window_status_tone: str
    kpis: list[UserDashboardKpi]
    registrations_section_title: str
    registration_count_label: str
    table_headers: list[str]
    registration_rows: list[ExamRegistrationManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ExamRegistrationBulkConfirmPayload(BaseModel):
    registration_ids: list[str] = Field(default_factory=list)
    session_id: str
    status: str | None = None
    programme_code: str | None = None
    page: int = 1


class ExaminationDashboardSessionRow(BaseModel):
    session_id: str
    session_label: str
    type_label: str
    period_label: str
    programmes_label: str
    students_count: int
    status_label: str
    status_tone: str
    detail_href: str


class ExaminationDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    create_examination_label: str
    create_examination_href: str
    scope_indicator_label: str
    updated_at_label: str
    workflow_steps: list[FacultyAssignmentWorkflowStep]
    kpis: list[UserDashboardKpi]
    sessions_section_title: str
    sessions_count_label: str
    table_headers: list[str]
    session_rows: list[ExaminationDashboardSessionRow]
    showing_label: str
    pagination: PoliciesPagination
    pending_title: str
    pending_items: list[StudentAdminWorkQueueItem]
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class FinanceDashboardTransactionRow(BaseModel):
    transaction_id: str
    student_name: str
    invoice_label: str
    method_label: str
    amount_label: str
    status_label: str
    status_tone: str
    detail_href: str


class FinanceProgrammeCollectionItem(BaseModel):
    key: str
    label: str
    collection_percent: float
    bar_tone: str


class FeeStructureManagementTableRow(BaseModel):
    structure_id: str
    structure_label: str
    year_label: str
    programme_label: str
    total_label: str
    status_label: str
    status_tone: str
    detail_href: str


class FeeStructureManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    create_fee_structure_label: str
    create_fee_structure_href: str
    structures_section_title: str
    structures_count_label: str
    table_headers: list[str]
    structures: list[FeeStructureManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    info_notice_title: str
    info_notice_body: str
    generated_at: datetime


class StudentFeeManagementTableRow(BaseModel):
    assessment_id: str
    student_name: str
    register_number: str
    programme_label: str
    assessed_label: str
    concession_label: str
    status_label: str
    status_tone: str
    detail_href: str


class StudentFeeManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    bulk_assign_label: str
    bulk_assign_href: str
    kpis: list[UserDashboardKpi]
    student_fees_section_title: str
    student_fees_count_label: str
    table_headers: list[str]
    student_fees: list[StudentFeeManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class FeeDemandInvoiceManagementTableRow(BaseModel):
    invoice_id: str
    invoice_label: str
    student_name: str
    due_label: str
    total_label: str
    paid_label: str
    status_label: str
    status_tone: str
    detail_href: str


class FeeDemandInvoiceManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    generate_demands_label: str
    generate_demands_href: str
    publish_label: str
    publish_href: str
    kpis: list[UserDashboardKpi]
    invoices_section_title: str
    invoices_count_label: str
    table_headers: list[str]
    invoice_rows: list[FeeDemandInvoiceManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class FinanceDashboardPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    open_portal_label: str
    open_portal_href: str
    academic_year_filter_label: str
    programme_filter_label: str
    academic_year_options: list[StudentAdminDashboardFilterOption]
    programme_options: list[StudentAdminDashboardFilterOption]
    selected_academic_year: str
    selected_programme_code: str
    workflow_steps: list[FacultyAssignmentWorkflowStep]
    kpis: list[UserDashboardKpi]
    transactions_section_title: str
    transactions_count_label: str
    table_headers: list[str]
    transaction_rows: list[FinanceDashboardTransactionRow]
    showing_label: str
    pagination: PoliciesPagination
    collection_section_title: str
    programme_collection_items: list[FinanceProgrammeCollectionItem]
    generated_at: datetime


class FinancePaymentGatewayItem(BaseModel):
    gateway_key: str
    gateway_label: str
    detail_line: str
    status_label: str
    status_tone: str
    icon_variant: str


class FinanceOfflinePaymentTableRow(BaseModel):
    reference: str
    student_name: str
    method_label: str
    amount_label: str
    counter_label: str
    status_label: str
    status_tone: str
    detail_href: str


class OnlinePaymentMonitoringPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    verify_pending_label: str
    verify_pending_href: str
    kpis: list[UserDashboardKpi]
    sub_nav: list[YearsSemestersSubNavItem]
    transactions_section_title: str
    table_headers: list[str]
    transaction_rows: list[FinanceDashboardTransactionRow]
    showing_label: str
    pagination: PoliciesPagination
    gateways_section_title: str
    gateway_items: list[FinancePaymentGatewayItem]
    generated_at: datetime


class OfflinePaymentCollectionPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    record_payment_label: str
    record_payment_href: str
    kpis: list[UserDashboardKpi]
    sub_nav: list[YearsSemestersSubNavItem]
    payments_section_title: str
    table_headers: list[str]
    payment_rows: list[FinanceOfflinePaymentTableRow]
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class PaymentTransactionsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    export_href: str
    search_placeholder: str
    sub_nav: list[YearsSemestersSubNavItem]
    month_filter_label: str
    month_options: list[StudentAdminDashboardFilterOption]
    selected_month: str
    method_filter_label: str
    method_options: list[StudentAdminDashboardFilterOption]
    selected_method: str
    status_filter_label: str
    status_options: list[StudentAdminDashboardFilterOption]
    selected_status: str
    transactions_section_title: str
    table_headers: list[str]
    transaction_rows: list[FinanceDashboardTransactionRow]
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class FinanceReceiptTableRow(BaseModel):
    receipt_label: str
    student_name: str
    invoice_label: str
    amount_label: str
    date_label: str
    status_label: str
    status_tone: str
    detail_href: str


class FinanceOutstandingDuesTableRow(BaseModel):
    student_name: str
    invoice_label: str
    balance_label: str
    overdue_label: str
    detail_href: str


class FinanceAgingBucketItem(BaseModel):
    bucket_key: str
    label: str
    amount_label: str
    progress_percent: int
    bar_tone: str


class ReceiptManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    bulk_generate_label: str
    bulk_generate_href: str
    kpis: list[UserDashboardKpi]
    sub_nav: list[YearsSemestersSubNavItem]
    receipts_section_title: str
    table_headers: list[str]
    receipt_rows: list[FinanceReceiptTableRow]
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class OutstandingDuesManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    send_reminders_label: str
    send_reminders_href: str
    kpis: list[UserDashboardKpi]
    sub_nav: list[YearsSemestersSubNavItem]
    dues_section_title: str
    table_headers: list[str]
    dues_rows: list[FinanceOutstandingDuesTableRow]
    showing_label: str
    list_count_label: str
    pagination: PoliciesPagination
    aging_section_title: str
    aging_items: list[FinanceAgingBucketItem]
    generated_at: datetime


class FinanceScholarshipTableRow(BaseModel):
    scheme_label: str
    category_label: str
    students_label: str
    awarded_label: str
    applied_label: str
    status_label: str
    status_tone: str
    detail_href: str


class FinanceConcessionTableRow(BaseModel):
    student_name: str
    category_label: str
    requested_label: str
    date_label: str
    approver_label: str
    status_label: str
    status_tone: str
    detail_href: str


class FinanceRefundTableRow(BaseModel):
    refund_label: str
    student_name: str
    original_transaction_label: str
    amount_label: str
    requested_label: str
    stage_label: str
    stage_tone: str
    detail_href: str


class ScholarshipManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_programme_label: str
    new_programme_href: str
    kpis: list[UserDashboardKpi]
    sub_nav: list[YearsSemestersSubNavItem]
    scholarships_section_title: str
    table_headers: list[str]
    scholarship_rows: list[FinanceScholarshipTableRow]
    list_count_label: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class ConcessionWaiverManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_request_label: str
    new_request_href: str
    kpis: list[UserDashboardKpi]
    sub_nav: list[YearsSemestersSubNavItem]
    requests_section_title: str
    table_headers: list[str]
    concession_rows: list[FinanceConcessionTableRow]
    list_count_label: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class RefundManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_request_label: str
    new_request_href: str
    kpis: list[UserDashboardKpi]
    sub_nav: list[YearsSemestersSubNavItem]
    refunds_section_title: str
    table_headers: list[str]
    refund_rows: list[FinanceRefundTableRow]
    list_count_label: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class FinanceReconciliationBatchRow(BaseModel):
    batch_label: str
    source_label: str
    period_label: str
    matched_label: str
    unmatched_label: str
    status_label: str
    status_tone: str
    detail_href: str


class FinanceFinancialReportRow(BaseModel):
    report_key: str
    report_label: str
    period_label: str
    format_label: str
    last_run_label: str
    schedule_label: str
    detail_href: str


class PaymentReconciliationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    new_batch_label: str
    new_batch_href: str
    kpis: list[UserDashboardKpi]
    sub_nav: list[YearsSemestersSubNavItem]
    batches_section_title: str
    table_headers: list[str]
    batch_rows: list[FinanceReconciliationBatchRow]
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class FinancialReportsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    create_report_label: str
    create_report_href: str
    sub_nav: list[YearsSemestersSubNavItem]
    reports_section_title: str
    table_headers: list[str]
    report_rows: list[FinanceFinancialReportRow]
    list_count_label: str
    showing_label: str
    pagination: PoliciesPagination
    generated_at: datetime


class FinanceSettingsFormValues(BaseModel):
    invoice_prefix: str = "INV-{YYYY}-{#####}"
    receipt_prefix: str = "RCT-{YYMM}-{####}"
    financial_year_start: str = "april_1"
    refund_approver: str = "finance_manager_principal"
    late_fee_policy: str = "LF-2026"
    default_payment_methods: str = "upi,card,net_banking,cash"
    confirm_online_backend: bool = True
    lock_posted_entries: bool = True
    allow_installment_plans: bool = True


class FinanceSettingsToggleRule(BaseModel):
    key: str
    label: str
    description: str = ""
    badge_label: str = ""
    enabled: bool


class FinanceSettingsPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    cancel_label: str
    save_label: str
    configuration_section_title: str
    controls_section_title: str
    form: FinanceSettingsFormValues
    field_meta: list[InstitutionFieldMeta]
    field_options: dict[str, list[InstitutionFieldOption]]
    toggle_rules: list[FinanceSettingsToggleRule]
    generated_at: datetime


class FinanceSettingsSave(BaseModel):
    form: FinanceSettingsFormValues


class ExaminationSessionManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    create_session_label: str
    create_session_href: str
    sessions_section_title: str
    sessions_count_label: str
    table_headers: list[str]
    session_rows: list[ExaminationDashboardSessionRow]
    showing_label: str
    pagination: PoliciesPagination
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ExaminationSetupFormValues(BaseModel):
    session_name: str = ""
    examination_type: str = "regular"
    academic_year_label: str = ""
    semester_label: str = ""
    examination_start_at: str = ""
    examination_end_at: str = ""
    registration_end_at: str = ""
    result_target_at: str = ""


class ExaminationSetupFieldMeta(BaseModel):
    key: str
    label: str
    required: bool = False
    field_type: str = "text"


class ExaminationSetupToggleRule(BaseModel):
    key: str
    label: str
    description: str
    enabled: bool = False


class ExaminationConfigurationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    back_href: str
    save_draft_label: str
    continue_label: str
    continue_href: str
    setup_section_title: str
    rules_section_title: str
    form: ExaminationSetupFormValues
    field_meta: list[ExaminationSetupFieldMeta]
    type_options: list[StudentAdminDashboardFilterOption]
    academic_year_options: list[StudentAdminDashboardFilterOption]
    semester_options: list[StudentAdminDashboardFilterOption]
    toggle_rules: list[ExaminationSetupToggleRule]
    is_new: bool
    session_id: str | None = None
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ExaminationConfigurationSave(BaseModel):
    session_id: str | None = None
    form: ExaminationSetupFormValues
    toggle_rules: dict[str, bool] = Field(default_factory=dict)
    advance_workflow: bool = False


class ExamTimetableClashBanner(BaseModel):
    visible: bool
    headline: str
    description: str
    tone: str = "warning"


class ExamTimetableManagementRow(BaseModel):
    entry_code: str
    date_label: str
    session_label: str
    subject_label: str
    code_label: str
    programme_sem_label: str
    hall_label: str


class ExamTimetableManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    regenerate_label: str
    publish_label: str
    session_filter_label: str
    programme_filter_label: str
    scope_indicator_label: str
    updated_at_label: str
    session_options: list[StudentAdminDashboardFilterOption]
    programme_options: list[StudentAdminDashboardFilterOption]
    selected_session_id: str
    selected_programme_code: str
    clash_banner: ExamTimetableClashBanner
    timetable_section_title: str
    papers_count_label: str
    table_headers: list[str]
    rows: list[ExamTimetableManagementRow]
    showing_label: str
    pagination: PoliciesPagination
    timetable_status_label: str
    publish_enabled: bool
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ExamTimetableManagementActionPayload(BaseModel):
    session_id: str
    programme_code: str | None = None
    page: int = 1


class StudentExamEligibilityTableRow(BaseModel):
    student_name: str
    register_number: str
    reason_label: str
    attendance_label: str
    fee_status_label: str
    fee_status_tone: str
    decision_label: str
    decision_tone: str


class StudentExamEligibilityPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    rerun_check_label: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    scope_indicator_label: str
    updated_at_label: str
    kpis: list[UserDashboardKpi]
    ineligible_section_title: str
    ineligible_count_label: str
    table_headers: list[str]
    ineligible_rows: list[StudentExamEligibilityTableRow]
    showing_label: str
    pagination: PoliciesPagination
    selected_session_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class StudentExamEligibilityRerunPayload(BaseModel):
    session_id: str
    page: int = 1


class HallTicketAdministrationRow(BaseModel):
    hall_ticket_id: str
    student_name: str
    register_number: str
    papers_count: int
    generated_at_label: str
    released_at_label: str
    status_label: str
    status_tone: str


class HallTicketAdministrationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    generate_all_label: str
    release_label: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    scope_indicator_label: str
    updated_at_label: str
    kpis: list[UserDashboardKpi]
    hall_tickets_section_title: str
    hall_tickets_count_label: str
    table_headers: list[str]
    ticket_rows: list[HallTicketAdministrationRow]
    showing_label: str
    pagination: PoliciesPagination
    selected_session_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class HallTicketAdministrationActionPayload(BaseModel):
    session_id: str
    page: int = 1


class ExaminationHallSeatingHallRow(BaseModel):
    room_id: str
    hall_label: str
    capacity: int
    allocated_count: int
    papers_count: int
    status_label: str
    status_tone: str


class ExaminationHallSeatingSeatUsageItem(BaseModel):
    hall_label: str
    allocated_count: int
    capacity: int
    usage_label: str
    usage_percent: float


class ExaminationHallSeatingManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    auto_allocate_label: str
    confirm_label: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    halls_section_title: str
    seat_usage_section_title: str
    table_headers: list[str]
    hall_rows: list[ExaminationHallSeatingHallRow]
    seat_usage_items: list[ExaminationHallSeatingSeatUsageItem]
    showing_label: str
    pagination: PoliciesPagination
    selected_session_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ExaminationHallSeatingActionPayload(BaseModel):
    session_id: str
    page: int = 1


class InvigilatorAllocationDutyRow(BaseModel):
    duty_key: str
    date_label: str
    session_label: str
    hall_label: str
    invigilator_label: str
    substitute_label: str
    status_label: str
    status_tone: str


class InvigilatorAllocationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    auto_assign_label: str
    publish_roster_label: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    duties_section_title: str
    table_headers: list[str]
    duty_rows: list[InvigilatorAllocationDutyRow]
    showing_label: str
    pagination: PoliciesPagination
    selected_session_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class InvigilatorAllocationActionPayload(BaseModel):
    session_id: str
    page: int = 1


class MarksEntryManagementProgressRow(BaseModel):
    course_code: str
    subject_label: str
    faculty_label: str
    scripts_count: int
    entered_count: int
    verified_count: int
    status_label: str
    status_tone: str


class MarksEntryManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    send_reminders_label: str
    lock_entry_label: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    progress_section_title: str
    table_headers: list[str]
    progress_rows: list[MarksEntryManagementProgressRow]
    showing_label: str
    pagination: PoliciesPagination
    workflow_steps: list[FacultyAssignmentWorkflowStep]
    selected_session_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class MarksEntryManagementActionPayload(BaseModel):
    session_id: str
    page: int = 1


class InternalExternalAssessmentComponentRow(BaseModel):
    component_id: str
    component_label: str
    weight_label: str
    max_marks_label: str
    source_label: str


class InternalExternalAssessmentPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    save_label: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    assessment_pattern_section_title: str
    moderation_section_title: str
    table_headers: list[str]
    component_rows: list[InternalExternalAssessmentComponentRow]
    total_weight_label: str
    moderation_range_label: str
    pass_mark_label: str
    selected_moderation_range: str
    selected_pass_mark_percent: str
    moderation_range_options: list[StudentAdminDashboardFilterOption]
    pass_mark_options: list[StudentAdminDashboardFilterOption]
    selected_config_id: str
    selected_session_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class InternalExternalAssessmentSavePayload(BaseModel):
    session_id: str
    config_id: str
    moderation_range: str
    pass_mark_percent: str


class ResultProcessingPassBarRow(BaseModel):
    programme_code: str
    programme_label: str
    pass_percent: float
    pass_percent_label: str
    bar_tone: str


class ResultProcessingPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    process_label: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    pass_chart_section_title: str
    kpis: list[UserDashboardKpi]
    pass_by_programme: list[ResultProcessingPassBarRow]
    selected_session_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ResultProcessingActionPayload(BaseModel):
    session_id: str


class ResultApprovalProgrammeRow(BaseModel):
    programme_code: str
    programme_label: str
    students_count: int
    pass_count: int
    pass_percent_label: str


class ResultApprovalRouteStep(BaseModel):
    key: str
    title: str
    status_label: str
    status_tone: str


class ResultApprovalPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    return_label: str
    approve_label: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    summary_section_title: str
    route_section_title: str
    table_headers: list[str]
    programme_rows: list[ResultApprovalProgrammeRow]
    approval_route_steps: list[ResultApprovalRouteStep]
    showing_label: str
    pagination: PoliciesPagination
    selected_session_id: str
    selected_workflow_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ResultApprovalActionPayload(BaseModel):
    session_id: str
    page: int = 1
    workflow_id: str | None = None


class ResultPublicationProgrammeRow(BaseModel):
    programme_code: str
    programme_label: str
    students_count: int
    approved_label: str
    publish_at_label: str
    notify_label: str
    notify_tone: str
    ready_to_publish: bool
    publication_id: str


class ResultPublicationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    schedule_label: str
    publish_now_label: str
    warning_title: str
    warning_message: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    ready_section_title: str
    table_headers: list[str]
    programme_rows: list[ResultPublicationProgrammeRow]
    ready_count_label: str
    showing_label: str
    pagination: PoliciesPagination
    selected_session_id: str
    selected_workflow_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class ResultPublicationActionPayload(BaseModel):
    session_id: str
    page: int = 1
    publish_at: datetime | None = None


class RevaluationManagementTableRow(BaseModel):
    application_id: str
    request_label: str
    student_label: str
    subject_label: str
    fee_label: str
    result_label: str
    status_label: str
    status_tone: str


class RevaluationManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    requests_section_title: str
    table_headers: list[str]
    request_rows: list[RevaluationManagementTableRow]
    showing_label: str
    pagination: PoliciesPagination
    selected_session_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class SupplementaryArrearSubjectRow(BaseModel):
    course_code: str
    subject_label: str
    students_count: int
    date_label: str
    hall_label: str


class SupplementaryExaminationManagementPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    create_session_label: str
    create_session_href: str
    sub_nav: list[ExaminationRegistrationSubNavItem]
    eligible_hint_label: str
    arrear_subjects_section_title: str
    table_headers: list[str]
    arrear_subject_rows: list[SupplementaryArrearSubjectRow]
    kpis: list[UserDashboardKpi]
    showing_label: str
    pagination: PoliciesPagination
    selected_session_id: str
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class SupplementaryExaminationCreateSessionPayload(BaseModel):
    session_id: str | None = None
    page: int = 1
