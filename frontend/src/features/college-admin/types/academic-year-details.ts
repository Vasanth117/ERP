export type AcademicYearDetailsKeyValueRow = {
  key: string;
  label: string;
  value: string;
};

export type AcademicYearDetailsTermRow = {
  term_id: string;
  label: string;
  period_label: string;
  status_label: string;
  status_tone: string;
};

export type AcademicYearDetailsPage = {
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  year_id: string;
  year_label: string;
  status_label: string;
  status_tone: string;
  is_current: boolean;
  overview_section_title: string;
  overview_rows: AcademicYearDetailsKeyValueRow[];
  terms_section_title: string;
  terms_table_headers: string[];
  term_rows: AcademicYearDetailsTermRow[];
  manage_semesters_label: string;
  manage_semesters_href: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};