import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";
import type { StudentAdminWorkQueueItem } from "@/features/college-admin/types/student-administration-dashboard";

export type FacultyEmployeeDashboardFilterOption = {
  value: string;
  label: string;
};

export type FacultyEmployeeDashboardFacultyRow = {
  record_id: string;
  faculty_name: string;
  employee_id_label: string;
  department_label: string;
  designation_label: string;
  workload_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type FacultyEmployeeDesignationBar = {
  key: string;
  label: string;
  value: number;
  max_value: number;
};

export type FacultyEmployeeDashboardPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type FacultyEmployeeDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  add_faculty_label: string;
  add_faculty_href: string;
  academic_year_filter_label: string;
  department_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  academic_year_options: FacultyEmployeeDashboardFilterOption[];
  department_options: FacultyEmployeeDashboardFilterOption[];
  selected_academic_year: string;
  selected_department_id: string;
  kpis: UserDashboardKpi[];
  faculty_table_title: string;
  faculty_table_headers: string[];
  faculty_rows: FacultyEmployeeDashboardFacultyRow[];
  faculty_table_pagination: FacultyEmployeeDashboardPagination;
  faculty_view_all_href: string;
  faculty_view_all_label: string;
  designation_section_title: string;
  designation_bars: FacultyEmployeeDesignationBar[];
  needs_attention_title: string;
  needs_attention_items: StudentAdminWorkQueueItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type FacultyEmployeeDashboardQuery = {
  academic_year_code?: string;
  department_id?: string;
  page?: number;
  page_size?: number;
};