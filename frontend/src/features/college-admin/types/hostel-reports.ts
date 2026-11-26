export type HostelReportsTableRow = {
  report_key: string;
  report_label: string;
  period_label: string;
  format_label: string;
  last_run_label: string;
  schedule_label: string;
  detail_href: string;
};

export type HostelReportsPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelReportsPage = {
  page_title: string;
  page_subtitle: string;
  create_report_label: string;
  create_report_href: string;
  reports_section_title: string;
  table_headers: string[];
  report_rows: HostelReportsTableRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: HostelReportsPagination;
  generated_at: string;
};

export type HostelReportsPageQuery = {
  page?: number;
  page_size?: number;
};