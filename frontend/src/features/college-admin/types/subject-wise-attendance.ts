export type SubjectWiseAttendanceRow = {
  subject_name: string;
  subject_code: string;
  faculty_label: string;
  classes_held: number;
  average_pct: number | null;
  below_minimum_count: number;
};

export type SubjectWiseAttendancePage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  term_filter_label: string;
  scope_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  term_options: { value: string; label: string }[];
  scope_options: { value: string; label: string }[];
  selected_term_key: string;
  selected_scope_key: string;
  subjects_table_title: string;
  subjects_table_headers: string[];
  subject_rows: SubjectWiseAttendanceRow[];
  subjects_footer_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type SubjectWiseAttendanceQuery = {
  term_key?: string;
  scope_key?: string;
};