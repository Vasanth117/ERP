export type FeeDemandInvoiceManagementPageQuery = {
  page?: number;
};

export type FeeDemandInvoiceManagementTableRow = {
  invoice_id: string;
  invoice_label: string;
  student_name: string;
  due_label: string;
  total_label: string;
  paid_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type FeeDemandInvoiceManagementPage = {
  page_title: string;
  page_subtitle: string;
  generate_demands_label: string;
  generate_demands_href: string;
  publish_label: string;
  publish_href: string;
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  invoices_section_title: string;
  invoices_count_label: string;
  table_headers: string[];
  invoice_rows: FeeDemandInvoiceManagementTableRow[];
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
  generated_at: string;
};