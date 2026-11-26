import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type LibraryFineManagementRow = {
  fine_id: string;
  member_name: string;
  book_title: string;
  days_late_label: string;
  fine_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LibraryFineManagementPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryFineManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  kpis: UserDashboardKpi[];
  fines_section_title: string;
  table_headers: string[];
  fine_rows: LibraryFineManagementRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryFineManagementPagination;
  generated_at: string;
};

export type LibraryFineManagementPageQuery = {
  page?: number;
  page_size?: number;
};