import type {
  FinanceReconciliationPagination,
  FinanceReconciliationSubNavItem,
  FinanceReconciliationUserDashboardKpi,
} from "@/features/college-admin/types/finance-reconciliation-shared";

export type PaymentReconciliationPageQuery = {
  page?: number;
};

export type FinanceReconciliationBatchRow = {
  batch_label: string;
  source_label: string;
  period_label: string;
  matched_label: string;
  unmatched_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type PaymentReconciliationPage = {
  page_title: string;
  page_subtitle: string;
  new_batch_label: string;
  new_batch_href: string;
  kpis: FinanceReconciliationUserDashboardKpi[];
  sub_nav: FinanceReconciliationSubNavItem[];
  batches_section_title: string;
  table_headers: string[];
  batch_rows: FinanceReconciliationBatchRow[];
  showing_label: string;
  pagination: FinanceReconciliationPagination;
  generated_at: string;
};