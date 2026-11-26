import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HostelFeeManagementTableRow = {
  row_key: string;
  resident_label: string;
  room_label: string;
  billed_label: string;
  paid_label: string;
  balance_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelFeeManagementPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelFeeManagementPage = {
  page_title: string;
  page_subtitle: string;
  generate_fees_label: string;
  generate_fees_href: string;
  kpis: UserDashboardKpi[];
  fees_section_title: string;
  table_headers: string[];
  fee_rows: HostelFeeManagementTableRow[];
  empty_table_message: string;
  count_label: string;
  showing_label: string;
  pagination: HostelFeeManagementPagination;
  academic_year_label: string | null;
  generated_at: string;
};

export type HostelFeeManagementPageQuery = {
  page?: number;
  page_size?: number;
};