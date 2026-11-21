import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";

export type DepartmentFacultyCapacityRow = {
  department_id: string;
  department_label: string;
  sanctioned: number;
  in_position: number;
  vacant: number;
  workload_pct: number | null;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type DepartmentFacultyVacancyItem = {
  department_id: string;
  department_label: string;
  detail: string;
  count: number;
  badge_tone: string;
};

export type DepartmentFacultyDesignationBar = {
  key: string;
  label: string;
  value: number;
  max_value: number;
};

export type DepartmentFacultyAllocationFormValues = {
  faculty_user_id: string;
  allocate_to_department_id: string;
  allocation_type: string;
  effective_from: string;
};

export type DepartmentFacultyAllocationPage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  allocate_faculty_label: string;
  allocate_faculty_href: string;
  semester_filter_label: string;
  department_filter_label: string;
  designation_filter_label: string;
  resources_nav_label: string;
  resources_nav_href: string;
  updated_at_label: string;
  semester_options: InstitutionFieldOption[];
  department_options: InstitutionFieldOption[];
  designation_options: InstitutionFieldOption[];
  selected_semester: string;
  selected_department_id: string;
  selected_designation: string;
  capacity_section_title: string;
  capacity_table_headers: string[];
  capacity_table_footer_note: string;
  capacity_rows: DepartmentFacultyCapacityRow[];
  pagination: PoliciesPagination;
  move_share_section_title: string;
  faculty_field_label: string;
  faculty_options: InstitutionFieldOption[];
  allocate_to_field_label: string;
  department_allocate_options: InstitutionFieldOption[];
  allocation_type_field_label: string;
  allocation_type_options: InstitutionFieldOption[];
  effective_from_field_label: string;
  form: DepartmentFacultyAllocationFormValues;
  move_footer_note: string;
  cancel_label: string;
  save_label: string;
  vacancies_section_title: string;
  hr_recruitment_label: string;
  hr_recruitment_href: string;
  vacancy_items: DepartmentFacultyVacancyItem[];
  designation_mix_section_title: string;
  designation_bars: DepartmentFacultyDesignationBar[];
  can_save: boolean;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

export type DepartmentFacultyAllocationSaveResult = {
  message: string;
  page: DepartmentFacultyAllocationPage;
};