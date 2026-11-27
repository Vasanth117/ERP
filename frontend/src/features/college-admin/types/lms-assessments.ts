import type { PoliciesPagination } from "@/features/college-admin/types/institution";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type LmsAssignmentManagementRow = {
  row_key: string;
  assignment_label: string;
  course_code: string;
  due_label: string;
  submitted_label: string;
  evaluated_count: number;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LmsAssignmentManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  primary_action_href: string;
  kpis: UserDashboardKpi[];
  assignments_section_title: string;
  table_headers: string[];
  assignment_rows: LmsAssignmentManagementRow[];
  empty_table_message: string;
  showing_label: string;
  count_footer_label: string;
  pagination: PoliciesPagination;
  generated_at: string;
};

export type LmsQuizManagementRow = {
  row_key: string;
  quiz_label: string;
  course_code: string;
  questions_label: string;
  attempts_label: string;
  average_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LmsQuizManagementPage = {
  page_title: string;
  page_subtitle: string;
  primary_action_label: string;
  primary_action_href: string;
  quizzes_section_title: string;
  table_headers: string[];
  quiz_rows: LmsQuizManagementRow[];
  empty_table_message: string;
  count_footer_label: string;
  pagination: PoliciesPagination;
  generated_at: string;
};

export type LmsAssessmentManagementRow = {
  row_key: string;
  assessment_label: string;
  course_code: string;
  type_label: string;
  weight_label: string;
  opens_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LmsAssessmentManagementPage = {
  page_title: string;
  page_subtitle: string;
  primary_action_label: string;
  primary_action_href: string;
  assessments_section_title: string;
  table_headers: string[];
  assessment_rows: LmsAssessmentManagementRow[];
  empty_table_message: string;
  count_footer_label: string;
  pagination: PoliciesPagination;
  generated_at: string;
};

export type LmsAssessmentsPageQuery = {
  page?: number;
  page_size?: number;
};