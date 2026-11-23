export type FeeStructureManagementPageQuery = {
  page?: number;
};

export type FeeStructureManagementTableRow = {
  structure_id: string;
  structure_label: string;
  year_label: string;
  programme_label: string;
  total_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type FeeStructureManagementPage = {
  page_title: string;
  page_subtitle: string;
  create_fee_structure_label: string;
  create_fee_structure_href: string;
  structures_section_title: string;
  structures_count_label: string;
  table_headers: string[];
  structures: FeeStructureManagementTableRow[];
  showing_label: string;
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    page_numbers: number[];
    has_previous: boolean;
    has_next: boolean;
  };
  info_notice_title: string;
  info_notice_body: string;
  generated_at: string;
};