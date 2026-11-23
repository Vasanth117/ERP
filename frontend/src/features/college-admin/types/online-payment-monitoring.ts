import type {
  FinanceDashboardTransactionRow,
  FinancePaymentUserDashboardKpi,
  FinancePaymentsPagination,
  FinancePaymentsSubNavItem,
} from "@/features/college-admin/types/finance-payments-shared";

export type OnlinePaymentMonitoringPageQuery = {
  page?: number;
};

export type FinancePaymentGatewayItem = {
  gateway_key: string;
  gateway_label: string;
  detail_line: string;
  status_label: string;
  status_tone: string;
  icon_variant: string;
};

export type OnlinePaymentMonitoringPage = {
  page_title: string;
  page_subtitle: string;
  verify_pending_label: string;
  verify_pending_href: string;
  kpis: FinancePaymentUserDashboardKpi[];
  sub_nav: FinancePaymentsSubNavItem[];
  transactions_section_title: string;
  table_headers: string[];
  transaction_rows: FinanceDashboardTransactionRow[];
  showing_label: string;
  pagination: FinancePaymentsPagination;
  gateways_section_title: string;
  gateway_items: FinancePaymentGatewayItem[];
  generated_at: string;
};