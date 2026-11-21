import type { PoliciesPagination } from "@/features/college-admin/types/institution";
import type { YearsSemestersSubNavItem } from "@/features/college-admin/types/academic-year-management";

export type FilterOption = { value: string; label: string };

export type SubjectManagementRow = {
  course_id: string;
  subject_name: string;
  subject_code: string;
  department_label: string;
  type_label: string;
  credits_label: string;
  semester_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
  configuration_href: string;
};

export type SubjectManagementPage = {
  page_title: string;
  page_subtitle: string;
  import_label: string;
  add_subject_label: string;
  add_subject_href: string;
  search_placeholder: string;
  department_filter_label: string;
  type_filter_label: string;
  regulation_filter_label: string;
  semester_filter_label: string;
  department_options: FilterOption[];
  type_options: FilterOption[];
  regulation_options: FilterOption[];
  semester_options: FilterOption[];
  subjects_section_title: string;
  subjects_count_label: string;
  table_headers: string[];
  subjects: SubjectManagementRow[];
  showing_label: string;
  pagination: PoliciesPagination;
  sub_nav: YearsSemestersSubNavItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type CurriculumSemesterTab = {
  semester_number: number;
  tab_label: string;
  is_selected: boolean;
};

export type CurriculumCourseRow = {
  course_id: string;
  course_code: string;
  course_name: string;
  type_label: string;
  ltp_label: string;
  credits_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
  configuration_href: string;
};

export type CurriculumCreditRow = {
  category_key: string;
  category_label: string;
  credits: number;
  share_pct: number | null;
};

export type CurriculumSummaryField = { key: string; label: string; value: string };

export type CurriculumManagementPage = {
  page_title: string;
  page_subtitle: string;
  download_pdf_label: string;
  subjects_button_label: string;
  subjects_button_href: string;
  edit_curriculum_label: string;
  edit_curriculum_href: string;
  programme_options: FilterOption[];
  selected_programme_id: string | null;
  selected_programme_label: string;
  regulation_label: string;
  semester_tabs: CurriculumSemesterTab[];
  selected_semester: number;
  courses_panel_title: string;
  courses_panel_meta: string;
  table_headers: string[];
  courses: CurriculumCourseRow[];
  approval_footer_label: string;
  version_history_label: string;
  version_history_href: string;
  credits_panel_title: string;
  credit_categories: CurriculumCreditRow[];
  summary_panel_title: string;
  summary_fields: CurriculumSummaryField[];
  sub_nav: YearsSemestersSubNavItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type CourseConfigurationForm = {
  course_id: string | null;
  course_code: string;
  course_title: string;
  department_id: string | null;
  course_type: string | null;
  semester_number: number | null;
  regulation_label: string | null;
  description: string | null;
  lecture_hours: number;
  tutorial_hours: number;
  practical_hours: number;
  credit_units: number;
  internal_assessment_label: string | null;
  end_semester_exam_label: string | null;
  exam_duration_label: string | null;
  exam_type_label: string | null;
};

export type CourseConfigurationPage = {
  page_title: string;
  page_subtitle: string;
  status_label: string;
  status_tone: string;
  cancel_label: string;
  save_label: string;
  form_note: string;
  details_section_title: string;
  hours_section_title: string;
  assessment_section_title: string;
  prerequisites_section_title: string;
  offered_section_title: string;
  outcomes_section_title: string;
  outcomes_edit_label: string;
  outcomes_edit_href: string;
  field_meta: { key: string; label: string; required: boolean; field_type: string }[];
  department_options: FilterOption[];
  course_type_options: FilterOption[];
  semester_options: FilterOption[];
  regulation_options: FilterOption[];
  exam_duration_options: FilterOption[];
  exam_type_options: FilterOption[];
  form: CourseConfigurationForm;
  prerequisites: {
    prerequisite_id: string;
    title: string;
    semester_hint: string | null;
    requirement_type: string;
    requirement_label: string;
    requirement_tone: string;
  }[];
  offered_to: { programme_label: string; detail_label: string }[];
  outcomes_text: string | null;
  sub_nav: YearsSemestersSubNavItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type CourseConfigurationSavePayload = {
  course_id?: string | null;
  form: CourseConfigurationForm;
};