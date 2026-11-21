import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type ResultPublicationPageQuery = {
  page?: number;
  session_id?: string;
};

export type ResultPublicationProgrammeRow = {
  programme_code: string;
  programme_label: string;
  students_count: number;
  approved_label: string;
  publish_at_label: string;
  notify_label: string;
  notify_tone: string;
  ready_to_publish: boolean;
  publication_id: string;
};

export type ResultPublicationPage = {
  page_title: string;
  page_subtitle: string;
  schedule_label: string;
  publish_now_label: string;
  warning_title: string;
  warning_message: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  ready_section_title: string;
  table_headers: string[];
  programme_rows: ResultPublicationProgrammeRow[];
  ready_count_label: string;
  showing_label: string;
  pagination: PoliciesPagination;
  selected_session_id: string;
  selected_workflow_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};