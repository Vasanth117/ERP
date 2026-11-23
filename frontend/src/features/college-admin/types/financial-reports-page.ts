import type {
  FinanceReconciliationPagination,
  FinanceReconciliationSubNavItem,
} from "@/features/college-admin/types/finance-reconciliation-shared";

export type FinancialReportsPageQuery = {
  page?: number;
};

export type FinanceFinancialReportRow = {
  report_key: string;
  report_label: string;
  period_label: string;
  format_label: string;
  last_run_label: string;
  schedule_label: string;
  detail_href: string;
};

export type FinancialReportsPage = {
  page_title: string;
  page_subtitle: string;
  create_report_label: string;
  create_report_href: string;
  sub_nav: FinanceReconciliationSubNavItem[];
  reports_section_title: string;
  table_headers: string[];
  report_rows: FinanceFinancialReportRow[];
  list_count_label: string;
  showing_label: string;
  pagination: FinanceReconciliationPagination;
  generated_at: string;
};