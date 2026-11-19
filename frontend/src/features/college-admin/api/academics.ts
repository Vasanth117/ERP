import { apiRequest } from "@/lib/api/client";

export type AcademicYear = {
  year_id: string;
  label: string;
  status?: string;
  is_current?: boolean;
};

export type AcademicTerm = {
  term_id: string;
  label: string;
  academic_year_id?: string;
};

export type Programme = {
  programme_id: string;
  name: string;
  code?: string;
  department_id?: string;
};

export function fetchAcademicYears() {
  return apiRequest<AcademicYear[]>("/college-admin/academic-config/years");
}

export function fetchAcademicTerms(yearId?: string) {
  const q = yearId ? `?academic_year_id=${encodeURIComponent(yearId)}` : "";
  return apiRequest<AcademicTerm[]>(`/college-admin/academic-config/terms${q}`);
}

export function fetchProgrammes() {
  return apiRequest<Programme[]>("/college-admin/academic-config/programmes");
}

export function fetchConfigHistory() {
  return apiRequest<unknown[]>("/college-admin/academic-config/configuration-history");
}