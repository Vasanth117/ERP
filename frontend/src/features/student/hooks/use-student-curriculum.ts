"use client";

import { useQuery } from "@tanstack/react-query";

import {
  fetchCourseInfo,
  fetchCurriculum,
  fetchCurriculumOverview,
  fetchCurriculumSemesterPage,
  fetchCurriculumSubjectDetail,
  fetchCurriculumSubjectList,
  fetchCurriculumCategoriesElectivesPage,
  fetchCurriculumHistoryPage,
  fetchCurriculumSyllabusPage,
  type CurriculumSubjectListParams,
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

export function useCurriculumOverview() {
  return useQuery({
    queryKey: studentQueryKeys.curriculumOverview(),
    queryFn: fetchCurriculumOverview,
    retry: false,
  });
}

export function useCurriculumSemesterPage(semester?: number) {
  return useQuery({
    queryKey: studentQueryKeys.curriculumSemester(semester),
    queryFn: () => fetchCurriculumSemesterPage(semester),
    retry: false,
  });
}

export function useCurriculumSubjectList(params?: CurriculumSubjectListParams) {
  return useQuery({
    queryKey: studentQueryKeys.curriculumSubjectList(params),
    queryFn: () => fetchCurriculumSubjectList(params),
    retry: false,
  });
}

export function useCurriculumSubjectDetail(courseCode: string | null) {
  return useQuery({
    queryKey: studentQueryKeys.curriculumSubjectDetail(courseCode ?? ""),
    queryFn: () => fetchCurriculumSubjectDetail(courseCode!),
    enabled: Boolean(courseCode),
    retry: false,
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

export function useCurriculumHistoryPage() {
  return useQuery({
    queryKey: studentQueryKeys.curriculumHistory(),
    queryFn: fetchCurriculumHistoryPage,
    retry: false,
  });
}

export function useCurriculumCategoriesElectivesPage() {
  return useQuery({
    queryKey: studentQueryKeys.curriculumCategoriesElectives(),
    queryFn: fetchCurriculumCategoriesElectivesPage,
    retry: false,
  });
}

export function useCurriculumSyllabusPage(courseCode: string | null, unitNo?: number | null) {
  return useQuery({
    queryKey: studentQueryKeys.curriculumSyllabusPage(courseCode ?? "", unitNo ?? undefined),
    queryFn: () => fetchCurriculumSyllabusPage(courseCode!, unitNo ?? undefined),
    enabled: Boolean(courseCode),
    retry: false,
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