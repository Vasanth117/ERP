export type LibraryLostDamagedRow = {
  report_id: string;
  book_title: string;
  member_name: string;
  type_label: string;
  recovery_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LibraryLostDamagedPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryLostDamagedPage = {
  page_title: string;
  page_subtitle: string;
  report_loss_label: string;
  report_loss_href: string;
  lost_damaged_section_title: string;
  table_headers: string[];
  report_rows: LibraryLostDamagedRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryLostDamagedPagination;
  generated_at: string;
};

export type LibraryLostDamagedPageQuery = {
  page?: number;
  page_size?: number;
};