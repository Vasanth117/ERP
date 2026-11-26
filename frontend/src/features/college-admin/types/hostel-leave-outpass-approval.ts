export type HostelLeaveOutpassApprovalTableRow = {
  request_id: string;
  resident_label: string;
  type_label: string;
  from_label: string;
  to_label: string;
  guardian_label: string;
  guardian_tone: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelLeaveOutpassApprovalPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelLeaveOutpassApprovalPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  export_href: string;
  outpass_section_title: string;
  table_headers: string[];
  outpass_rows: HostelLeaveOutpassApprovalTableRow[];
  empty_table_message: string;
  count_label: string;
  showing_label: string;
  pagination: HostelLeaveOutpassApprovalPagination;
  generated_at: string;
};

export type HostelLeaveOutpassApprovalPageQuery = {
  page?: number;
  page_size?: number;
};