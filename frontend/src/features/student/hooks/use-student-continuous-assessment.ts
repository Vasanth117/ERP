"use client";

import { useQuery } from "@tanstack/react-query";

import {
  fetchAssessmentProgress,
  fetchAssignmentDetail,
  fetchAssignmentFeedback,
  fetchAssignmentMarks,
  fetchAssignments,
  fetchQuizResults,
  fetchQuizSchedules,
  fetchResubmissionEligibility,
  fetchSubmissionStatus,
} from "@/features/student/api/continuous-assessment";
import { studentQueryKeys } from "@/features/student/query-keys";

export function useAssessmentProgress() {
  return useQuery({
    queryKey: studentQueryKeys.assessmentProgress(),
    queryFn: fetchAssessmentProgress,
  });
}

export function useAssignments() {
  return useQuery({
    queryKey: studentQueryKeys.assignments(),
    queryFn: fetchAssignments,
  });
}

export function useAssignmentDetail(assignmentId: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.assignmentDetail(assignmentId ?? ""),
    queryFn: () => fetchAssignmentDetail(assignmentId!),
    enabled: Boolean(assignmentId),
  });
}

export function useQuizSchedules() {
  return useQuery({
    queryKey: studentQueryKeys.quizSchedules(),
    queryFn: fetchQuizSchedules,
  });
}

export function useQuizResults() {
  return useQuery({
    queryKey: studentQueryKeys.quizResults(),
    queryFn: fetchQuizResults,
  });
}

export function useAssignmentMarks() {
  return useQuery({
    queryKey: studentQueryKeys.assignmentMarks(),
    queryFn: fetchAssignmentMarks,
  });
}

export function useSubmissionStatus(assignmentId: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.submissionStatus(assignmentId ?? ""),
    queryFn: () => fetchSubmissionStatus(assignmentId!),
    enabled: Boolean(assignmentId),
  });
}

export function useAssignmentFeedback(assignmentId: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.assignmentFeedback(assignmentId ?? ""),
    queryFn: () => fetchAssignmentFeedback(assignmentId!),
    enabled: Boolean(assignmentId),
  });
}

export function useResubmissionEligibility(assignmentId: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.resubmissionEligibility(assignmentId ?? ""),
    queryFn: () => fetchResubmissionEligibility(assignmentId!),
    enabled: Boolean(assignmentId),
  });
}