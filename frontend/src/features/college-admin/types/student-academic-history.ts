export type StudentAcademicHistoryBadge = {
  key: string;
  label: string;
  tone: string;
};

export type StudentAcademicHistorySemesterRow = {
  term_key: string;
  semester_label: string;
  year_label: string;
  sgpa_label: string;
  credits_label: string;
  result_label: string;
  result_tone: string;
  attendance_label: string;
};

export type StudentAcademicHistoryChangeStep = {
  key: string;
  label: string;
  date_label: string;
  tone: string;
};

export type StudentAcademicHistoryPage = {
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  export_label: string;
  selected_record_id: string;
  profile_initials: string;
  profile_name: string;
  profile_badges: StudentAcademicHistoryBadge[];
  profile_summary_line: string;
  email: string;
  phone: string;
  admitted_label: string;
  semester_record_section_title: string;
  semester_table_headers: string[];
  semester_rows: StudentAcademicHistorySemesterRow[];
  semester_footer_label: string;
  record_changes_section_title: string;
  record_change_steps: StudentAcademicHistoryChangeStep[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};