export type HostelBuildingManagementTableRow = {
  block_key: string;
  block_label: string;
  type_label: string;
  floors_label: string;
  rooms_label: string;
  beds_label: string;
  warden_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type HostelBuildingManagementPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type HostelBuildingManagementPage = {
  page_title: string;
  page_subtitle: string;
  add_building_label: string;
  add_building_href: string;
  buildings_section_title: string;
  table_headers: string[];
  block_rows: HostelBuildingManagementTableRow[];
  empty_table_message: string;
  count_label: string;
  showing_label: string;
  pagination: HostelBuildingManagementPagination;
  generated_at: string;
};

export type HostelBuildingManagementPageQuery = {
  page?: number;
  page_size?: number;
};