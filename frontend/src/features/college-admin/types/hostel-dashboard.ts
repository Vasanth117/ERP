import type { StudentAdminWorkQueueItem } from "@/features/college-admin/types/student-administration-dashboard";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HostelDashboardOutpassRow = {
  request_id: string;
  resident_label: string;
  type_label: string;
  from_label: string;
  to_label: string;
  guardian_label: string;
  guardian_tone: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelDashboardPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  open_portal_label: string;
  open_portal_href: string;
  kpis: UserDashboardKpi[];
  outpass_section_title: string;
  outpass_view_all_href: string;
  outpass_view_all_label: string;
  table_headers: string[];
  outpass_rows: HostelDashboardOutpassRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: HostelDashboardPagination;
  needs_attention_title: string;
  needs_attention_items: StudentAdminWorkQueueItem[];
  generated_at: string;
};

export type HostelDashboardPageQuery = {
  page?: number;
  page_size?: number;
};