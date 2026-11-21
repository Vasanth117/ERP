import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type DepartmentDesignationAssignmentFormValues = {
  record_id: string;
  department_id: string;
  designation: string;
  reporting_to: string;
  effective_from: string;
  reason: string;
};

export type DepartmentDesignationHistoryItem = {
  key: string;
  title: string;
  date_label: string;
  tone: string;
};

export type DepartmentDesignationApprovalStep = {
  key: string;
  label: string;
  status_label: string;
  tone: string;
};

export type FacultyAssignmentEmployeeOption = {
  record_id: string;
  label: string;
  employee_id_label: string;
};

export type DepartmentDesignationAssignmentPage = {
  page_title: string;
  page_subtitle: string;
  cancel_label: string;
  cancel_href: string;
  save_label: string;
  requires_record: boolean;
  select_employee_title?: string | null;
  select_employee_hint?: string | null;
  faculty_directory_href?: string | null;
  faculty_directory_label?: string | null;
  picker_rows: FacultyAssignmentEmployeeOption[];
  employee_display?: string | null;
  assignment_section_title: string;
  field_meta: InstitutionFieldMeta[];
  form: DepartmentDesignationAssignmentFormValues;
  employee_options: InstitutionFieldOption[];
  department_options: InstitutionFieldOption[];
  designation_options: InstitutionFieldOption[];
  reporting_to_options: InstitutionFieldOption[];
  history_section_title: string;
  history_items: DepartmentDesignationHistoryItem[];
  approval_section_title: string;
  approval_steps: DepartmentDesignationApprovalStep[];
  has_unsaved_changes: boolean;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};