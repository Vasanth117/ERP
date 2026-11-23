import type {
  AcademicTermSummary,
  HeadcountStatistics,
} from "@/features/college-admin/types/dashboard";

export type InstitutionAddress = {
  line1?: string | null;
  line2?: string | null;
  city?: string | null;
  district?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country?: string | null;
  latitude?: number | null;
  longitude?: number | null;
};

export type InstitutionProfile = {
  tenant_id: string;
  tenant_code: string;
  legal_name: string;
  display_name: string;
  short_name: string | null;
  institution_code: string | null;
  secondary_codes: string[];
  institution_email: string | null;
  contact_phone: string | null;
  contact_fax: string | null;
  official_website: string | null;
  description: string | null;
  address: InstitutionAddress;
  institution_type: string | null;
  affiliation_name: string | null;
  affiliation_type: string | null;
  affiliation_id: string | null;
  aishe_code: string | null;
  ownership_name: string | null;
  year_established: number | null;
  medium_of_instruction: string | null;
  accreditation_display: string | null;
  autonomous_status_valid_until: string | null;
  ugc_recognition: string | null;
  has_draft: boolean;
  timezone: string;
  locale: string;
  version: number;
  updated_at: string;
};

export type InstitutionProfileUpdate = Partial<
  Pick<
    InstitutionProfile,
    | "legal_name"
    | "display_name"
    | "short_name"
    | "institution_code"
    | "secondary_codes"
    | "institution_email"
    | "contact_phone"
    | "contact_fax"
    | "official_website"
    | "description"
    | "address"
    | "institution_type"
    | "affiliation_name"
    | "affiliation_type"
    | "affiliation_id"
    | "aishe_code"
    | "ownership_name"
    | "year_established"
    | "medium_of_instruction"
    | "accreditation_display"
    | "autonomous_status_valid_until"
    | "ugc_recognition"
  >
>;

export type InstitutionFieldOption = { value: string; label: string };

export type InstitutionFieldMeta = {
  key: string;
  label: string;
  required: boolean;
  locked: boolean;
  field_type: string;
};

export type InstitutionInformationFormValues = {
  legal_name: string;
  display_name: string;
  short_name: string | null;
  institution_code: string | null;
  year_established: number | null;
  institution_type: string | null;
  medium_of_instruction: string | null;
  description: string | null;
  affiliation_name: string | null;
  autonomous_status_valid_until: string | null;
  affiliation_id: string | null;
  aishe_code: string | null;
  ugc_recognition: string | null;
  ownership_name: string | null;
  institution_email: string | null;
  contact_phone: string | null;
  official_website: string | null;
  contact_fax: string | null;
};

export type BrandingAssetRow = {
  asset_key: string;
  label: string;
  detail_line: string;
  status: string;
  status_label: string;
  editable: boolean;
  file_name: string | null;
  file_id: string | null;
};

export type BrandingDocumentTemplateRow = {
  template_key: string;
  title: string;
  used_for: string;
  last_updated_label: string;
  status: string;
  status_label: string;
};

export type InstitutionBrandingFormValues = {
  primary_color: string;
  secondary_color: string;
  text_on_primary: string | null;
  accent_status: string | null;
  display_name: string | null;
};

export type InstitutionBrandingPage = {
  form: InstitutionBrandingFormValues;
  primary_logo: {
    upload_hint: string;
    current_summary: string | null;
    file_id: string | null;
  };
  color_fields: { key: string; label: string; value: string | null; required: boolean }[];
  document_templates: BrandingDocumentTemplateRow[];
  template_count_label: string;
  templates_manage_href: string;
  brand_assets: BrandingAssetRow[];
  preview_items: { title: string; description: string }[];
  preview_portal_href: string;
  footer_note: string;
  has_draft: boolean;
  generated_at: string;
};

export type InstitutionInformationPage = {
  form: InstitutionInformationFormValues;
  field_meta: InstitutionFieldMeta[];
  institution_type_options: InstitutionFieldOption[];
  medium_of_instruction_options: InstitutionFieldOption[];
  ugc_recognition_options: InstitutionFieldOption[];
  affiliation_options: InstitutionFieldOption[];
  approval_notice: { title: string; body: string };
  usage_contexts: { title: string; description: string }[];
  recent_changes: {
    change_id: string;
    title: string;
    detail_line: string;
    tone: string;
    occurred_at: string;
  }[];
  history_href: string;
  footer_note: string;
  has_draft: boolean;
  generated_at: string;
};

export type AcademicInstitutionFormValues = {
  academic_pattern: string;
  credit_system: string;
  working_days_per_semester: string;
  teaching_week: string;
  periods_per_day: string;
  period_duration_minutes: string;
  minimum_attendance_for_exams: string;
  condonation_band: string;
  attendance_calculation: string;
  medical_leave_counted_present: string;
  internal_external_weightage: string;
  pass_mark_external: string;
  pass_mark_overall: string;
  grading_scheme: string;
  allow_re_registration_failed_courses: boolean;
  enable_grace_marks: boolean;
  auto_detain_below_attendance: boolean;
  lock_marks_after_result_approval: boolean;
};

export type AcademicInstitutionFieldGroup = {
  key: string;
  title: string;
  field_keys: string[];
};

export type AcademicInstitutionToggleRule = {
  key: string;
  label: string;
  description: string;
  enabled: boolean;
};

export type AcademicInstitutionAppliesRow = {
  key: string;
  title: string;
  description: string;
  href: string | null;
  icon_slug: string;
  badge_label: string | null;
  badge_tone: string | null;
};

export type AcademicInstitutionSettingsPage = {
  page_title: string;
  page_subtitle: string;
  reset_label: string;
  save_label: string;
  footer_note: string;
  form: AcademicInstitutionFormValues;
  field_meta: InstitutionFieldMeta[];
  field_options: Record<string, InstitutionFieldOption[]>;
  field_groups: AcademicInstitutionFieldGroup[];
  toggle_rules: AcademicInstitutionToggleRule[];
  applies_to: AcademicInstitutionAppliesRow[];
  generated_at: string;
};

export type AcademicYearTableRow = {
  year_id: string;
  label: string;
  start_label: string;
  end_label: string;
  semesters_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type AcademicYearSemesterForm = {
  odd_semester_start: string | null;
  odd_semester_end: string | null;
  even_semester_start: string | null;
  even_semester_end: string | null;
  summer_term_start: string | null;
  summer_term_end: string | null;
  year_end_closing: string | null;
};

export type AcademicYearSemesterFieldMeta = {
  key: string;
  label: string;
  required: boolean;
  field_type: string;
};

export type AcademicYearTimelineItem = {
  item_id: string;
  title: string;
  date_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type AcademicYearLinkedConfig = {
  key: string;
  title: string;
  description: string;
  href: string;
  icon_slug: string;
};

export type AcademicYearConfigurationPage = {
  page_title: string;
  page_subtitle: string;
  copy_from_previous_label: string;
  new_academic_year_label: string;
  save_label: string;
  cancel_label: string;
  academic_years_table_title: string;
  archive_view_href: string;
  archive_view_label: string;
  academic_year_count_label: string;
  academic_years: AcademicYearTableRow[];
  selected_year_id: string | null;
  semester_section_title: string;
  semester_form: AcademicYearSemesterForm | null;
  semester_field_meta: AcademicYearSemesterFieldMeta[];
  year_timeline_title: string;
  timeline: AcademicYearTimelineItem[];
  linked_configuration_title: string;
  linked_configuration: AcademicYearLinkedConfig[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type InstitutionPolicyFilterOption = {
  value: string;
  label: string;
};

export type InstitutionPolicyRow = {
  policy_id: string;
  title: string;
  audience_label: string;
  version_label: string;
  effective_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type InstitutionPolicySelectedDetail = {
  policy_id: string;
  title: string;
  open_href: string;
  open_label: string;
  owner_label: string | null;
  approved_by_label: string | null;
  acknowledgement_requirement: string | null;
  acknowledgement_progress_label: string | null;
};

export type InstitutionPolicyReviewItem = {
  review_id: string;
  title: string;
  subtitle: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type PoliciesPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type InstitutionCalendarHolidayRow = {
  holiday_id: string;
  title: string;
  date_label: string;
  type_label: string;
  applies_to_label: string;
};

export type InstitutionCalendarFormValues = {
  working_days: string;
  saturday_pattern: string;
  day_start: string;
  day_end: string;
  publish_student_portal: boolean;
  publish_parent_app: boolean;
  send_reminders_day_before: boolean;
  sync_external_calendars: boolean;
};

export type InstitutionCalendarToggleRule = {
  key: string;
  label: string;
  description: string | null;
  enabled: boolean;
};

export type InstitutionCalendarTimeOption = {
  value: string;
  label: string;
};

export type InstitutionHolidayCreatePayload = {
  academic_year_id: string;
  title: string;
  start_date: string;
  end_date?: string | null;
  holiday_type?: string;
  applies_to?: string;
};

export type InstitutionHolidayCreateResult = {
  holiday_id: string;
  title: string;
  message: string;
};

export type InstitutionCalendarSettingsPage = {
  page_title: string;
  page_subtitle: string;
  import_holidays_label: string;
  save_label: string;
  cancel_label: string;
  holidays_section_title: string;
  add_holiday_label: string;
  add_holiday_href: string;
  add_holiday_dialog_title?: string;
  add_holiday_dialog_subtitle?: string;
  create_holiday_save_label?: string;
  create_holiday_cancel_label?: string;
  create_holiday_type_options?: InstitutionFieldOption[];
  create_holiday_applies_options?: InstitutionFieldOption[];
  holiday_table_headers: string[];
  holidays: InstitutionCalendarHolidayRow[];
  holiday_count_label: string;
  pagination: PoliciesPagination;
  selected_academic_year_id: string | null;
  working_week_title: string;
  publishing_title: string;
  form: InstitutionCalendarFormValues;
  working_days_options: InstitutionFieldOption[];
  saturday_pattern_options: InstitutionFieldOption[];
  time_options: InstitutionCalendarTimeOption[];
  working_days_meta: InstitutionFieldMeta;
  saturday_pattern_meta: InstitutionFieldMeta;
  day_start_meta: InstitutionFieldMeta;
  day_end_meta: InstitutionFieldMeta;
  publishing_toggles: InstitutionCalendarToggleRule[];
  footer_note: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type InstitutionPolicyCreatePayload = {
  title: string;
  category: string;
  audience: string;
  version_label?: string;
  effective_from?: string | null;
  status?: string;
  owner_label?: string | null;
  approved_by_label?: string | null;
  acknowledgement_requirement?: string | null;
};

export type InstitutionPolicyCreateResult = {
  policy_id: string;
  title: string;
  message: string;
};

export type InstitutionPoliciesPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  add_policy_label: string;
  add_policy_href: string;
  create_dialog_title?: string;
  create_dialog_subtitle?: string;
  create_save_label?: string;
  create_cancel_label?: string;
  create_category_options?: InstitutionPolicyFilterOption[];
  create_audience_options?: InstitutionPolicyFilterOption[];
  create_status_options?: InstitutionPolicyFilterOption[];
  search_placeholder: string;
  category_filter_label: string;
  audience_filter_label: string;
  status_filter_label: string;
  category_options: InstitutionPolicyFilterOption[];
  audience_options: InstitutionPolicyFilterOption[];
  status_options: InstitutionPolicyFilterOption[];
  policies: InstitutionPolicyRow[];
  policy_count_label: string;
  pagination: PoliciesPagination;
  selected_policy: InstitutionPolicySelectedDetail | null;
  review_schedule: InstitutionPolicyReviewItem[];
  review_schedule_title: string;
  selected_panel_prefix: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type InstitutionStatusBadge = {
  label: string;
  tone: "success" | "warning" | "info" | "muted";
};

export type InstitutionAboutField = {
  label: string;
  value: string | null;
};

export type InstitutionLeadershipRow = {
  name: string;
  role_label: string;
  detail_line: string | null;
};

export type ProfileCompletenessRow = {
  key: string;
  label: string;
  completed_count: number;
  total_count: number;
  progress_percent: number;
  status_label: string;
};

export type RelatedSettingLink = {
  key: string;
  title: string;
  description: string;
  href: string;
};

export type InstitutionProfilePage = {
  profile: InstitutionProfile;
  display_name: string;
  subtitle_line: string | null;
  location_label: string | null;
  status_badges: InstitutionStatusBadge[];
  about_fields: InstitutionAboutField[];
  leadership: InstitutionLeadershipRow[];
  profile_completeness: ProfileCompletenessRow[];
  related_settings: RelatedSettingLink[];
  branding_primary_color: string | null;
  branding_logo_file_id: string | null;
  footer_disclaimer: string;
  generated_at: string;
};

export type Campus = {
  campus_id: string;
  campus_code: string;
  name: string;
  is_main: boolean;
  is_active: boolean;
  address: InstitutionAddress;
  contact_email: string | null;
  contact_phone: string | null;
  timezone: string | null;
  locale: string | null;
  updated_at: string;
};

export type CampusCreate = {
  campus_code: string;
  name: string;
  is_main?: boolean;
  address?: InstitutionAddress;
  contact_email?: string | null;
  contact_phone?: string | null;
  timezone?: string | null;
  locale?: string | null;
};

export type CampusUpdate = Partial<
  Pick<
    Campus,
    | "name"
    | "is_main"
    | "is_active"
    | "address"
    | "contact_email"
    | "contact_phone"
    | "timezone"
    | "locale"
  >
> & {
  area_acres?: number | null;
  built_up_sq_m?: number | null;
  buildings_count?: number | null;
};

export type CampusDashboardKpi = {
  key: string;
  label: string;
  value: string;
  hint: string;
  hint_tone: string;
};

export type CampusDashboardRow = {
  campus_id: string;
  name: string;
  location_label: string;
  student_count: number;
  buildings_count: number;
  status_code: string;
  status_label: string;
  detail_href: string;
};

export type ClassroomUtilizationBar = {
  building_label: string;
  utilization_percent: number;
  tone: string;
};

export type CampusFacilitySummary = {
  key: string;
  title: string;
  description: string;
  icon_slug: string;
};

export type CampusOpenIssue = {
  issue_id: string;
  title: string;
  raised_label: string;
  status_code: string;
  status_label: string;
  tone: string;
};

export type CampusBuildingRow = {
  building_id: string;
  name: string;
  floors: number;
  classroom_count: number;
  laboratory_count: number;
  departments_label: string;
};

export type CampusSummaryStat = {
  key: string;
  label: string;
  value: string;
};

export type CampusFacilityStatusRow = {
  showcase_id: string;
  title: string;
  subtitle: string;
  status_code: string;
  status_label: string;
  icon_slug: string;
};

export type CampusDetailPage = {
  page_title: string;
  campus_id: string;
  campus_name: string;
  back_href: string;
  contact_href: string;
  buildings: CampusBuildingRow[];
  buildings_total: number;
  buildings_shown: number;
  buildings_footer_label: string;
  manage_buildings_href: string;
  view_all_buildings_href: string;
  summary_stats: CampusSummaryStat[];
  facility_statuses: CampusFacilityStatusRow[];
  generated_at: string;
};

export type CampusTabLink = {
  campus_id: string;
  name: string;
  href: string;
  is_active: boolean;
};

export type CampusOfficialContactRow = {
  contact_id: string;
  role_label: string;
  name: string;
  phone: string | null;
  email: string | null;
};

export type CampusEmergencyContactRow = {
  contact_id: string;
  label: string;
  phone: string;
};

export type CampusContactOfficialInput = {
  contact_id?: string | null;
  role_label: string;
  name: string;
  phone?: string | null;
  email?: string | null;
};

export type CampusContactEmergencyInput = {
  contact_id?: string | null;
  label: string;
  phone: string;
};

export type CampusContactPageSave = {
  address: InstitutionAddress;
  official_contacts: CampusContactOfficialInput[];
  emergency_contacts: CampusContactEmergencyInput[];
};

export type CampusContactPage = {
  page_title: string;
  campus_tabs: CampusTabLink[];
  address: InstitutionAddress;
  address_field_meta: InstitutionFieldMeta[];
  state_options: InstitutionFieldOption[];
  district_options: InstitutionFieldOption[];
  official_contacts: CampusOfficialContactRow[];
  contact_count_label: string;
  add_contact_enabled: boolean;
  usage_contexts: { title: string; description: string }[];
  emergency_contacts: CampusEmergencyContactRow[];
  footer_note: string;
  cancel_href: string;
  generated_at: string;
};

export type CampusManagementDashboard = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  add_campus_label: string;
  kpis: CampusDashboardKpi[];
  campuses: CampusDashboardRow[];
  campus_count_label: string;
  campuses_view_all_href: string;
  campus_details_href: string;
  classroom_utilization: ClassroomUtilizationBar[];
  classroom_utilization_hint: string | null;
  facilities: CampusFacilitySummary[];
  open_issues: CampusOpenIssue[];
  operations_href: string;
  add_campus_href: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type InstitutionBranding = {
  display_name?: string;
  primary_color?: string;
  secondary_color?: string;
  logo_file_id?: string;
  favicon_file_id?: string;
  theme?: Record<string, string>;
  version?: number;
};

export type InstitutionSettings = {
  tenant_id: string;
  settings: Record<string, unknown>;
  branding: InstitutionBranding | null;
  version: number;
  updated_at: string;
};

export type InstitutionSettingsPatch = {
  locale?: string;
  timezone?: string;
  date_format?: string;
  time_format?: string;
  academic_year_display?: string;
  semester_display?: string;
  grade_display_scale?: string;
  show_department_in_reports?: boolean;
  notification_digest_enabled?: boolean;
  inter_batch_section_transfer_requires_college_approval?: boolean;
  branding?: InstitutionBranding;
};

export type ConfigurationHistoryItem = {
  scope: string;
  version_number: number;
  changed_keys: string[];
  created_at: string;
  created_by: string | null;
};

export type ConfigurationChangeRow = {
  change_id: string;
  change_summary: string;
  setting_label: string;
  changed_by_label: string;
  when_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type ConfigurationChangeDetail = {
  change_id: string;
  setting_line: string;
  previous_value: string | null;
  new_value: string | null;
  approved_by_label: string | null;
  reason_line: string | null;
  applies_to_line: string | null;
  ip_line: string | null;
  open_href: string;
  open_label: string;
};

export type ConfigurationAreaSummary = {
  area_key: string;
  title: string;
  count: number;
  progress_percent: number;
};

export type ConfigurationHistoryFilterOption = {
  value: string;
  label: string;
};

export type ConfigurationHistoryPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  date_range_filter_label: string;
  setting_filter_label: string;
  user_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  date_range_options: ConfigurationHistoryFilterOption[];
  setting_options: ConfigurationHistoryFilterOption[];
  user_options: ConfigurationHistoryFilterOption[];
  change_log_title: string;
  table_headers: string[];
  changes: ConfigurationChangeRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  selected_change: ConfigurationChangeDetail | null;
  change_details_title: string;
  changes_by_area_title: string;
  changes_by_area: ConfigurationAreaSummary[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type CampusOverviewRow = {
  campus_id: string;
  campus_code: string;
  name: string;
  is_main: boolean;
  is_active: boolean;
  location_label: string;
  student_count: number;
  department_count: number;
};

export type ProgrammeLevelMixItem = {
  level: string;
  label: string;
  student_count: number;
  programme_count: number;
};

export type ComplianceStatusItem = {
  title: string;
  status_code: string;
  detail?: string | null;
};

export type KeyContactItem = {
  name: string;
  role_label: string;
  email?: string | null;
  phone?: string | null;
};

export type InstitutionalOverview = {
  profile: InstitutionProfile;
  academic_term: AcademicTermSummary;
  statistics: HeadcountStatistics;
  accreditation_summary: string | null;
  accreditation_detail: string | null;
  campuses: CampusOverviewRow[];
  programme_mix: ProgrammeLevelMixItem[];
  compliance_items: ComplianceStatusItem[];
  key_contacts: KeyContactItem[];
  generated_at: string;
};