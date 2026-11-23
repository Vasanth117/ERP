export type StudentFeeManagementPageQuery = {
  page?: number;
};

export type StudentFeeManagementTableRow = {
  assessment_id: string;
  student_name: string;
  register_number: string;
  programme_label: string;
  assessed_label: string;
  concession_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type StudentFeeManagementPage = {
  page_title: string;
  page_subtitle: string;
  bulk_assign_label: string;
  bulk_assign_href: string;
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  student_fees_section_title: string;
  student_fees_count_label: string;
  table_headers: string[];
  student_fees: StudentFeeManagementTableRow[];
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
  generated_at: string;
};