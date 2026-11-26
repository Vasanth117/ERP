import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type LibraryMemberManagementRow = {
  member_user_id: string;
  member_name: string;
  member_id_label: string;
  type_label: string;
  borrowing_limit_label: string;
  on_loan_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LibraryMemberManagementPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryMemberManagementPage = {
  page_title: string;
  page_subtitle: string;
  add_member_label: string;
  add_member_href: string;
  kpis: UserDashboardKpi[];
  members_section_title: string;
  table_headers: string[];
  member_rows: LibraryMemberManagementRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryMemberManagementPagination;
  generated_at: string;
};

export type LibraryMemberManagementPageQuery = {
  page?: number;
  page_size?: number;
};