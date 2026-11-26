import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HrRecruitmentSubNavItem = {
  key: string;
  label: string;
  href: string;
};

export type HrRecruitmentVacancyRow = {
  opening_id: string;
  position_label: string;
  department_label: string;
  openings_count: number;
  applicants_count: number;
  closes_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HrRecruitmentPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HrRecruitmentManagementPage = {
  page_title: string;
  page_subtitle: string;
  new_vacancy_label: string;
  new_vacancy_href: string;
  kpis: UserDashboardKpi[];
  sub_nav: HrRecruitmentSubNavItem[];
  vacancies_section_title: string;
  table_headers: string[];
  vacancy_rows: HrRecruitmentVacancyRow[];
  showing_label: string;
  pagination: HrRecruitmentPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrOnboardingStatusCell = {
  label: string;
  tone: string;
};

export type HrOnboardingTableRow = {
  process_id: string;
  employee_name: string;
  joining_label: string;
  documents: HrOnboardingStatusCell;
  it_account: HrOnboardingStatusCell;
  id_card: HrOnboardingStatusCell;
  progress: HrOnboardingStatusCell;
  detail_href: string;
};

export type HrEmployeeOnboardingPage = {
  page_title: string;
  page_subtitle: string;
  new_onboarding_label: string;
  new_onboarding_href: string;
  sub_nav: HrRecruitmentSubNavItem[];
  onboarding_section_title: string;
  table_headers: string[];
  onboarding_rows: HrOnboardingTableRow[];
  showing_label: string;
  pagination: HrRecruitmentPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type HrRecruitmentPageQuery = {
  page?: number;
  page_size?: number;
};