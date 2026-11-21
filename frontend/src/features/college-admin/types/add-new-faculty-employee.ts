import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type AddNewFacultyEmployeeWizardStep = {
  key: string;
  label: string;
  step_number: number;
  status: string;
};

export type AddNewFacultyEmployeeFormValues = {
  full_name: string;
  mobile: string;
  date_of_birth: string;
  gender: string;
  residential_address: string;
  employee_type: string;
  department_id: string;
  designation: string;
  joining_date: string;
  reporting_to: string;
  employment_status: string;
  contract_end_date: string;
  official_email: string;
  degree: string;
  institution: string;
  qualification_year: string;
  specialization: string;
  experience_years: string;
  document_ids_verified: string;
  document_degree_certificates: string;
  document_experience: string;
  password: string;
  confirm_password: string;
};

export type AddNewFacultyEmployeePage = {
  draft_id: string;
  page_title: string;
  page_subtitle: string;
  back_href: string;
  back_label: string;
  save_draft_label: string;
  create_label: string;
  current_step_key: string;
  steps: AddNewFacultyEmployeeWizardStep[];
  employment_section_title: string;
  field_meta: InstitutionFieldMeta[];
  form: AddNewFacultyEmployeeFormValues;
  employee_type_options: InstitutionFieldOption[];
  department_options: InstitutionFieldOption[];
  designation_options: InstitutionFieldOption[];
  employment_status_options: InstitutionFieldOption[];
  reporting_to_options: InstitutionFieldOption[];
  gender_options: InstitutionFieldOption[];
  document_checklist: InstitutionFieldOption[];
  access_card: {
    title: string;
    role_label: string;
    role_icon_key: string;
    login_created_label: string;
    login_icon_key: string;
  };
  employee_id_card: {
    title: string;
    next_id_label: string;
    next_id_value: string;
    format_label: string;
    format_value: string;
  };
  has_draft: boolean;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AddNewFacultyEmployeeDraftPayload = {
  draft_id?: string;
  step_key?: string;
  values?: Record<string, unknown>;
};

export type AddNewFacultyEmployeeCreateResult = {
  record_id: string;
  employee_id: string | null;
  detail_href: string;
  message: string;
};