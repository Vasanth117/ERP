import type { StudentAdminWorkQueueItem } from "@/features/college-admin/types/student-administration-dashboard";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type LibraryDashboardIssueReturnRow = {
  circulation_id: string;
  member_name: string;
  book_title: string;
  issued_label: string;
  due_label: string;
  fine_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LibraryDashboardPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  open_portal_label: string;
  open_portal_href: string;
  kpis: UserDashboardKpi[];
  issue_return_section_title: string;
  issue_return_view_all_href: string;
  issue_return_view_all_label: string;
  table_headers: string[];
  issue_return_rows: LibraryDashboardIssueReturnRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryDashboardPagination;
  needs_attention_title: string;
  needs_attention_items: StudentAdminWorkQueueItem[];
  generated_at: string;
};

export type LibraryDashboardPageQuery = {
  page?: number;
  page_size?: number;
};