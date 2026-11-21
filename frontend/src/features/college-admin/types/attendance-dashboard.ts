import type { StudentAdminWorkQueueItem } from "@/features/college-admin/types/student-administration-dashboard";

export type AttendanceDashboardFilterOption = {
  value: string;
  label: string;
};

export type AttendanceDashboardKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};

export type AttendanceDashboardDepartmentRow = {
  department_id: string;
  department_name: string;
  student_count: number;
  average_pct: number | null;
  below_minimum_count: number;
  trend_direction: string;
  trend_label: string;
  trend_tone: string;
};

export type AttendanceDashboardTrendPoint = {
  date_label: string;
  attendance_pct: number | null;
};

export type AttendanceDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  open_reports_label: string;
  open_reports_href: string;
  term_filter_label: string;
  department_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  term_options: AttendanceDashboardFilterOption[];
  department_options: AttendanceDashboardFilterOption[];
  selected_term_key: string;
  selected_department_id: string;
  kpis: AttendanceDashboardKpi[];
  department_table_title: string;
  department_table_headers: string[];
  department_rows: AttendanceDashboardDepartmentRow[];
  department_table_footer_label: string;
  trend_chart_title: string;
  trend_series: AttendanceDashboardTrendPoint[];
  needs_attention_title: string;
  needs_attention_items: StudentAdminWorkQueueItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AttendanceDashboardQuery = {
  term_key?: string;
  department_id?: string;
};