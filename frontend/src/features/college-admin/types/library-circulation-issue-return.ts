import type { LibraryDashboardIssueReturnRow } from "@/features/college-admin/types/library-dashboard";

export type LibraryCirculationIssueReturnPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryCirculationIssueReturnPage = {
  page_title: string;
  page_subtitle: string;
  issue_book_label: string;
  issue_book_href: string;
  issue_return_section_title: string;
  table_headers: string[];
  issue_return_rows: LibraryDashboardIssueReturnRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryCirculationIssueReturnPagination;
  generated_at: string;
};

export type LibraryCirculationIssueReturnPageQuery = {
  page?: number;
  page_size?: number;
};