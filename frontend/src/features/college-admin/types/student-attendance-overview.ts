export type StudentAttendanceOverviewFilterOption = {
  value: string;
  label: string;
};

export type StudentAttendanceOverviewKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};

export type StudentAttendanceProgrammeRow = {
  programme_code: string;
  programme_label: string;
  student_count: number;
  average_pct: number | null;
  below_minimum_count: number;
};

export type StudentAttendanceDistributionBar = {
  bucket_key: string;
  label: string;
  student_count: number;
  share_pct: number;
  bar_tone: string;
};

export type StudentAttendanceOverviewPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  term_filter_label: string;
  programme_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  term_options: StudentAttendanceOverviewFilterOption[];
  programme_options: StudentAttendanceOverviewFilterOption[];
  selected_term_key: string;
  selected_programme_code: string;
  kpis: StudentAttendanceOverviewKpi[];
  programme_table_title: string;
  programme_table_headers: string[];
  programme_rows: StudentAttendanceProgrammeRow[];
  programme_table_footer_label: string;
  distribution_title: string;
  distribution_bars: StudentAttendanceDistributionBar[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type StudentAttendanceOverviewQuery = {
  term_key?: string;
  programme_code?: string;
};