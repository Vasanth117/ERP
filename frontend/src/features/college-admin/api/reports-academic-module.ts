import { apiRequest } from "@/lib/api/client";

import type {
  ReportsAcademicModulePage,
  ReportsAcademicPageQuery,
  ReportsModuleSection,
} from "@/features/college-admin/types/reports-academic-module";

function buildQuery(params?: ReportsAcademicPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  if (params?.academic_year) search.set("academic_year", params.academic_year);
  if (params?.department_id) search.set("department_id", params.department_id);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

function reportsModuleBasePath(section: ReportsModuleSection) {
  if (section === "people") return "people";
  if (section === "operations") return "operations";
  return "academic";
}

export function fetchReportsModulePage(
  section: ReportsModuleSection,
  pageKey: string,
  params?: ReportsAcademicPageQuery,
) {
  const base = reportsModuleBasePath(section);
  return apiRequest<ReportsAcademicModulePage>(
    `/college-admin/reports-analytics/${base}/${encodeURIComponent(pageKey)}/management/page${buildQuery(params)}`,
  );
}

export function fetchReportsAcademicModulePage(pageKey: string, params?: ReportsAcademicPageQuery) {
  return fetchReportsModulePage("academic", pageKey, params);
}

export function runReportsModuleReport(section: ReportsModuleSection, pageKey: string) {
  const base = reportsModuleBasePath(section);
  return apiRequest<{ job_id: string; report_key: string; status: string }>(
    `/college-admin/reports-analytics/${base}/${encodeURIComponent(pageKey)}/run`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export function runReportsAcademicReport(pageKey: string) {
  return runReportsModuleReport("academic", pageKey);
}