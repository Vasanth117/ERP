export type RegulationTableRow = {
  regulation_id: string;
  regulation_code: string;
  regulation_label: string;
  effective_from_label: string;
  batch_range_label: string;
  student_count: number;
  programme_count: number;
  status_code: string;
  status_label: string;
  status_tone: string;
  is_selected: boolean;
};

export type RegulationHighlightRow = { key: string; label: string; value: string };

export type RegulationPhaseOutStep = {
  step_id: string;
  title: string;
  date_label: string;
  is_active: boolean;
};

export type RegulationDocumentRow = {
  document_id: string;
  title: string;
  size_label: string;
  download_label: string;
  download_href: string | null;
};

export type RegulationManagementPage = {
  page_title: string;
  page_subtitle: string;
  compare_label: string;
  compare_href: string;
  new_regulation_label: string;
  regulations_section_title: string;
  regulations_count_label: string;
  table_headers: string[];
  regulations: RegulationTableRow[];
  view_documents_label: string;
  view_documents_href: string;
  selected_regulation_code: string;
  highlights_section_title: string;
  highlight_rows: RegulationHighlightRow[];
  phase_out_section_title: string;
  phase_out_steps: RegulationPhaseOutStep[];
  documents_section_title: string;
  documents: RegulationDocumentRow[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type RegulationManagementCreatePayload = {
  regulation_code: string;
  display_label?: string | null;
};