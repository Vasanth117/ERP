import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";
import type { StudentAdminWorkQueueItem } from "@/features/college-admin/types/student-administration-dashboard";

export type HrDashboardLeaveRow = {
  leave_request_id: string;
  employee_name: string;
  leave_type_label: string;
  dates_label: string;
  days_label: string;
  approver_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HrDashboardPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HrDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  open_portal_label: string;
  open_portal_href: string;
  kpis: UserDashboardKpi[];
  leave_section_title: string;
  leave_view_all_href: string;
  leave_view_all_label: string;
  table_headers: string[];
  leave_rows: HrDashboardLeaveRow[];
  showing_label: string;
  pagination: HrDashboardPagination;
  needs_attention_title: string;
  needs_attention_items: StudentAdminWorkQueueItem[];
  generated_at: string;
};

export type HrDashboardPageQuery = {
  page?: number;
  page_size?: number;
};