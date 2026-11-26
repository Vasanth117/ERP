import type { HrRecruitmentPagination, HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HrPayrollWorkflowStep = {
  key: string;
  label: string;
  state: "complete" | "current" | "upcoming" | string;
};

export type HrSalaryStructureTableRow = {
  structure_id: string;
  structure_label: string;
  applies_to_label: string;
  components_count: number;
  employees_count: number;
  effective_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HrSalaryStructureManagementPage = {
  page_title: string;
  page_subtitle: string;
  new_structure_label: string;
  new_structure_href: string;
  sub_nav: HrRecruitmentSubNavItem[];
  structures_section_title: string;
  table_headers: string[];
  structure_rows: HrSalaryStructureTableRow[];
  showing_label: string;
  pagination: HrRecruitmentPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrPayrollExceptionRow = {
  row_key: string;
  employee_label: string;
  issue_label: string;
  impact_label: string;
  owner_label: string;
  status_label: string;
  status_tone: string;
};

export type HrPayrollProcessingPage = {
  page_title: string;
  page_subtitle: string;
  validate_label: string;
  process_payroll_label: string;
  can_validate: boolean;
  can_process: boolean;
  action_blocked_message: string | null;
  payroll_period_id: string | null;
  payroll_run_id: string | null;
  sub_nav: HrRecruitmentSubNavItem[];
  workflow_steps: HrPayrollWorkflowStep[];
  kpis: UserDashboardKpi[];
  exceptions_section_title: string;
  exception_table_headers: string[];
  exception_rows: HrPayrollExceptionRow[];
  exceptions_showing_label: string;
  exceptions_pagination: HrRecruitmentPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrSalarySlipMonthRow = {
  period_id: string;
  month_label: string;
  payroll_run_id: string | null;
  employees_count: number;
  generated_count: number | null;
  published_count: number | null;
  failed_count: number | null;
  status_label: string;
  status_tone: string;
};

export type HrSalarySlipManagementPage = {
  page_title: string;
  page_subtitle: string;
  generate_label: string;
  publish_label: string;
  can_generate: boolean;
  can_publish: boolean;
  generate_blocked_message: string | null;
  publish_blocked_message: string | null;
  selected_payroll_run_id: string | null;
  sub_nav: HrRecruitmentSubNavItem[];
  slips_section_title: string;
  table_headers: string[];
  slip_rows: HrSalarySlipMonthRow[];
  showing_label: string;
  pagination: HrRecruitmentPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrPayrollPageQuery = {
  page?: number;
  page_size?: number;
};