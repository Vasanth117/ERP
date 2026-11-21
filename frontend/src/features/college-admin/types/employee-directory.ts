export type EmployeeDirectoryTableRow = {
  record_id: string;
  employee_name: string;
  employee_id_label: string;
  unit_label: string;
  role_label: string;
  type_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type EmployeeDirectoryFilterOption = {
  value: string;
  label: string;
};

export type EmployeeDirectoryPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type EmployeeDirectoryPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  add_employee_label: string;
  add_employee_href: string;
  search_placeholder: string;
  unit_filter_label: string;
  role_filter_label: string;
  type_filter_label: string;
  status_filter_label: string;
  unit_options: EmployeeDirectoryFilterOption[];
  role_options: EmployeeDirectoryFilterOption[];
  type_options: EmployeeDirectoryFilterOption[];
  status_options: EmployeeDirectoryFilterOption[];
  employees_section_title: string;
  employees_count_label: string;
  table_headers: string[];
  employee_rows: EmployeeDirectoryTableRow[];
  showing_label: string;
  pagination: EmployeeDirectoryPagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type EmployeeDirectoryQuery = {
  page?: number;
  search?: string;
  unit_id?: string;
  role?: string;
  type_filter?: string;
  status_filter?: string;
};