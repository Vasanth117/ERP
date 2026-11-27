import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";
import type { ExaminationWorkflowStep } from "@/features/college-admin/types/examination-dashboard";
import type { ExaminationWorkflowEmptyState } from "@/features/college-admin/types/examination-workflow-empty";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type ResultApprovalPageQuery = {
  page?: number;
  session_id?: string;
};

export type ResultApprovalProgrammeRow = {
  programme_code: string;
  programme_label: string;
  students_count: number;
  pass_count: number;
  pass_percent_label: string;
};

export type ResultApprovalRouteStep = {
  key: string;
  title: string;
  status_label: string;
  status_tone: string;
};

export type ResultApprovalPage = {
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
  return_label: string;
  approve_label: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  summary_section_title: string;
  route_section_title: string;
  table_headers: string[];
  programme_rows: ResultApprovalProgrammeRow[];
  approval_route_steps: ResultApprovalRouteStep[];
  showing_label: string;
  pagination: PoliciesPagination;
  selected_session_id: string;
  selected_workflow_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};