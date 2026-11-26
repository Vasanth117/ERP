export type HostelResidentManagementTableRow = {
  resident_key: string;
  resident_label: string;
  register_label: string;
  room_label: string;
  block_label: string;
  fee_label: string;
  fee_tone: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelResidentManagementFilterOption = {
  value: string;
  label: string;
};

export type HostelResidentManagementPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelResidentManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  export_href: string;
  search_placeholder: string;
  block_filter_label: string;
  status_filter_label: string;
  block_options: HostelResidentManagementFilterOption[];
  status_options: HostelResidentManagementFilterOption[];
  residents_section_title: string;
  table_headers: string[];
  resident_rows: HostelResidentManagementTableRow[];
  empty_table_message: string;
  count_label: string;
  showing_label: string;
  pagination: HostelResidentManagementPagination;
  generated_at: string;
};

export type HostelResidentManagementPageQuery = {
  page?: number;
  page_size?: number;
  search?: string;
  block_code?: string;
  status_filter?: string;
};