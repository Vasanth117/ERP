import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";
import type { ExaminationWorkflowStep } from "@/features/college-admin/types/examination-dashboard";
import type { ExaminationWorkflowEmptyState } from "@/features/college-admin/types/examination-workflow-empty";

export type MarksEntryManagementPageQuery = {
  page?: number;
  session_id?: string;
};

export type MarksEntryManagementProgressRow = {
  course_code: string;
  subject_label: string;
  faculty_label: string;
  scripts_count: number;
  entered_count: number;
  verified_count: number;
  status_label: string;
  status_tone: string;
};

export type MarksEntryManagementPage = {
  page_title: string;
  page_subtitle: string;
  panel_empty_state?: ExaminationWorkflowEmptyState | null;
  back_href: string;
  save_draft_label: string;
  continue_label: string;
  continue_href: string;
  continue_enabled?: boolean;
  workflow_active_key: string;
  send_reminders_label: string;
  lock_entry_label: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  progress_section_title: string;
  table_headers: string[];
  progress_rows: MarksEntryManagementProgressRow[];
  showing_label: string;
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    page_numbers: number[];
    has_previous: boolean;
    has_next: boolean;
  };
  workflow_steps: ExaminationWorkflowStep[];
  selected_session_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};