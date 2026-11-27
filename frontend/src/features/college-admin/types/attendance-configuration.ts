export type AttendanceFieldOption = { value: string; label: string };

export type AttendanceConfigurationFieldMeta = {
  key: string;
  label: string;
  field_type: string;
};

export type AttendanceConfigurationToggleRule = {
  key: string;
  label: string;
  description: string;
  enabled: boolean;
};

export type AttendanceConfigurationSummaryItem = {
  key: string;
  label: string;
  value_label: string;
  section_key: string;
  detail_description: string;
  value_tone: string;
};

export type AttendanceConfigurationPolicyPreview = {
  row_key: string;
  policy_title: string;
  value_label: string;
  applies_to_label: string;
};

export type AttendanceConfigurationPage = {
  page_title: string;
  page_subtitle: string;
  cancel_label: string;
  save_label: string;
  edit_settings_label: string;
  current_settings_section_title: string;
  view_settings_description: string;
  rules_policies_href: string;
  rules_policies_link_label: string;
  reports_href: string;
  reports_link_label: string;
  related_policies_section_title: string;
  related_policies_description: string;
  policy_preview_rows: AttendanceConfigurationPolicyPreview[];
  summary_items: AttendanceConfigurationSummaryItem[];
  marking_section_title: string;
  behaviour_section_title: string;
  marking_window_key: string;
  correction_window_key: string;
  late_mark_after_key: string;
  session_length_key: string;
  marking_window_options: AttendanceFieldOption[];
  correction_window_options: AttendanceFieldOption[];
  late_mark_after_options: AttendanceFieldOption[];
  session_length_options: AttendanceFieldOption[];
  field_meta: AttendanceConfigurationFieldMeta[];
  toggle_rules: AttendanceConfigurationToggleRule[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AttendanceConfigurationSavePayload = {
  marking_window_key: string;
  correction_window_key: string;
  late_mark_after_key: string;
  session_length_key: string;
  toggle_rules: Record<string, boolean>;
};

export type AttendanceRulesPolicyRow = {
  row_key: string;
  policy_title: string;
  value_label: string;
  applies_to_label: string;
  effective_label: string;
  status_label: string;
  status_tone: string;
};

export type AttendanceInstitutionalPolicySavePayload = {
  policy_key?: string | null;
  title: string;
  value_label: string;
  applies_to_label: string;
  is_active: boolean;
};

export type AttendanceRulesPoliciesPage = {
  page_title: string;
  page_subtitle: string;
  configuration_href: string;
  configuration_edit_href: string;
  back_label: string;
  add_policy_label: string;
  edit_policy_label: string;
  edit_marking_settings_label: string;
  policies_section_title: string;
  policies_table_headers: string[];
  policy_rows: AttendanceRulesPolicyRow[];
  policies_table_footer_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type AttendanceRulesPoliciesQuery = {
  page?: number;
  page_size?: number;
};