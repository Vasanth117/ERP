import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type ExamTimetableManagementPageQuery = {
  page?: number;
  session_id?: string;
  programme_code?: string;
};

export type ExamTimetableClashBanner = {
  visible: boolean;
  headline: string;
  description: string;
  tone: string;
};

export type ExamTimetableManagementRow = {
  entry_code: string;
  date_label: string;
  session_label: string;
  subject_label: string;
  code_label: string;
  programme_sem_label: string;
  hall_label: string;
};

export type ExamTimetableManagementPage = {
  page_title: string;
  page_subtitle: string;
  regenerate_label: string;
  publish_label: string;
  session_filter_label: string;
  programme_filter_label: string;
  scope_indicator_label: string;
  updated_at_label: string;
  session_options: { value: string; label: string }[];
  programme_options: { value: string; label: string }[];
  selected_session_id: string;
  selected_programme_code: string;
  clash_banner: ExamTimetableClashBanner;
  timetable_section_title: string;
  papers_count_label: string;
  table_headers: string[];
  rows: ExamTimetableManagementRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  timetable_status_label: string;
  publish_enabled: boolean;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type ExamTimetableManagementActionPayload = {
  session_id: string;
  programme_code?: string;
  page?: number;
};