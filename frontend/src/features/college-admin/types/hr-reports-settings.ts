import type { HrRecruitmentPagination, HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type HrReportTableRow = {
  row_id: string;
  report_key: string;
  report_label: string;
  period_label: string;
  format_label: string;
  last_run_label: string;
  schedule_label: string;
  detail_href: string;
};

export type HrReportsPage = {
  page_title: string;
  page_subtitle: string;
  create_report_label: string;
  sub_nav: HrRecruitmentSubNavItem[];
  reports_section_title: string;
  table_headers: string[];
  report_rows: HrReportTableRow[];
  create_report_templates: InstitutionFieldOption[];
  showing_label: string;
  pagination: HrRecruitmentPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrReportsPageQuery = {
  page?: number;
  page_size?: number;
};

export type HrReportScheduleCreate = {
  report_key: string;
};

export type HrSettingsPoliciesFormValues = {
  working_week: string;
  earned_leave_per_year: string;
  casual_leave_per_year: string;
  leave_approver: string;
  probation_period_months: string;
  payroll_cutoff_day: string;
  carry_forward_earned_leave: boolean;
  auto_lock_attendance_before_payroll: boolean;
  self_service_salary_slips: boolean;
};

export type HrSettingsPoliciesToggleRule = {
  key: keyof HrSettingsPoliciesFormValues;
  label: string;
  description: string;
  badge_label: string;
  enabled: boolean;
};

export type HrSettingsPoliciesPage = {
  page_title: string;
  page_subtitle: string;
  cancel_label: string;
  save_label: string;
  policies_section_title: string;
  controls_section_title: string;
  sub_nav: HrRecruitmentSubNavItem[];
  form: HrSettingsPoliciesFormValues;
  field_meta: InstitutionFieldMeta[];
  field_options: Record<string, InstitutionFieldOption[]>;
  toggle_rules: HrSettingsPoliciesToggleRule[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};