import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";
import type { PoliciesPagination } from "@/features/college-admin/types/all-departments-list";

export type DepartmentHeadAssignmentTableRow = {
  department_id: string;
  department_label: string;
  head_name: string;
  since_label: string;
  term_ends_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
  is_selected: boolean;
};

export type DepartmentHeadEligibilityRow = {
  key: string;
  label: string;
  detail: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type DepartmentHeadAssignmentFormValues = {
  faculty_user_id: string;
  appointment_type: string;
  effective_from: string;
  term_end: string;
  order_reference: string;
};

export type DepartmentHeadAssignmentPage = {
  page_title: string;
  page_subtitle: string;
  rotation_policy_label: string;
  rotation_policy_href: string;
  assign_head_label: string;
  current_heads_section_title: string;
  table_headers: string[];
  table_rows: DepartmentHeadAssignmentTableRow[];
  departments_count_label: string;
  pagination: PoliciesPagination;
  assign_panel_title: string;
  assign_panel_subtitle: string;
  faculty_field_label: string;
  faculty_options: InstitutionFieldOption[];
  appointment_type_field_label: string;
  appointment_type_options: InstitutionFieldOption[];
  effective_from_field_label: string;
  term_end_field_label: string;
  order_reference_field_label: string;
  eligibility_section_title: string;
  eligibility_rows: DepartmentHeadEligibilityRow[];
  form: DepartmentHeadAssignmentFormValues;
  selected_department_id: string | null;
  cancel_label: string;
  submit_label: string;
  footer_note: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  can_submit: boolean;
  generated_at: string;
};

export type DepartmentHeadAssignmentSaveResult = {
  message: string;
  approval_status: string;
  page: DepartmentHeadAssignmentPage;
};