import type {
  FinancePaymentUserDashboardKpi,
  FinancePaymentsPagination,
  FinancePaymentsSubNavItem,
} from "@/features/college-admin/types/finance-payments-shared";

export type OfflinePaymentCollectionPageQuery = {
  page?: number;
};

export type FinanceOfflinePaymentTableRow = {
  reference: string;
  student_name: string;
  method_label: string;
  amount_label: string;
  counter_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type OfflinePaymentCollectionPage = {
  page_title: string;
  page_subtitle: string;
  record_payment_label: string;
  record_payment_href: string;
  kpis: FinancePaymentUserDashboardKpi[];
  sub_nav: FinancePaymentsSubNavItem[];
  payments_section_title: string;
  table_headers: string[];
  payment_rows: FinanceOfflinePaymentTableRow[];
  showing_label: string;
  pagination: FinancePaymentsPagination;
  generated_at: string;
};