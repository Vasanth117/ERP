import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type LmsReportsTableRow = {
  report_key: string;
  report_label: string;
  period_label: string;
  format_label: string;
  last_run_label: string;
  schedule_label: string;
  detail_href: string;
};

export type LmsReportsPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LmsReportsPage = {
  page_title: string;
  page_subtitle: string;
  create_report_label: string;
  reports_section_title: string;
  table_headers: string[];
  report_rows: LmsReportsTableRow[];
  create_report_templates: InstitutionFieldOption[];
  empty_table_message: string;
  showing_label: string;
  pagination: LmsReportsPagination;
  generated_at: string;
};

export type LmsReportsPageQuery = {
  page?: number;
  page_size?: number;
};

export type LmsSettingsFormValues = {
  max_upload_size_mb: string;
  allowed_formats: string;
  late_submission: string;
  quiz_attempts: string;
  video_retention_years: string;
  completion_threshold_percent: string;
  require_content_review: boolean;
  allow_video_download: boolean;
  plagiarism_check_assignments: boolean;
};

export type LmsSettingsToggleRule = {
  key: string;
  label: string;
  description?: string | null;
  badge_label?: string | null;
  enabled: boolean;
};

export type LmsSettingsPage = {
  page_title: string;
  page_subtitle: string;
  cancel_label: string;
  save_label: string;
  limits_section_title: string;
  controls_section_title: string;
  field_meta: InstitutionFieldMeta[];
  field_options: Record<string, InstitutionFieldOption[]>;
  form: LmsSettingsFormValues;
  toggle_rules: LmsSettingsToggleRule[];
  generated_at: string;
};