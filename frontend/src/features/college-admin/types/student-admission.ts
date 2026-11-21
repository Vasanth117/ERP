export type StudentAdmissionListTableRow = {
  admission_id: string;
  applicant_name: string;
  application_number: string;
  programme_label: string;
  quota_label: string;
  marks_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type StudentAdmissionPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  new_admission_label: string;
  new_admission_href: string;
  academic_year_filter_label: string;
  programme_filter_label: string;
  quota_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  academic_year_options: { value: string; label: string }[];
  programme_options: { value: string; label: string }[];
  quota_options: { value: string; label: string }[];
  status_filter_label: string;
  status_options: { value: string; label: string }[];
  selected_academic_year: string;
  selected_programme_code: string;
  selected_quota: string;
  selected_status: string;
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  applications_section_title: string;
  applications_count_label: string;
  table_headers: string[];
  applications: StudentAdmissionListTableRow[];
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

export type StudentAdmissionPageQuery = {
  page?: number;
  academic_year_code?: string;
  programme_code?: string;
  quota_filter?: string;
  status_filter?: string;
  search?: string;
};