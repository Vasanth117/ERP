import type {
  FinanceReceiptsPagination,
  FinanceReceiptsSubNavItem,
  FinanceReceiptUserDashboardKpi,
} from "@/features/college-admin/types/finance-receipts-shared";

export type OutstandingDuesManagementPageQuery = {
  page?: number;
};

export type FinanceOutstandingDuesTableRow = {
  student_name: string;
  invoice_label: string;
  balance_label: string;
  overdue_label: string;
  detail_href: string;
};

export type FinanceAgingBucketItem = {
  bucket_key: string;
  label: string;
  amount_label: string;
  progress_percent: number;
  bar_tone: string;
};

export type OutstandingDuesManagementPage = {
  page_title: string;
  page_subtitle: string;
  send_reminders_label: string;
  send_reminders_href: string;
  kpis: FinanceReceiptUserDashboardKpi[];
  sub_nav: FinanceReceiptsSubNavItem[];
  dues_section_title: string;
  table_headers: string[];
  dues_rows: FinanceOutstandingDuesTableRow[];
  showing_label: string;
  list_count_label: string;
  pagination: FinanceReceiptsPagination;
  aging_section_title: string;
  aging_items: FinanceAgingBucketItem[];
  generated_at: string;
};