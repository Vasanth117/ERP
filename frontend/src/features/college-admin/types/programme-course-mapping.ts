import type { OrganizationModuleEmptyState } from "@/features/college-admin/types/organization-module";

export type ProgrammeCourseMappingDepartmentTab = {
  department_id: string;
  tab_label: string;
  is_selected: boolean;
};

export type ProgrammeOwnedRow = {
  programme_id: string;
  programme_name: string;
  level_label: string;
  duration_label: string;
  intake_label: string;
  regulation_label: string;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type ServiceCourseRow = {
  course_id: string;
  course_label: string;
  taught_to_label: string;
  semester_label: string;
  student_count: number;
};

export type UnmappedCourseItem = {
  course_id: string;
  course_label: string;
  detail: string;
  action_code: string;
  action_label: string;
  action_tone: string;
};

export type CourseLoadBarItem = {
  key: string;
  label: string;
  value: number;
  max_value: number;
};

export type ProgrammeCourseMappingPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  map_programme_label: string;
  map_programme_href: string;
  department_tabs: ProgrammeCourseMappingDepartmentTab[];
  more_departments: ProgrammeCourseMappingDepartmentTab[];
  selected_department_id: string;
  selected_department_name: string;
  programmes_section_title: string;
  programmes_table_headers: string[];
  programmes: ProgrammeOwnedRow[];
  programmes_count_label: string;
  academic_configuration_label: string;
  academic_configuration_href: string;
  service_courses_section_title: string;
  service_table_headers: string[];
  service_courses: ServiceCourseRow[];
  service_courses_count_label: string;
  service_view_all_label: string;
  service_view_all_href: string;
  unmapped_section_title: string;
  unmapped_items: UnmappedCourseItem[];
  course_load_section_title: string;
  course_load_bars: CourseLoadBarItem[];
  footer_disclaimer: string;
  footer_snapshot_label: string;
  setup_empty_state?: OrganizationModuleEmptyState | null;
  generated_at: string;
};