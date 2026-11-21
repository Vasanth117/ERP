export type StudentIdCardManagementTableRow = {
  record_id: string;
  card_id: string;
  student_name: string;
  card_number_label: string;
  issued_label: string;
  valid_until_label: string;
  status_label: string;
  status_tone: string;
};

export type StudentIdCardManagementKpi = {
  key: string;
  label: string;
  value: string;
  hint_line: string;
  hint_tone: string;
};

export type StudentIdCardManagementPage = {
  page_title: string;
  page_subtitle: string;
  bulk_print_label: string;
  issue_card_label: string;
  issue_card_href: string;
  kpis: StudentIdCardManagementKpi[];
  id_cards_section_title: string;
  table_headers: string[];
  card_rows: StudentIdCardManagementTableRow[];
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

export type StudentIdCardManagementPageQuery = {
  page?: number;
};

export type StudentIdCardIssuePayload = {
  record_id?: string | null;
  page?: number;
};

export type StudentIdCardBulkPrintPayload = {
  record_ids?: string[];
  page?: number;
};