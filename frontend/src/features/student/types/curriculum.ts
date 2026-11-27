export type EnrolledCourseItem = {
  course_id: string;
  course_code: string;
  name: string;
  section_code: string | null;
  credit_units: number;
  academic_year_label: string;
  semester_label: string;
  source: string;
};

export type SubjectItem = {
  subject_id: string;
  subject_code: string;
  name: string;
  description: string | null;
  credit_units: number;
  sequence_order: number;
};

export type Curriculum = {
  programme_code: string;
  academic_year_label: string;
  semester_label: string;
  version: string | null;
  summary: string | null;
  academic_regulations: string[];
  locked: boolean;
};

export type CurriculumOverviewKpis = {
  total_credits: number;
  total_semesters: number;
  total_credits_semester_hint: string | null;
  core_subjects: number;
  electives: number;
  elective_credits: number;
  elective_credits_hint: string | null;
  labs: number;
};

export type CurriculumOverviewSemesterRow = {
  semester_number: number;
  label: string;
  subject_count: number;
  credits: number;
  status_code: string;
  status_label: string;
  status_tone: string;
};

export type CurriculumOverview = {
  page_title: string;
  programme_headline: string;
  programme_code: string;
  regulation_label: string | null;
  kpis: CurriculumOverviewKpis;
  semesters: CurriculumOverviewSemesterRow[];
  semesters_footer_label: string;
};

export type CurriculumSemesterTab = {
  semester_number: number;
  tab_label: string;
};

export type CurriculumSemesterCourseRow = {
  course_id: string;
  course_code: string;
  course_name: string;
  type_label: string;
  ltp_label: string;
  credits: number;
  status_code: string;
  status_label: string;
  status_tone: string;
  syllabus_href: string;
};

export type CurriculumSemesterCreditCategory = {
  category_key: string;
  category_label: string;
  credits: number;
  share_pct: number | null;
};

export type CurriculumSubjectFilterOption = {
  value: string;
  label: string;
};

export type CurriculumSubjectListRow = {
  course_id: string;
  course_code: string;
  course_name: string;
  category_label: string;
  ltp_label: string;
  credits: number;
  status_code: string;
  status_label: string;
  status_tone: string;
  semester_number: number | null;
};

export type CurriculumSubjectList = {
  page_title: string;
  page_subtitle: string;
  filter_semester: number | null;
  filter_category: string;
  filter_status: string;
  search_query: string | null;
  semester_options: CurriculumSubjectFilterOption[];
  category_options: CurriculumSubjectFilterOption[];
  status_options: CurriculumSubjectFilterOption[];
  table_headers: string[];
  subjects: CurriculumSubjectListRow[];
  footer_label: string;
  total_matching: number;
};

export type CurriculumSubjectAssessment = {
  label: string;
  marks_label: string;
  kind: string;
};

export type CurriculumSubjectResource = {
  title: string;
  subtitle: string | null;
  kind: string;
};

export type CurriculumCreditComponentRow = {
  component_label: string;
  hours_per_week: number;
  credits: number;
  assessed_by: string;
  is_total?: boolean;
};

export type CurriculumSubjectCreditDetails = {
  page_title: string;
  page_subtitle: string;
  panel_title: string;
  table_headers: string[];
  rows: CurriculumCreditComponentRow[];
  footer_label: string;
};

export type CurriculumSubjectDetail = {
  page_title: string;
  headline: string;
  course_code: string;
  course_name: string;
  code: string;
  category_label: string;
  credits: number;
  ltp_label: string;
  faculty_label: string;
  regulation_label: string | null;
  objectives: string[];
  assessments: CurriculumSubjectAssessment[];
  resources: CurriculumSubjectResource[];
  syllabus_href: string;
  credit_details: CurriculumSubjectCreditDetails;
};

export type CurriculumSemesterPage = {
  page_title: string;
  programme_headline: string;
  programme_code: string;
  selected_semester: number;
  total_semesters: number;
  semester_tabs: CurriculumSemesterTab[];
  courses_panel_title: string;
  courses_panel_meta: string;
  table_headers: string[];
  courses: CurriculumSemesterCourseRow[];
  credit_categories: CurriculumSemesterCreditCategory[];
  semester_status_code: string;
  semester_status_label: string;
  semester_status_tone: string;
  courses_footer_label: string;
};

export type SyllabusUnit = {
  title: string;
  topics: string[];
  hours?: number | null;
};

export type TeachingMaterialRef = {
  ref: string;
  label: string;
  kind?: string | null;
};

export type SyllabusRevision = {
  version: string;
  effective_at: string;
  summary: string | null;
};

export type SyllabusDetail = {
  course_id: string;
  subject_id: string | null;
  academic_year_label: string;
  semester_label: string;
  units: SyllabusUnit[];
  objectives: string[];
  teaching_materials: TeachingMaterialRef[];
  revision_history: SyllabusRevision[];
  locked: boolean;
};

export type CurriculumSyllabusTopic = {
  title: string;
  hours: number;
};

export type CurriculumSyllabusUnitRow = {
  unit_no: number;
  title: string;
  planned_hours: number;
  topic_count: number;
  progress_code: string;
  progress_label: string;
  progress_tone: string;
};

export type CurriculumSyllabusResource = {
  title: string;
  subtitle: string | null;
  url: string | null;
  kind: string;
};

export type CurriculumSyllabusUnitDetail = {
  page_title: string;
  unit_no: number;
  headline: string;
  planned_hours: number;
  weightage_pct: number | null;
  co_mapping_label: string | null;
  topics: CurriculumSyllabusTopic[];
  learning_resources: CurriculumSyllabusResource[];
  open_materials_url: string | null;
  faculty_label: string | null;
};

export type CurriculumCategoryCourseRow = {
  course_code: string;
  course_name: string;
  credits: number;
};

export type CurriculumCategoryPanel = {
  panel_title: string;
  table_headers: string[];
  rows: CurriculumCategoryCourseRow[];
  footer_label: string;
};

export type CurriculumElectiveCatalogueRow = {
  course_code: string;
  course_name: string;
  group_label: string;
  credits: number;
  offered_in_label: string;
};

export type CurriculumHistoryRow = {
  version_label: string;
  regulation_label: string;
  effective_from_label: string;
  change_summary: string;
  applies_code: string;
  applies_label: string;
  applies_tone: string;
};

export type CurriculumHistoryPage = {
  page_title: string;
  page_subtitle: string;
  panel_title: string;
  table_headers: string[];
  rows: CurriculumHistoryRow[];
  footer_label: string;
};

export type CurriculumCategoriesElectivesPage = {
  categories_page_title: string;
  categories_page_subtitle: string;
  theory_panel: CurriculumCategoryPanel;
  practical_panel: CurriculumCategoryPanel;
  elective_page_title: string;
  elective_page_subtitle: string;
  elective_table_headers: string[];
  elective_rows: CurriculumElectiveCatalogueRow[];
  elective_footer_label: string;
  registration_href: string;
};

export type CurriculumSyllabusPage = {
  page_title: string;
  headline: string;
  course_code: string;
  course_name: string;
  units_panel_title: string;
  table_headers: string[];
  units: CurriculumSyllabusUnitRow[];
  units_footer_label: string;
  selected_unit_no: number | null;
  unit_detail: CurriculumSyllabusUnitDetail | null;
};

export type LearningOutcomesDetail = {
  course_id: string;
  academic_year_label: string;
  semester_label: string;
  outcomes: string[];
  locked: boolean;
};

export type PrerequisiteDetail = {
  course_id: string;
  course_code: string;
  prerequisite_course_ids: string[];
  corequisite_course_ids: string[];
  min_cgpa: number | null;
  notes: string | null;
};

export type FacultyInfo = {
  faculty_user_id: string;
  display_name: string;
  section: string;
  subject_code: string | null;
};

export type CourseInfo = {
  course_id: string;
  course_code: string;
  name: string;
  description: string | null;
  credit_units: number;
  faculty: FacultyInfo[];
};

export type SemesterSubjects = {
  academic_year_label: string;
  semester_label: string;
  subjects: SubjectItem[];
};