export type LibraryDigitalResourceRow = {
  resource_id: string;
  title: string;
  type_label: string;
  licence_label: string;
  users_label: string;
  expires_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LibraryDigitalLibraryPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryDigitalLibraryPage = {
  page_title: string;
  page_subtitle: string;
  add_resource_label: string;
  add_resource_href: string;
  digital_resources_section_title: string;
  table_headers: string[];
  resource_rows: LibraryDigitalResourceRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryDigitalLibraryPagination;
  generated_at: string;
};

export type LibraryDigitalLibraryPageQuery = {
  page?: number;
  page_size?: number;
};