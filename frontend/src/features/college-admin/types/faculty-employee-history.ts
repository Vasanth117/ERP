export type FacultyEmployeeHistoryTableRow = {
  row_id: string;
  date_label: string;
  employee_name: string;
  change_label: string;
  actor_label: string;
  reference_label: string;
};

export type FacultyEmployeeHistoryPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  history_section_title: string;
  table_headers: string[];
  history_rows: FacultyEmployeeHistoryTableRow[];
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

export type FacultyEmployeeHistoryPageQuery = {
  page?: number;
};