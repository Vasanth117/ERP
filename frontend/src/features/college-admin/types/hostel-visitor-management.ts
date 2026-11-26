export type HostelVisitorManagementTableRow = {
  visit_key: string;
  visitor_label: string;
  visiting_label: string;
  relation_label: string;
  in_label: string;
  out_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelVisitorManagementPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelVisitorManagementPage = {
  page_title: string;
  page_subtitle: string;
  register_visitor_label: string;
  register_visitor_href: string;
  visitors_section_title: string;
  table_headers: string[];
  visitor_rows: HostelVisitorManagementTableRow[];
  empty_table_message: string;
  count_label: string;
  showing_label: string;
  pagination: HostelVisitorManagementPagination;
  generated_at: string;
};

export type HostelVisitorManagementPageQuery = {
  page?: number;
  page_size?: number;
};