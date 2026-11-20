import type { PoliciesPagination } from "@/features/college-admin/types/user-management-dashboard";

export type DepartmentListFilterOption = {
  value: string;
  label: string;
};

export type AllDepartmentsTableRow = {
  department_id: string;
  department_name: string;
  department_code: string;
  head_label: string;
  programme_count: number;
  student_count: number;
  faculty_count: number;
  status_code: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type AllDepartmentsListPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  create_department_label: string;
  create_department_href: string;
  search_placeholder: string;
  school_filter_label: string;
  type_filter_label: string;
  status_filter_label: string;
  school_options: DepartmentListFilterOption[];
  type_options: DepartmentListFilterOption[];
  status_options: DepartmentListFilterOption[];
  departments_section_title: string;
  departments_count_label: string;
  table_headers: string[];
  departments: AllDepartmentsTableRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};