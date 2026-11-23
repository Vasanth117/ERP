import type {
  FinanceAidPagination,
  FinanceAidSubNavItem,
  FinanceAidUserDashboardKpi,
} from "@/features/college-admin/types/finance-aid-shared";

export type ConcessionWaiverManagementPageQuery = {
  page?: number;
};

export type FinanceConcessionTableRow = {
  student_name: string;
  category_label: string;
  requested_label: string;
  date_label: string;
  approver_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type ConcessionWaiverManagementPage = {
  page_title: string;
  page_subtitle: string;
  new_request_label: string;
  new_request_href: string;
  kpis: FinanceAidUserDashboardKpi[];
  sub_nav: FinanceAidSubNavItem[];
  requests_section_title: string;
  table_headers: string[];
  concession_rows: FinanceConcessionTableRow[];
  list_count_label: string;
  showing_label: string;
  pagination: FinanceAidPagination;
  generated_at: string;
};