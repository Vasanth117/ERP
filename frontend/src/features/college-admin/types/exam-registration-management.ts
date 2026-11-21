export type ExamRegistrationManagementPageQuery = {
  page?: number;
  session_id?: string;
  status?: string;
  programme_code?: string;
};

export type ExamRegistrationManagementFilterOption = {
  value: string;
  label: string;
};

export type ExamRegistrationManagementTableRow = {
  registration_id: string;
  student_name: string;
  register_number: string;
  programme_label: string;
  subjects_count: number;
  fee_status_label: string;
  fee_status_tone: string;
  registration_status_label: string;
  registration_status_tone: string;
  submitted_at_label: string;
  detail_href: string;
  is_selectable: boolean;
};

export type ExamRegistrationManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  confirm_selected_label: string;
  session_filter_label: string;
  status_filter_label: string;
  programme_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  session_options: ExamRegistrationManagementFilterOption[];
  status_options: ExamRegistrationManagementFilterOption[];
  programme_options: ExamRegistrationManagementFilterOption[];
  selected_session_id: string;
  selected_status: string;
  selected_programme_code: string;
  registration_window_title: string;
  registration_window_open_label: string;
  registration_window_close_label: string;
  registration_window_status_label: string;
  registration_window_status_tone: string;
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  registrations_section_title: string;
  registration_count_label: string;
  table_headers: string[];
  registration_rows: ExamRegistrationManagementTableRow[];
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