import { apiRequest } from "@/lib/api/client";

import type {
  HrPayrollPageQuery,
  HrPayrollProcessingPage,
  HrSalarySlipManagementPage,
  HrSalaryStructureManagementPage,
} from "@/features/college-admin/types/hr-payroll";

function buildQuery(params?: HrPayrollPageQuery) {
  const search = new URLSearchParams();
  if (params?.page != null) search.set("page", String(params.page));
  if (params?.page_size != null) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

function runQuery(payrollRunId?: string) {
  return payrollRunId ? `?payroll_run_id=${encodeURIComponent(payrollRunId)}` : "";
}

export function fetchHrSalaryStructureManagementPage(params?: HrPayrollPageQuery) {
  return apiRequest<HrSalaryStructureManagementPage>(
    `/college-admin/hr-administration/payroll/salary-structure/page${buildQuery(params)}`,
  );
}

export function fetchHrPayrollProcessingPage(params?: HrPayrollPageQuery) {
  return apiRequest<HrPayrollProcessingPage>(
    `/college-admin/hr-administration/payroll/processing/page${buildQuery(params)}`,
  );
}

export function fetchHrSalarySlipManagementPage(params?: HrPayrollPageQuery) {
  return apiRequest<HrSalarySlipManagementPage>(
    `/college-admin/hr-administration/payroll/slips/page${buildQuery(params)}`,
  );
}

export function validateHrPayroll(payrollRunId?: string) {
  return apiRequest<{ payroll_run_id: string; status: string }>(
    `/college-admin/hr-administration/payroll/processing/validate${runQuery(payrollRunId)}`,
    { method: "POST" },
  );
}

export function processHrPayroll(payrollRunId?: string) {
  return apiRequest<{ payroll_run_id: string; status: string }>(
    `/college-admin/hr-administration/payroll/processing/process${runQuery(payrollRunId)}`,
    { method: "POST" },
  );
}

export function generateHrSalarySlips(payrollRunId?: string) {
  return apiRequest<{ generated: number }>(
    `/college-admin/hr-administration/payroll/slips/generate${runQuery(payrollRunId)}`,
    { method: "POST" },
  );
}

export function publishHrSalarySlips(payrollRunId?: string) {
  return apiRequest<{ published: number }>(
    `/college-admin/hr-administration/payroll/slips/publish${runQuery(payrollRunId)}`,
    { method: "POST" },
  );
}