export type StudentEnrollmentManagementTableRow = {
  record_id: string;
  student_name: string;
  register_number: string;
  programme_label: string;
  semester_label: string;
  fee_status_label: string;
  fee_status_tone: string;
  enrollment_status_label: string;
  enrollment_status_tone: string;
  detail_href: string;
  is_selectable: boolean;
};

export type StudentEnrollmentManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  enroll_selected_label: string;
  term_filter_label: string;
  programme_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  term_options: { value: string; label: string }[];
  programme_options: { value: string; label: string }[];
  selected_term_key: string;
  selected_programme_code: string;
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  enrollment_section_title: string;
  enrollment_count_label: string;
  table_headers: string[];
  enrollment_rows: StudentEnrollmentManagementTableRow[];
  showing_label: string;
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    page_numbers: number[];
    has_previous: boolean;
    has_next: boolean;
  };
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type StudentEnrollmentManagementPageQuery = {
  page?: number;
  term_key?: string;
  programme_code?: string;
};