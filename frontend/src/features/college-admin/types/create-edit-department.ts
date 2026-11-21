import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";

export type CreateEditDepartmentFormValues = {
  name: string;
  department_code: string;
  department_kind: string;
  organization_unit_id: string;
  campus_id: string;
  establishment_year: number | null;
  building_floor_label: string;
  contact_email: string;
  vision_mission: string;
  head_user_id: string;
  approved_intake_ug: number | null;
  aicte_approval_reference: string;
  cost_centre_code: string;
  settings_template_department_id: string;
};

export type CreateEditDepartmentTemplateOption = {
  template_key: string;
  title: string;
  subtitle: string;
  action_label: string;
  department_id: string;
};

export type CreateEditDepartmentChecklistStep = {
  key: string;
  label: string;
  hint: string;
  state: string;
};

export type CreateEditDepartmentPage = {
  page_title: string;
  page_subtitle: string;
  cancel_href: string;
  cancel_label: string;
  save_label: string;
  save_draft_label: string;
  create_label: string;
  details_section_title: string;
  setup_section_title: string;
  copy_settings_title: string;
  checklist_title: string;
  details_field_meta: InstitutionFieldMeta[];
  setup_field_meta: InstitutionFieldMeta[];
  department_kind_options: InstitutionFieldOption[];
  school_options: InstitutionFieldOption[];
  campus_options: InstitutionFieldOption[];
  building_options: InstitutionFieldOption[];
  cost_centre_options: InstitutionFieldOption[];
  head_options: InstitutionFieldOption[];
  template_options: CreateEditDepartmentTemplateOption[];
  checklist_steps: CreateEditDepartmentChecklistStep[];
  form: CreateEditDepartmentFormValues;
  department_id: string | null;
  is_create: boolean;
  can_save: boolean;
  footer_note: string;
  footer_disclaimer: string;
  generated_at: string;
};