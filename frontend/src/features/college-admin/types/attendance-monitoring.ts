export type AttendanceMonitoringKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};

export type AttendanceMonitoringTableRow = {
  row_key: string;
  class_label: string;
  faculty_label: string;
  time_label: string;
  room_label: string;
  delay_label: string;
  action_label: string;
  action_tone: string;
};

export type AttendanceMonitoringPage = {
  page_title: string;
  page_subtitle: string;
  notify_faculty_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  not_marked_after_label: string;
  kpis: AttendanceMonitoringKpi[];
  not_marked_table_title: string;
  not_marked_table_headers: string[];
  not_marked_rows: AttendanceMonitoringTableRow[];
  not_marked_table_footer_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AttendanceMonitoringQuery = {
  page?: number;
  page_size?: number;
};