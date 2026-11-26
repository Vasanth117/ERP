export type LibraryBookAcquisitionRow = {
  acquisition_id: string;
  title: string;
  requested_by_label: string;
  copies_label: string;
  cost_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LibraryBookAcquisitionPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryBookAcquisitionPage = {
  page_title: string;
  page_subtitle: string;
  new_request_label: string;
  new_request_href: string;
  acquisitions_section_title: string;
  table_headers: string[];
  acquisition_rows: LibraryBookAcquisitionRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryBookAcquisitionPagination;
  generated_at: string;
};

export type LibraryBookAcquisitionPageQuery = {
  page?: number;
  page_size?: number;
};