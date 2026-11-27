import type {
  InstitutionPolicyFilterOption,
  PoliciesPagination,
} from "@/features/college-admin/types/institution";

export type LmsChannelAlertBanner = {
  tone: string;
  message: string;
  link_label: string;
  link_href: string;
};

export type LmsCourseManagementRow = {
  row_key: string;
  course_label: string;
  course_code: string;
  department_label: string;
  faculty_label: string;
  students_count: number;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LmsCourseManagementPage = {
  page_title: string;
  page_subtitle: string;
  primary_action_label: string;
  primary_action_href: string;
  search_placeholder: string;
  department_filter_label: string;
  status_filter_label: string;
  department_options: InstitutionPolicyFilterOption[];
  status_options: InstitutionPolicyFilterOption[];
  courses_section_title: string;
  table_headers: string[];
  course_rows: LmsCourseManagementRow[];
  empty_table_message: string;
  showing_label: string;
  count_footer_label: string;
  pagination: PoliciesPagination;
  generated_at: string;
};

export type LmsCourseManagementPageQuery = {
  page?: number;
  page_size?: number;
  search?: string;
  department?: string;
  status?: string;
};

export type LmsSubjectMappingRow = {
  row_key: string;
  subject_label: string;
  section_label: string;
  faculty_label: string;
  lms_course_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LmsSubjectCourseMappingPage = {
  page_title: string;
  page_subtitle: string;
  auto_map_action_label: string;
  save_mapping_action_label: string;
  save_mapping_enabled: boolean;
  alert_banner?: LmsChannelAlertBanner | null;
  mapping_section_title: string;
  table_headers: string[];
  mapping_rows: LmsSubjectMappingRow[];
  empty_table_message: string;
  showing_label: string;
  count_footer_label: string;
  pagination: PoliciesPagination;
  generated_at: string;
};

export type LmsSubjectCourseMappingPageQuery = {
  page?: number;
  page_size?: number;
};