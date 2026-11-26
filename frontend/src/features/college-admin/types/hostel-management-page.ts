export type HostelManagementTableRow = {
  row_id: string;
  cells: string[];
  status_label?: string | null;
  status_tone?: string | null;
  detail_href?: string | null;
};

export type HostelManagementPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelManagementPage = {
  screen_slug: string;
  figma_frame: string;
  page_title: string;
  page_subtitle: string;
  primary_action_label?: string | null;
  primary_action_href?: string | null;
  section_title: string;
  count_label: string;
  table_headers: string[];
  rows: HostelManagementTableRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: HostelManagementPagination;
  generated_at: string;
};

export type HostelManagementPageQuery = {
  page?: number;
  page_size?: number;
};