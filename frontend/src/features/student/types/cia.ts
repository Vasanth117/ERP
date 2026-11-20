export type CiaSchedule = {
  id: string;
  title: string;
  course_code: string;
  assessment_type: string;
  scheduled_at: string;
  source: string;
};

export type AssessmentComponent = {
  assessment_id: string;
  component_id: string;
  code: string;
  name: string;
  component_type: string;
  max_marks: number;
  weight_percent: number;
};

export type PublishedMark = {
  assessment_id: string;
  component_id: string;
  course_code: string | null;
  subject_id: string | null;
  marks_obtained: number;
  max_marks: number;
  percentage: number;
  grade_letter: string | null;
  published_at: string;
  visibility: string;
};

export type SubjectInternalMarks = {
  course_code: string;
  subject_id: string | null;
  components: PublishedMark[];
  total_obtained: number;
  total_max: number;
  weighted_percentage: number | null;
};

export type CiaSummary = {
  academic_year_label: string;
  semester_label: string;
  published_count: number;
  unpublished_count: number;
  missing_count: number;
  subjects: SubjectInternalMarks[];
  unpublished_components: {
    assessment_id: string;
    component_id: string;
    component_name: string;
    course_code: string;
    visibility: string;
  }[];
};

export type MarksCorrectionStatus = {
  id: string;
  batch_id: string;
  status: string;
  reason: string;
  created_at: string;
  resolved_at: string | null;
};

export type CiaHistoryItem = {
  component_id: string;
  assessment_id: string;
  marks_obtained: number;
  max_marks: number;
  status: string;
  updated_at: string;
};

export type CiaFeedback = {
  feedback?: string;
  [key: string]: unknown;
};