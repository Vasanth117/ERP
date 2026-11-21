export type ExaminationSetupFormValues = {
  session_name: string;
  examination_type: string;
  academic_year_label: string;
  semester_label: string;
  examination_start_at: string;
  examination_end_at: string;
  registration_end_at: string;
  result_target_at: string;
};

export type ExaminationSetupFieldMeta = {
  key: keyof ExaminationSetupFormValues;
  label: string;
  required: boolean;
  field_type: string;
};

export type ExaminationSetupToggleRule = {
  key: string;
  label: string;
  description: string;
  enabled: boolean;
};

export type ExaminationConfigurationFilterOption = {
  value: string;
  label: string;
};

export type ExaminationConfigurationPageQuery = {
  session_id?: string;
  mode?: string;
};

export type ExaminationConfigurationPage = {
  page_title: string;
  page_subtitle: string;
  back_href: string;
  save_draft_label: string;
  continue_label: string;
  continue_href: string;
  setup_section_title: string;
  rules_section_title: string;
  form: ExaminationSetupFormValues;
  field_meta: ExaminationSetupFieldMeta[];
  type_options: ExaminationConfigurationFilterOption[];
  academic_year_options: ExaminationConfigurationFilterOption[];
  semester_options: ExaminationConfigurationFilterOption[];
  toggle_rules: ExaminationSetupToggleRule[];
  is_new: boolean;
  session_id: string | null;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type ExaminationConfigurationSavePayload = {
  session_id?: string | null;
  form: ExaminationSetupFormValues;
  toggle_rules: Record<string, boolean>;
  advance_workflow?: boolean;
};