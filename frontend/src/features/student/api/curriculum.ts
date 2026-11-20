import { apiRequest } from "@/lib/api/client";

import type {
  CourseInfo,
  Curriculum,
  EnrolledCourseItem,
  LearningOutcomesDetail,
  PrerequisiteDetail,
  SemesterSubjects,
  SubjectItem,
  SyllabusDetail,
} from "@/features/student/types/curriculum";

const BASE = "/students";

export async function fetchCurriculum(): Promise<Curriculum> {
  return apiRequest<Curriculum>(`${BASE}/me/curriculum/programme`);
}

export async function fetchEnrolledCourses(): Promise<EnrolledCourseItem[]> {
  return apiRequest<EnrolledCourseItem[]>(`${BASE}/me/curriculum/courses`);
}

export async function fetchSemesterSubjects(): Promise<SemesterSubjects> {
  return apiRequest<SemesterSubjects>(`${BASE}/me/curriculum/semester-subjects`);
}

export async function fetchSubjectsForCourse(courseCode: string): Promise<SubjectItem[]> {
  return apiRequest<SubjectItem[]>(
    `${BASE}/me/curriculum/courses/${encodeURIComponent(courseCode)}/subjects`,
  );
}

export async function fetchSyllabus(
  courseCode: string,
  subjectId?: string,
): Promise<SyllabusDetail> {
  const q = subjectId ? `?subject_id=${encodeURIComponent(subjectId)}` : "";
  return apiRequest<SyllabusDetail>(
    `${BASE}/me/curriculum/courses/${encodeURIComponent(courseCode)}/syllabus${q}`,
  );
}

export async function fetchLearningOutcomes(courseCode: string): Promise<LearningOutcomesDetail> {
  return apiRequest<LearningOutcomesDetail>(
    `${BASE}/me/curriculum/courses/${encodeURIComponent(courseCode)}/outcomes`,
  );
}

export async function fetchPrerequisites(courseCode: string): Promise<PrerequisiteDetail> {
  return apiRequest<PrerequisiteDetail>(
    `${BASE}/me/curriculum/courses/${encodeURIComponent(courseCode)}/prerequisites`,
  );
}

export async function fetchCourseInfo(courseCode: string): Promise<CourseInfo> {
  return apiRequest<CourseInfo>(
    `${BASE}/me/curriculum/courses/${encodeURIComponent(courseCode)}/info`,
  );
}