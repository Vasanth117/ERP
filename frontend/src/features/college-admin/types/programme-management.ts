import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type ProgrammeManagementTableRow = {
  programme_id: string;
  programme_name: string;
  programme_code: string;
  level_label: string;
  department_label: string;
  duration_label: string;
  intake_label: string;
  regulation_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type ProgrammeManagementFilterOption = {
  value: string;
  label: string;
};

export type ProgrammeManagementCreateField = {
  key: string;
  label: string;
  required: boolean;
  field_type: string;
};

export type ProgrammeManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  add_programme_label: string;
  search_placeholder: string;
  level_filter_label: string;
  department_filter_label: string;
  regulation_filter_label: string;
  status_filter_label: string;
  level_options: ProgrammeManagementFilterOption[];
  department_options: ProgrammeManagementFilterOption[];
  regulation_options: ProgrammeManagementFilterOption[];
  status_options: ProgrammeManagementFilterOption[];
  programmes_section_title: string;
  programmes_count_label: string;
  table_headers: string[];
  programmes: ProgrammeManagementTableRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  create_section_title: string;
  create_form_note: string;
  create_submit_label: string;
  create_cancel_label: string;
  create_fields: ProgrammeManagementCreateField[];
  create_department_options: ProgrammeManagementFilterOption[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type ProgrammeManagementCreatePayload = {
  programme_code: string;
  name: string;
  department_id?: string | null;
  duration_semesters: number;
  credits_required: number;
};