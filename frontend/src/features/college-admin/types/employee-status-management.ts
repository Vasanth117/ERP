import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type EmployeeStatusManagementTableRow = {
  request_id: string;
  employee_name: string;
  current_status_label: string;
  new_status_label: string;
  effective_label: string;
  reason_label: string;
  approval_status_label: string;
  approval_status_tone: string;
};

export type EmployeeStatusManagementMixItem = {
  status_key: string;
  status_label: string;
  count: number;
  bar_percent: number;
  tone: string;
};

export type EmployeeStatusPickerOption = {
  record_id: string;
  label: string;
};

export type EmployeeStatusManagementPage = {
  page_title: string;
  page_subtitle: string;
  change_status_label: string;
  change_status_href: string;
  status_changes_section_title: string;
  table_headers: string[];
  status_change_rows: EmployeeStatusManagementTableRow[];
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
  status_mix_title: string;
  status_mix_items: EmployeeStatusManagementMixItem[];
  update_status_section_title: string;
  employee_field_label: string;
  new_status_field_label: string;
  reason_field_label: string;
  effective_date_field_label: string;
  submit_status_label: string;
  approve_status_label: string;
  employee_picker_options: EmployeeStatusPickerOption[];
  new_status_options: InstitutionFieldOption[];
  selected_request_id?: string | null;
  form_record_id: string;
  form_new_status: string;
  form_reason: string;
  form_effective_date: string;
  updated_at_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type EmployeeStatusManagementPageQuery = {
  page?: number;
  selected_request_id?: string;
};