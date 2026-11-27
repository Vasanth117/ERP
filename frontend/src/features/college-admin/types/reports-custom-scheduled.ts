import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type ReportsTablePagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type ReportsScheduledTableRow = {
  row_key: string;
  report_label: string;
  frequency_label: string;
  next_run_label: string;
  recipients_label: string;
  format_label: string;
  status_label: string;
  status_tone: string;
};

export type ReportsScheduledPage = {
  page_title: string;
  page_subtitle: string;
  schedule_action_label: string;
  schedules_section_title: string;
  table_headers: string[];
  schedule_rows: ReportsScheduledTableRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: ReportsTablePagination;
  report_options: InstitutionFieldOption[];
  generated_at: string;
};

export type ReportsExportHistoryTableRow = {
  row_key: string;
  file_label: string;
  requested_by_label: string;
  format_label: string;
  size_label: string;
  date_label: string;
  status_label: string;
  status_tone: string;
};

export type ReportsExportHistoryPage = {
  page_title: string;
  page_subtitle: string;
  export_log_label: string;
  exports_section_title: string;
  table_headers: string[];
  export_rows: ReportsExportHistoryTableRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: ReportsTablePagination;
  generated_at: string;
};

export type ReportsCustomBuilderStep = {
  step_key: string;
  step_label: string;
  step_number: number;
  status: string;
};

export type ReportsCustomBuilderPreviewRow = {
  row_key: string;
  name_label: string;
  programme_label: string;
  attendance_label: string;
};

export type ReportsCustomBuilderPage = {
  page_title: string;
  page_subtitle: string;
  save_template_label: string;
  run_label: string;
  steps: ReportsCustomBuilderStep[];
  data_source_label: string;
  data_source_options: InstitutionFieldOption[];
  selected_data_source: string;
  fields_label: string;
  field_options: InstitutionFieldOption[];
  selected_fields: string[];
  group_by_label: string;
  group_by_options: InstitutionFieldOption[];
  selected_group_by: string;
  sort_by_label: string;
  sort_by_options: InstitutionFieldOption[];
  selected_sort_by: string;
  date_range_label: string;
  date_range_options: InstitutionFieldOption[];
  selected_date_range: string;
  format_label: string;
  format_options: InstitutionFieldOption[];
  selected_format: string;
  preview_section_title: string;
  preview_headers: string[];
  preview_rows: ReportsCustomBuilderPreviewRow[];
  empty_preview_message: string;
  filter_id: string;
  report_key: string;
  generated_at: string;
};

export type ReportsCustomBuilderSave = {
  filter_id: string;
  data_source: string;
  selected_fields: string[];
  group_by: string;
  sort_by: string;
  export_format: string;
  academic_year?: string;
};

export type ReportsPageQuery = {
  page?: number;
  page_size?: number;
};

export type ReportsBuilderPageQuery = {
  data_source?: string;
  filter_id?: string;
  active_step?: string;
};

export type ReportsScheduleCreate = {
  report_key: string;
  schedule_cron?: string;
  frequency_label?: string;
  export_format?: string;
  recipients?: string[];
};