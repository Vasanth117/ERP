import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type BatchSectionBatchTab = {
  batch_year: string;
  label: string;
  active: boolean;
};

export type BatchSectionTableRow = {
  section_id: string;
  section_label: string;
  advisor_label: string;
  capacity_label: string;
  allocated_count: number | null;
  room_label: string;
  status_label: string;
  status_tone: string;
};

export type BatchSectionOverviewRow = {
  batch_label: string;
  seats_filled_label: string;
  bar_percent: number;
};

export type BatchSectionPendingTaskRow = {
  task_id: string;
  title: string;
  subtitle: string;
  action_label: string;
  action_kind: string;
  action_href: string | null;
  status_tone: string;
};

export type BatchSectionAllocationField = {
  key: string;
  label: string;
  required: boolean;
  field_type: string;
  options: InstitutionFieldOption[];
  value: string;
};

export type BatchSectionAllocationRulesForm = {
  section_title: string;
  fields: BatchSectionAllocationField[];
};

export type BatchSectionPagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type BatchSectionConfigurationPage = {
  page_title: string;
  page_subtitle: string;
  auto_allocate_label: string;
  add_section_label: string;
  batch_tabs: BatchSectionBatchTab[];
  selected_batch_year: string;
  selected_programme_code: string;
  programme_options: InstitutionFieldOption[];
  sections_panel_title: string;
  table_headers: string[];
  section_rows: BatchSectionTableRow[];
  section_summary_label: string;
  pagination: BatchSectionPagination;
  allocation_rules: BatchSectionAllocationRulesForm;
  overview_title: string;
  overview_rows: BatchSectionOverviewRow[];
  pending_tasks_title: string;
  pending_tasks: BatchSectionPendingTaskRow[];
  footer_note: string;
  cancel_label: string;
  save_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type BatchSectionAllocationRulesPayload = {
  default_section_size: number;
  allocation_method: string;
  balance_by_gender: string;
  lateral_entry_handling: string;
};

export type BatchSectionAddSectionPayload = {
  programme_code: string;
  batch_label: string;
  section_code: string;
  section_name: string;
  capacity: number;
  room_label?: string | null;
};

export type BatchSectionAutoAllocatePayload = {
  programme_code: string;
  batch_label: string;
};