export type FacultyAttendanceTableRow = {
  faculty_user_id: string;
  faculty_name: string;
  department_label: string;
  present_count: number;
  leave_count: number;
  absent_count: number;
  attendance_rate_pct: number | null;
};

export type FacultyAttendancePagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type FacultyAttendanceOverviewKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};

export type FacultyAttendanceOverviewPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  late_arrivals_hint: string;
  kpis: FacultyAttendanceOverviewKpi[];
  faculty_table_title: string;
  faculty_table_headers: string[];
  faculty_rows: FacultyAttendanceTableRow[];
  table_footer_label: string;
  table_pagination: FacultyAttendancePagination;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type FacultyAttendanceOverviewQuery = {
  department_id?: string;
  page?: number;
  page_size?: number;
};