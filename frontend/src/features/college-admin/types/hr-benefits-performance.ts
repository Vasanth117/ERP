import type { HrRecruitmentPagination, HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HrBenefitClaimTableRow = {
  claim_id: string;
  employee_name: string;
  benefit_label: string;
  category_label: string;
  amount_label: string;
  submitted_label: string;
  status_label: string;
  status_tone: string;
  review_href: string;
};

export type HrEmployeeBenefitsClaimsPage = {
  page_title: string;
  page_subtitle: string;
  new_program_label: string;
  new_program_href: string;
  sub_nav: HrRecruitmentSubNavItem[];
  kpis: UserDashboardKpi[];
  claims_section_title: string;
  table_headers: string[];
  claim_rows: HrBenefitClaimTableRow[];
  showing_label: string;
  pagination: HrRecruitmentPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrPerformanceProgressRow = {
  key: string;
  label: string;
  completed_count: number;
  total_count: number;
  progress_pct: number;
  tone: string;
};

export type HrPerformanceManagementPage = {
  page_title: string;
  page_subtitle: string;
  open_cycle_label: string;
  can_open_cycle: boolean;
  open_cycle_blocked_message: string | null;
  selected_cycle_id: string | null;
  sub_nav: HrRecruitmentSubNavItem[];
  kpis: UserDashboardKpi[];
  progress_section_title: string;
  progress_rows: HrPerformanceProgressRow[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrBenefitsPageQuery = {
  page?: number;
  page_size?: number;
};