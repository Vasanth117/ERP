import type { PoliciesPagination } from "@/features/college-admin/types/institution";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type LmsStudentLearningProgressRow = {
  row_key: string;
  student_label: string;
  register_number: string;
  completion_percent: number;
  last_active_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LmsStudentLearningProgressPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  learners_section_title: string;
  table_headers: string[];
  kpis: UserDashboardKpi[];
  learner_rows: LmsStudentLearningProgressRow[];
  empty_table_message: string;
  count_footer_label: string;
  pagination: PoliciesPagination;
  generated_at: string;
};

export type LmsFacultyContentRow = {
  row_key: string;
  faculty_label: string;
  department_label: string;
  materials_count: number;
  videos_count: number;
  pending_review_count: number;
  detail_href: string;
};

export type LmsFacultyContentManagementPage = {
  page_title: string;
  page_subtitle: string;
  approve_selected_action_label: string;
  approve_selected_enabled: boolean;
  faculty_section_title: string;
  table_headers: string[];
  faculty_rows: LmsFacultyContentRow[];
  empty_table_message: string;
  count_footer_label: string;
  pagination: PoliciesPagination;
  generated_at: string;
};

export type LmsProgressFacultyPageQuery = {
  page?: number;
  page_size?: number;
};