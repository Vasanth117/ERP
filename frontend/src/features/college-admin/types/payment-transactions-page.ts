import type {
  FinanceDashboardTransactionRow,
  FinancePaymentsPagination,
  FinancePaymentsSubNavItem,
} from "@/features/college-admin/types/finance-payments-shared";

export type PaymentTransactionsPageQuery = {
  page?: number;
  search?: string;
  month?: string;
  method?: string;
  status?: string;
};

export type PaymentTransactionsFilterOption = {
  value: string;
  label: string;
};

export type PaymentTransactionsPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  export_href: string;
  search_placeholder: string;
  sub_nav: FinancePaymentsSubNavItem[];
  month_filter_label: string;
  month_options: PaymentTransactionsFilterOption[];
  selected_month: string;
  method_filter_label: string;
  method_options: PaymentTransactionsFilterOption[];
  selected_method: string;
  status_filter_label: string;
  status_options: PaymentTransactionsFilterOption[];
  selected_status: string;
  transactions_section_title: string;
  table_headers: string[];
  transaction_rows: FinanceDashboardTransactionRow[];
  showing_label: string;
  pagination: FinancePaymentsPagination;
  generated_at: string;
};