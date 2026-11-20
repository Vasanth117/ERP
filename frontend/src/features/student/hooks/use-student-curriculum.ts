"use client";

import { useQuery } from "@tanstack/react-query";

import {
  fetchCourseInfo,
  fetchCurriculum,
  fetchEnrolledCourses,
  fetchLearningOutcomes,
  fetchPrerequisites,
  fetchSemesterSubjects,
  fetchSyllabus,
  fetchSubjectsForCourse,
} from "@/features/student/api/curriculum";
import { studentQueryKeys } from "@/features/student/query-keys";

export function useCurriculum() {
  return useQuery({
    queryKey: studentQueryKeys.curriculum(),
    queryFn: fetchCurriculum,
  });
}

export function useEnrolledCourses() {
  return useQuery({
    queryKey: studentQueryKeys.enrolledCourses(),
    queryFn: fetchEnrolledCourses,
  });
}

export function useSemesterSubjects() {
  return useQuery({
    queryKey: studentQueryKeys.semesterSubjects(),
    queryFn: fetchSemesterSubjects,
  });
}

export function useSubjectsForCourse(courseCode: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.subjectsForCourse(courseCode ?? ""),
    queryFn: () => fetchSubjectsForCourse(courseCode!),
    enabled: Boolean(courseCode),
  });
}

export function useSyllabus(courseCode: string | null, subjectId?: string) {
  return useQuery({
    queryKey: studentQueryKeys.syllabus(courseCode ?? "", subjectId),
    queryFn: () => fetchSyllabus(courseCode!, subjectId),
    enabled: Boolean(courseCode),
  });
}

export function useLearningOutcomes(courseCode: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.outcomes(courseCode ?? ""),
    queryFn: () => fetchLearningOutcomes(courseCode!),
    enabled: Boolean(courseCode),
  });
}

export function usePrerequisites(courseCode: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.prerequisites(courseCode ?? ""),
    queryFn: () => fetchPrerequisites(courseCode!),
    enabled: Boolean(courseCode),
  });
}

export function useCourseInfo(courseCode: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.courseInfo(courseCode ?? ""),
    queryFn: () => fetchCourseInfo(courseCode!),
    enabled: Boolean(courseCode),
  });
}