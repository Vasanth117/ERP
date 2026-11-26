import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type HostelAdmissionApplicationsTableRow = {
  application_id: string;
  application_label: string;
  student_label: string;
  year_label: string;
  distance_label: string;
  submitted_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelAdmissionApplicationsPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelAdmissionApplicationsPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  export_href: string;
  kpis: UserDashboardKpi[];
  applications_section_title: string;
  table_headers: string[];
  application_rows: HostelAdmissionApplicationsTableRow[];
  empty_table_message: string;
  count_label: string;
  showing_label: string;
  pagination: HostelAdmissionApplicationsPagination;
  academic_year_label: string | null;
  generated_at: string;
};

export type HostelAdmissionApplicationsPageQuery = {
  page?: number;
  page_size?: number;
  academic_year_label?: string;
};