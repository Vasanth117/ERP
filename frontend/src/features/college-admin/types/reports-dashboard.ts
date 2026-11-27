import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type ReportsSectionSubNavItem = {
  key: string;
  label: string;
  href: string;
  icon_key: string;
  active: boolean;
};

export type ReportsSectionSubNav = {
  path: string;
  section_key: string | null;
  items: ReportsSectionSubNavItem[];
};

export type ReportsDashboardTableRow = {
  row_id: string;
  report_label: string;
  period_label: string;
  format_label: string;
  last_run_label: string;
  schedule_label: string;
  detail_href: string;
};

export type ReportsDashboardGroupRow = {
  group_key: string;
  label: string;
  count_label: string;
  count_badge: string;
  icon_key: string;
  detail_href: string;
};

export type ReportsDashboardPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type ReportsDashboardPage = {
  page_title: string;
  page_subtitle: string;
  create_report_label: string;
  create_report_href: string;
  reports_section_title: string;
  groups_section_title: string;
  table_headers: string[];
  report_rows: ReportsDashboardTableRow[];
  group_rows: ReportsDashboardGroupRow[];
  empty_table_message: string;
  empty_groups_message: string;
  showing_label: string;
  kpis: UserDashboardKpi[];
  pagination: ReportsDashboardPagination;
  generated_at: string;
};

export type ReportsDashboardPageQuery = {
  page?: number;
  page_size?: number;
};