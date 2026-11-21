export type AttendanceReportsTableRow = {
  row_key: string;
  report_title: string;
  period_label: string;
  format_label: string;
  last_run_label: string;
  schedule_label: string;
};

export type AttendanceFieldOption = { value: string; label: string };

export type AttendanceReportsPage = {
  page_title: string;
  page_subtitle: string;
  create_report_label: string;
  reports_section_title: string;
  reports_table_headers: string[];
  report_rows: AttendanceReportsTableRow[];
  reports_table_footer_label: string;
  create_report_templates: AttendanceFieldOption[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AttendanceReportCreatePayload = {
  template_key: string;
  title?: string;
};

export type AttendanceReportsQuery = {
  page?: number;
  page_size?: number;
};