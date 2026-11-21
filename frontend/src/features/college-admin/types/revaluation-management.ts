import type { ExaminationRegistrationSubNavItem } from "@/features/college-admin/types/examination-registration-shared";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type RevaluationManagementPageQuery = {
  page?: number;
  session_id?: string;
};

export type RevaluationManagementTableRow = {
  application_id: string;
  request_label: string;
  student_label: string;
  subject_label: string;
  fee_label: string;
  result_label: string;
  status_label: string;
  status_tone: string;
};

export type RevaluationManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  sub_nav: ExaminationRegistrationSubNavItem[];
  requests_section_title: string;
  table_headers: string[];
  request_rows: RevaluationManagementTableRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  selected_session_id: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};