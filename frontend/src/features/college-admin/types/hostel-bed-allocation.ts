import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HostelBedAllocationTableRow = {
  row_key: string;
  student_label: string;
  year_label: string;
  preference_label: string;
  allocated_bed_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelBedAllocationPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelBedAllocationPage = {
  page_title: string;
  page_subtitle: string;
  auto_allocate_label: string;
  auto_allocate_href: string;
  allocate_bed_label: string;
  allocate_bed_href: string;
  kpis: UserDashboardKpi[];
  allocation_section_title: string;
  table_headers: string[];
  allocation_rows: HostelBedAllocationTableRow[];
  empty_table_message: string;
  count_label: string;
  showing_label: string;
  pagination: HostelBedAllocationPagination;
  academic_year_label: string | null;
  generated_at: string;
};

export type HostelBedAllocationPageQuery = {
  page?: number;
  page_size?: number;
  academic_year_label?: string;
};