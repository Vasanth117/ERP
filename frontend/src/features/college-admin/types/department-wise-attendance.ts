import type { AttendanceDashboardDepartmentRow } from "@/features/college-admin/types/attendance-dashboard";

export type DepartmentWiseAttendanceBarItem = {
  department_code: string;
  department_name: string;
  average_pct: number | null;
};

export type DepartmentWiseAttendancePage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  term_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  term_options: { value: string; label: string }[];
  selected_term_key: string;
  department_table_title: string;
  department_table_headers: string[];
  department_rows: AttendanceDashboardDepartmentRow[];
  department_table_footer_label: string;
  bars_section_title: string;
  department_bars: DepartmentWiseAttendanceBarItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type DepartmentWiseAttendanceQuery = {
  term_key?: string;
};