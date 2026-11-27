import { apiRequest } from "@/lib/api/client";

import type {
  CourseInfo,
  Curriculum,
  CurriculumOverview,
  CurriculumSemesterPage,
  CurriculumSubjectDetail,
  CurriculumSubjectList,
  CurriculumCategoriesElectivesPage,
  CurriculumHistoryPage,
  CurriculumSyllabusPage,
  EnrolledCourseItem,
  LearningOutcomesDetail,
  PrerequisiteDetail,
  SemesterSubjects,
  SubjectItem,
  SyllabusDetail,
} from "@/features/student/types/curriculum";

/** ST 03 — student curriculum read APIs (`/api/v1/students/me/curriculum/*`). */
const BASE = "/students";

export async function fetchCurriculum(): Promise<Curriculum> {
  return apiRequest<Curriculum>(`${BASE}/me/curriculum/programme`);
}

export async function fetchCurriculumOverview(): Promise<CurriculumOverview> {
  return apiRequest<CurriculumOverview>(`${BASE}/me/curriculum/overview`);
}

export async function fetchCurriculumSemesterPage(semester?: number): Promise<CurriculumSemesterPage> {
  const q = semester != null ? `?semester=${semester}` : "";
  return apiRequest<CurriculumSemesterPage>(`${BASE}/me/curriculum/semesters${q}`);
}

export type CurriculumSubjectListParams = {
  semester?: number;
  category?: string;
  status?: string;
  q?: string;
};

export async function fetchCurriculumSubjectList(
  params?: CurriculumSubjectListParams,
): Promise<CurriculumSubjectList> {
  const search = new URLSearchParams();
  if (params?.semester != null) search.set("semester", String(params.semester));
  if (params?.category) search.set("category", params.category);
  if (params?.status) search.set("status", params.status);
  if (params?.q) search.set("q", params.q);
  const qs = search.toString();
  return apiRequest<CurriculumSubjectList>(`${BASE}/me/curriculum/subjects${qs ? `?${qs}` : ""}`);
}

export async function fetchCurriculumSubjectDetail(courseCode: string): Promise<CurriculumSubjectDetail> {
  return apiRequest<CurriculumSubjectDetail>(
    `${BASE}/me/curriculum/subjects/${encodeURIComponent(courseCode)}`,
  );
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

export async function fetchCurriculumHistoryPage(): Promise<CurriculumHistoryPage> {
  return apiRequest<CurriculumHistoryPage>(`${BASE}/me/curriculum/history`);
}

export async function fetchCurriculumCategoriesElectivesPage(): Promise<CurriculumCategoriesElectivesPage> {
  return apiRequest<CurriculumCategoriesElectivesPage>(`${BASE}/me/curriculum/categories-electives`);
}

export async function fetchCurriculumSyllabusPage(
  courseCode: string,
  unitNo?: number,
): Promise<CurriculumSyllabusPage> {
  const q = unitNo != null ? `?unit=${unitNo}` : "";
  return apiRequest<CurriculumSyllabusPage>(
    `${BASE}/me/curriculum/syllabus/${encodeURIComponent(courseCode)}${q}`,
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