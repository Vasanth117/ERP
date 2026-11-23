export type FinancePaymentsSubNavItem = {
  key: string;
  label: string;
  href: string;
  active: boolean;
};

export type FinancePaymentsPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type FinanceDashboardTransactionRow = {
  transaction_id: string;
  student_name: string;
  invoice_label: string;
  method_label: string;
  amount_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type FinancePaymentUserDashboardKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};