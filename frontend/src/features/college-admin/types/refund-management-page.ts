import type {
  FinanceAidPagination,
  FinanceAidSubNavItem,
  FinanceAidUserDashboardKpi,
} from "@/features/college-admin/types/finance-aid-shared";

export type RefundManagementPageQuery = {
  page?: number;
};

export type FinanceRefundTableRow = {
  refund_label: string;
  student_name: string;
  original_transaction_label: string;
  amount_label: string;
  requested_label: string;
  stage_label: string;
  stage_tone: string;
  detail_href: string;
};

export type RefundManagementPage = {
  page_title: string;
  page_subtitle: string;
  new_request_label: string;
  new_request_href: string;
  kpis: FinanceAidUserDashboardKpi[];
  sub_nav: FinanceAidSubNavItem[];
  refunds_section_title: string;
  table_headers: string[];
  refund_rows: FinanceRefundTableRow[];
  list_count_label: string;
  showing_label: string;
  pagination: FinanceAidPagination;
  generated_at: string;
};