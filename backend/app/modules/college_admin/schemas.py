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


class BrandingAssetRow(BaseModel):
    asset_key: str
    label: str
    detail_line: str
    status: str
    status_label: str
    editable: bool = True
    file_name: str | None = None


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


class AcademicYearSemesterForm(BaseModel):
    odd_semester_start: date | None = None
    odd_semester_end: date | None = None
    even_semester_start: date | None = None
    even_semester_end: date | None = None
    summer_term_start: date | None = None
    summer_term_end: date | None = None
    year_end_closing: date | None = None


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


class AcademicYearConfigurationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    copy_from_previous_label: str
    new_academic_year_label: str
    save_label: str
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


class PoliciesPagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    page_numbers: list[int]
    has_previous: bool
    has_next: bool


class InstitutionCalendarHolidayRow(BaseModel):
    holiday_id: str
    title: str
    date_label: str
    type_label: str
    applies_to_label: str


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
    send_invitation_email: bool = True
    send_sms_login_link: bool = False
    require_mfa_first_login: bool = True
    allow_sso_login: bool = True


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


class OrganizationalHierarchySelectedUnitRead(BaseModel):
    node_id: str
    unit_label: str
    reports_to_label: str
    head_label: str
    members_label: str


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


class DepartmentFacultyAllocationPageRead(BaseModel):
    page_title: str
    page_subtitle: str
    export_label: str
    allocate_faculty_label: str
    allocate_faculty_href: str
    semester_filter_label: str
    department_filter_label: str
    designation_filter_label: str
    scope_indicator_label: str
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
    faculty_field_label: str
    faculty_options: list[InstitutionFieldOption]
    allocate_to_field_label: str
    department_allocate_options: list[InstitutionFieldOption]
    allocation_type_field_label: str
    allocation_type_options: list[InstitutionFieldOption]
    effective_from_field_label: str
    form: DepartmentFacultyAllocationFormValues
    move_footer_note: str
    cancel_label: str
    save_label: str
    vacancies_section_title: str
    hr_recruitment_label: str
    hr_recruitment_href: str
    vacancy_items: list[DepartmentFacultyVacancyItem]
    designation_mix_section_title: str
    designation_bars: list[DepartmentFacultyDesignationBar]
    can_save: bool
    footer_disclaimer: str
    footer_snapshot_label: str
    generated_at: datetime


class DepartmentFacultyAllocationSavePayload(BaseModel):
    form: DepartmentFacultyAllocationFormValues


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
