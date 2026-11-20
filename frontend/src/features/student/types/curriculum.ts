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