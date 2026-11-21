export type FacultyDirectoryTableRow = {
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

export type FacultyDirectoryFilterOption = {
  value: string;
  label: string;
};

export type FacultyDirectoryPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type FacultyDirectoryPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  add_faculty_label: string;
  add_faculty_href: string;
  search_placeholder: string;
  department_filter_label: string;
  designation_filter_label: string;
  status_filter_label: string;
  department_options: FacultyDirectoryFilterOption[];
  designation_options: FacultyDirectoryFilterOption[];
  status_options: FacultyDirectoryFilterOption[];
  faculty_section_title: string;
  faculty_count_label: string;
  table_headers: string[];
  faculty_rows: FacultyDirectoryTableRow[];
  showing_label: string;
  pagination: FacultyDirectoryPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type FacultyDirectoryQuery = {
  page?: number;
  search?: string;
  department_id?: string;
  designation?: string;
  status_filter?: string;
  academic_year_code?: string;
};