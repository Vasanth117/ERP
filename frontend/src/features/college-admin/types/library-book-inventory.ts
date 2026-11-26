import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type LibraryBookInventoryRow = {
  copy_id: string;
  accession_label: string;
  title: string;
  branch_label: string;
  shelf_label: string;
  condition_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LibraryBookInventoryPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryBookInventoryPage = {
  page_title: string;
  page_subtitle: string;
  stock_verification_label: string;
  stock_verification_href: string;
  kpis: UserDashboardKpi[];
  copies_section_title: string;
  table_headers: string[];
  copy_rows: LibraryBookInventoryRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryBookInventoryPagination;
  generated_at: string;
};

export type LibraryBookInventoryPageQuery = {
  page?: number;
  page_size?: number;
};