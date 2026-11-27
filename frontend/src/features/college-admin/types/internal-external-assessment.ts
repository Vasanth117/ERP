import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";

export type InternalExternalAssessmentPageQuery = {
  session_id?: string;
};

export type InternalExternalAssessmentComponentDraft = {
  component_id: string;
  code: string;
  name: string;
  assessment_type: string;
  weight_percent: number;
  max_marks: number;
  source: string;
};

export type InternalExternalAssessmentSavePayload = {
  session_id: string;
  config_id: string;
  moderation_range: string;
  pass_mark_percent: string;
  advance_workflow?: boolean;
  components?: InternalExternalAssessmentComponentDraft[];
};

export type InternalExternalAssessmentComponentRow = {
  component_id: string;
  component_label: string;
  weight_label: string;
  max_marks_label: string;
  source_label: string;
};

import type { ExaminationWorkflowStep } from "@/features/college-admin/types/examination-dashboard";
import type { ExaminationWorkflowEmptyState } from "@/features/college-admin/types/examination-workflow-empty";

export type InternalExternalAssessmentPage = {
  page_title: string;
  page_subtitle: string;
  panel_empty_state?: ExaminationWorkflowEmptyState | null;
  back_href: string;
  save_draft_label: string;
  continue_label: string;
  continue_href: string;
  continue_enabled?: boolean;
  workflow_steps: ExaminationWorkflowStep[];
  workflow_active_key: string;
  save_label: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  assessment_pattern_section_title: string;
  moderation_section_title: string;
  table_headers: string[];
  component_rows: InternalExternalAssessmentComponentRow[];
  component_drafts: InternalExternalAssessmentComponentDraft[];
  assessment_type_options: { value: string; label: string }[];
  source_options: { value: string; label: string }[];
  add_component_label: string;
  total_weight_label: string;
  moderation_range_label: string;
  pass_mark_label: string;
  selected_moderation_range: string;
  selected_pass_mark_percent: string;
  moderation_range_options: { value: string; label: string }[];
  pass_mark_options: { value: string; label: string }[];
  selected_config_id: string;
  selected_session_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};