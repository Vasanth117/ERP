import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HostelCheckInCheckoutTableRow = {
  movement_key: string;
  student_label: string;
  room_label: string;
  type_label: string;
  date_label: string;
  handover_label: string;
  handover_tone: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelCheckInCheckoutPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelCheckInCheckoutPage = {
  page_title: string;
  page_subtitle: string;
  check_in_label: string;
  check_in_href: string;
  kpis: UserDashboardKpi[];
  movements_section_title: string;
  table_headers: string[];
  movement_rows: HostelCheckInCheckoutTableRow[];
  empty_table_message: string;
  count_label: string;
  showing_label: string;
  pagination: HostelCheckInCheckoutPagination;
  generated_at: string;
};

export type HostelCheckInCheckoutPageQuery = {
  page?: number;
  page_size?: number;
};