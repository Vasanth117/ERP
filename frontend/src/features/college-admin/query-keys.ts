export const collegeAdminQueryKeys = {
  all: ["college-admin"] as const,
  dashboard: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "dashboard", params ?? {}] as const,
  dashboardStats: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "dashboard-stats", params ?? {}] as const,
  dashboardOperations: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "dashboard-operations", params ?? {}] as const,
  pendingApprovals: (offset?: number, limit?: number) =>
    [
      ...collegeAdminQueryKeys.all,
      "pending-approvals",
      offset ?? 0,
      limit ?? 20,
    ] as const,
  activities: (offset?: number, limit?: number, range?: string) =>
    [
      ...collegeAdminQueryKeys.all,
      "activities",
      offset ?? 0,
      limit ?? 20,
      range ?? "week",
    ] as const,
  profile: () => [...collegeAdminQueryKeys.all, "institution-profile"] as const,
  institutionalOverview: () =>
    [...collegeAdminQueryKeys.all, "institutional-overview"] as const,
  studentStatistics: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-statistics", params ?? {}] as const,
  facultyStatistics: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "faculty-statistics", params ?? {}] as const,
  departmentPerformance: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "department-performance", params ?? {}] as const,
  academicPerformance: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "academic-performance", params ?? {}] as const,
  attendanceOverview: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "attendance-overview", params ?? {}] as const,
  examinationOverview: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "examination-overview", params ?? {}] as const,
  financeOverview: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "finance-overview", params ?? {}] as const,
  pendingApprovalsOverview: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "pending-approvals-overview", params ?? {}] as const,
  recentActivitiesOverview: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "recent-activities-overview", params ?? {}] as const,
  alertsOverview: () => [...collegeAdminQueryKeys.all, "alerts-overview"] as const,
  campuses: (activeOnly?: boolean) =>
    [...collegeAdminQueryKeys.all, "campuses", activeOnly ?? false] as const,
  campus: (id: string) => [...collegeAdminQueryKeys.all, "campus", id] as const,
  settings: () => [...collegeAdminQueryKeys.all, "institution-settings"] as const,
  configHistory: () =>
    [...collegeAdminQueryKeys.all, "configuration-history"] as const,
};