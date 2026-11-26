export type LibraryReportsTableRow = {
  report_type: string;
  report_label: string;
  period_label: string;
  format_label: string;
  last_run_label: string;
  schedule_label: string;
  detail_href: string;
};

export type LibraryReportsPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryReportsPage = {
  page_title: string;
  page_subtitle: string;
  create_report_label: string;
  create_report_href: string;
  reports_section_title: string;
  table_headers: string[];
  report_rows: LibraryReportsTableRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryReportsPagination;
  generated_at: string;
};

export type LibraryReportsPageQuery = {
  page?: number;
  page_size?: number;
};