import type { YearsSemestersSubNavItem } from "@/features/college-admin/types/academic-year-management";

export type RuleToggle = {
  key: string;
  title: string;
  description: string;
  enabled: boolean;
};

export type CreditLevelRow = {
  level_key: string;
  level_label: string;
  min_graduate_credits: number;
  max_per_semester: number;
  min_per_semester: number;
  status_label: string;
  status_tone: string;
};

export type CreditCalculationField = {
  key: string;
  label: string;
  value: string;
  field_type: string;
  options: { value: string; label: string }[];
};

export type CreditLimitStat = {
  key: string;
  title: string;
  description: string;
  count: number;
  count_tone: string;
};

export type CreditConfigurationPage = {
  page_title: string;
  page_subtitle: string;
  reset_label: string;
  save_rules_label: string;
  cancel_label: string;
  requirements_section_title: string;
  requirements_table_headers: string[];
  requirements_footer_label: string;
  requirements_edit_label: string;
  requirements_edit_href: string;
  level_rows: CreditLevelRow[];
  calculation_section_title: string;
  calculation_fields: CreditCalculationField[];
  rules_section_title: string;
  rules: RuleToggle[];
  limits_section_title: string;
  limit_stats: CreditLimitStat[];
  form_note: string;
  sub_nav: YearsSemestersSubNavItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type CreditConfigurationSavePayload = {
  calculation: Record<string, string>;
  rules: Record<string, boolean>;
  level_rows: CreditLevelRow[];
};

export type GradingScaleRow = {
  grade_id: string;
  grade: string;
  grade_point: number;
  marks_range_label: string;
  description: string;
};

export type GradingClassificationRow = {
  class_id: string;
  class_label: string;
  cgpa_label: string;
  condition_label: string;
};

export type GradingCalculationField = {
  key: string;
  label: string;
  value: string;
  required: boolean;
  field_type: string;
  options: { value: string; label: string }[];
};

export type GradingSystemConfigurationPage = {
  page_title: string;
  page_subtitle: string;
  preview_transcript_label: string;
  preview_transcript_href: string;
  save_grading_label: string;
  cancel_label: string;
  grade_scale_title: string;
  grade_table_headers: string[];
  grade_rows: GradingScaleRow[];
  grade_scale_footer: string;
  add_grade_label: string;
  classification_section_title: string;
  classification_table_headers: string[];
  classification_rows: GradingClassificationRow[];
  classification_footer: string;
  classification_edit_label: string;
  calculation_section_title: string;
  calculation_fields: GradingCalculationField[];
  rules_section_title: string;
  rules: RuleToggle[];
  form_note: string;
  sub_nav: YearsSemestersSubNavItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type GradingSystemConfigurationSavePayload = {
  grade_rows: GradingScaleRow[];
  classification_rows: GradingClassificationRow[];
  calculation: Record<string, string>;
  rules: Record<string, boolean>;
};