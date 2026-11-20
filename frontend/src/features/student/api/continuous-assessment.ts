import { apiRequest } from "@/lib/api/client";

import type {
  AssessmentProgress,
  AssignmentDetail,
  AssignmentFeedback,
  AssignmentListItem,
  ContinuousAssessmentMark,
  QuizSchedule,
  ResubmissionEligibility,
  SubmissionStatus,
} from "@/features/student/types/continuous-assessment";

const BASE = "/students";

export function fetchAssessmentProgress() {
  return apiRequest<AssessmentProgress[]>(`${BASE}/me/assessments/progress`);
}

export function fetchAssignments() {
  return apiRequest<AssignmentListItem[]>(`${BASE}/me/assessments/assignments`);
}

export function fetchAssignmentDetail(assignmentId: string) {
  return apiRequest<AssignmentDetail>(
    `${BASE}/me/assessments/assignments/${encodeURIComponent(assignmentId)}`,
  );
}

export function fetchQuizSchedules() {
  return apiRequest<QuizSchedule[]>(`${BASE}/me/assessments/quizzes/schedules`);
}

export function fetchQuizResults() {
  return apiRequest<ContinuousAssessmentMark[]>(`${BASE}/me/assessments/quizzes/results`);
}

export function fetchAssignmentMarks() {
  return apiRequest<ContinuousAssessmentMark[]>(`${BASE}/me/assessments/marks`);
}

export function fetchSubmissionStatus(assignmentId: string) {
  return apiRequest<SubmissionStatus>(
    `${BASE}/me/assessments/assignments/${encodeURIComponent(assignmentId)}/submission`,
  );
}

export function fetchAssignmentFeedback(assignmentId: string) {
  return apiRequest<AssignmentFeedback>(
    `${BASE}/me/assessments/assignments/${encodeURIComponent(assignmentId)}/feedback`,
  );
}

export function fetchResubmissionEligibility(assignmentId: string) {
  return apiRequest<ResubmissionEligibility>(
    `${BASE}/me/assessments/assignments/${encodeURIComponent(assignmentId)}/resubmission-eligibility`,
  );
}