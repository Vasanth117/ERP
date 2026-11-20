export type AssignmentListItem = {
  id: string;
  title: string;
  course_code: string;
  section: string;
  deadline_at: string;
  max_marks: number;
  instructions_preview: string;
};

export type AssignmentDetail = {
  id: string;
  title: string;
  course_code: string;
  section: string;
  instructions: string;
  max_marks: number;
  deadline_at: string;
  academic_year_label: string;
  semester_label: string;
};

export type QuizSchedule = {
  id: string;
  title: string;
  course_code: string;
  scheduled_at: string;
  assessment_type: string;
};

export type SubmissionStatus = {
  assignment_id: string;
  status: string;
  submitted_at: string | null;
  file_name: string | null;
  late: boolean;
  missing: boolean;
  evaluated: boolean;
};

export type ContinuousAssessmentMark = {
  assignment_id: string;
  course_code: string;
  title: string;
  marks_awarded: number | null;
  max_marks: number;
  visibility: string;
  evaluated_at: string | null;
};

export type AssignmentFeedback = {
  assignment_id: string;
  submission_id: string;
  feedback: string;
  created_at: string;
};

export type ResubmissionEligibility = {
  assignment_id: string;
  eligible: boolean;
  reasons: string[];
  max_resubmissions: number;
  attempts_used: number;
};

export type AssessmentProgress = {
  assignment_id: string;
  course_code: string;
  title: string;
  submission_status: string;
  evaluation_published: boolean;
  marks_awarded: number | null;
  pending_evaluation: boolean;
};