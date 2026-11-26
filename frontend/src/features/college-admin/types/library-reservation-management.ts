export type LibraryReservationManagementRow = {
  reservation_id: string;
  title: string;
  member_name: string;
  queue_label: string;
  reserved_label: string;
  expires_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LibraryReservationManagementPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryReservationManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  reservations_section_title: string;
  table_headers: string[];
  reservation_rows: LibraryReservationManagementRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryReservationManagementPagination;
  generated_at: string;
};

export type LibraryReservationManagementPageQuery = {
  page?: number;
  page_size?: number;
};