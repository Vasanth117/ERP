export type StudentPromotionRuleRow = {
  rule_key: string;
  rule_label: string;
  requirement_label: string;
  affected_label: string;
};

export type StudentPromotionManagementPage = {
  page_title: string;
  page_subtitle: string;
  preview_label: string;
  promote_eligible_label: string;
  transition_filter_label: string;
  programme_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  transition_options: { value: string; label: string }[];
  programme_options: { value: string; label: string }[];
  selected_transition_key: string;
  selected_programme_code: string;
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  promotion_rules_section_title: string;
  promotion_rules_footer_label: string;
  promotion_rules_table_headers: string[];
  promotion_rules_rows: StudentPromotionRuleRow[];
  preview_note: string | null;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type StudentPromotionManagementPageQuery = {
  transition_key?: string;
  programme_code?: string;
};

export type StudentPromotionPromotePayload = {
  transition_key: string;
  programme_code?: string;
};