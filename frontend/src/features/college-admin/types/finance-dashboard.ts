export type FinanceDashboardPageQuery = {
  page?: number;
  academic_year_code?: string;
  programme_code?: string;
};

export type FinanceWorkflowStep = {
  key: string;
  label: string;
  step_number: number;
  status: string;
  href?: string | null;
};

export type FinanceDashboardTransactionRow = {
  transaction_id: string;
  student_name: string;
  invoice_label: string;
  method_label: string;
  amount_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type FinanceProgrammeCollectionItem = {
  key: string;
  label: string;
  collection_percent: number;
  bar_tone: string;
};

export type FinanceDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  open_portal_label: string;
  open_portal_href: string;
  academic_year_filter_label: string;
  programme_filter_label: string;
  academic_year_options: { value: string; label: string }[];
  programme_options: { value: string; label: string }[];
  selected_academic_year: string;
  selected_programme_code: string;
  workflow_steps: FinanceWorkflowStep[];
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  transactions_section_title: string;
  transactions_count_label: string;
  table_headers: string[];
  transaction_rows: FinanceDashboardTransactionRow[];
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
  collection_section_title: string;
  programme_collection_items: FinanceProgrammeCollectionItem[];
  generated_at: string;
};