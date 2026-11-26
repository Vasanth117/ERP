export type HostelRoomFilterOption = {
  value: string;
  label: string;
};

export type HostelRoomManagementTableRow = {
  room_code: string;
  room_label: string;
  block_label: string;
  floor_label: string;
  type_label: string;
  beds_label: string;
  occupied_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelRoomManagementPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelRoomManagementPage = {
  page_title: string;
  page_subtitle: string;
  add_room_label: string;
  add_room_href: string;
  search_placeholder: string;
  block_filter_label: string;
  floor_filter_label: string;
  type_filter_label: string;
  block_options: HostelRoomFilterOption[];
  floor_options: HostelRoomFilterOption[];
  type_options: HostelRoomFilterOption[];
  rooms_section_title: string;
  table_headers: string[];
  room_rows: HostelRoomManagementTableRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: HostelRoomManagementPagination;
  generated_at: string;
};

export type HostelRoomManagementPageQuery = {
  page?: number;
  page_size?: number;
  search?: string;
  block_code?: string;
  floor_id?: string;
  room_type?: string;
};