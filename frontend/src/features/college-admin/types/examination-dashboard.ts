import type { StudentAdminWorkQueueItem } from "@/features/college-admin/types/student-administration-dashboard";

export type ExaminationDashboardPageQuery = {
  page?: number;
};

export type ExaminationWorkflowStep = {
  key: string;
  label: string;
  step_number: number;
  status: string;
  href?: string | null;
};

export type ExaminationDashboardSessionRow = {
  session_id: string;
  session_label: string;
  type_label: string;
  period_label: string;
  programmes_label: string;
  students_count: number;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type ExaminationDashboardPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  create_examination_label: string;
  create_examination_href: string;
  scope_indicator_label: string;
  updated_at_label: string;
  workflow_steps: ExaminationWorkflowStep[];
  kpis: { key: string; label: string; value: string; hint_line: string; hint_tone: string }[];
  sessions_section_title: string;
  sessions_count_label: string;
  table_headers: string[];
  session_rows: ExaminationDashboardSessionRow[];
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
  pending_title: string;
  pending_items: StudentAdminWorkQueueItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};