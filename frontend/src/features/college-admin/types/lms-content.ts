import type { PoliciesPagination } from "@/features/college-admin/types/institution";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";

export type LmsLearningMaterialRow = {
  row_key: string;
  material_label: string;
  course_code: string;
  type_label: string;
  uploaded_by_label: string;
  date_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LmsLearningMaterialManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label?: string;
  primary_action_label: string;
  primary_action_href: string;
  materials_section_title: string;
  table_headers: string[];
  material_rows: LmsLearningMaterialRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: PoliciesPagination;
  generated_at: string;
};

export type LmsLearningMaterialPageQuery = {
  page?: number;
  page_size?: number;
};

export type LmsVideoLectureRow = {
  row_key: string;
  lecture_label: string;
  course_code: string;
  length_label: string;
  views_label: string;
  uploaded_label: string;
  status_label: string;
  status_tone: string;
  detail_href: string;
};

export type LmsVideoLectureManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label?: string;
  primary_action_label: string;
  primary_action_href: string;
  kpis: UserDashboardKpi[];
  videos_section_title: string;
  table_headers: string[];
  video_rows: LmsVideoLectureRow[];
  empty_table_message: string;
  count_footer_label: string;
  pagination: PoliciesPagination;
  generated_at: string;
};

export type LmsVideoLecturePageQuery = {
  page?: number;
  page_size?: number;
};

export type LmsChapterRow = {
  row_key: string;
  chapter_label: string;
  materials_count_label: string;
  detail_href?: string | null;
};

export type LmsUnitChapterRow = {
  row_key: string;
  unit_label: string;
  chapter_count_label: string;
  status_label: string;
  status_tone: string;
  default_expanded: boolean;
  chapters: LmsChapterRow[];
};

export type LmsUnitChapterCourseOption = {
  course_code: string;
  course_label: string;
  selected: boolean;
};

export type LmsUnitChapterManagementPage = {
  page_title: string;
  page_subtitle: string;
  export_label?: string;
  primary_action_label: string;
  primary_action_href: string;
  course_header_label: string;
  course_options: LmsUnitChapterCourseOption[];
  unit_rows: LmsUnitChapterRow[];
  empty_message: string;
  generated_at: string;
};

export type LmsUnitChapterPageQuery = {
  course_code?: string;
};