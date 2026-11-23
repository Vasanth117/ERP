import type {
  FinanceReceiptsPagination,
  FinanceReceiptsSubNavItem,
  FinanceReceiptUserDashboardKpi,
} from "@/features/college-admin/types/finance-receipts-shared";

export type ReceiptManagementPageQuery = {
  page?: number;
};

export type FinanceReceiptTableRow = {
  receipt_label: string;
  student_name: string;
  invoice_label: string;
  amount_label: string;
  date_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type ReceiptManagementPage = {
  page_title: string;
  page_subtitle: string;
  bulk_generate_label: string;
  bulk_generate_href: string;
  kpis: FinanceReceiptUserDashboardKpi[];
  sub_nav: FinanceReceiptsSubNavItem[];
  receipts_section_title: string;
  table_headers: string[];
  receipt_rows: FinanceReceiptTableRow[];
  showing_label: string;
  pagination: FinanceReceiptsPagination;
  generated_at: string;
};