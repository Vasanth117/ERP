export type FinanceReconciliationSubNavItem = {
  key: string;
  label: string;
  href: string;
  active: boolean;
};

export type FinanceReconciliationPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type FinanceReconciliationUserDashboardKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};