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
  profilePage: () =>
    [...collegeAdminQueryKeys.all, "institution-profile-page"] as const,
  informationPage: () =>
    [...collegeAdminQueryKeys.all, "institution-information-page"] as const,
  brandingPage: () =>
    [...collegeAdminQueryKeys.all, "institution-branding-page"] as const,
  academicSettingsPage: () =>
    [...collegeAdminQueryKeys.all, "institution-academic-settings-page"] as const,
  policiesPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "institution-policies-page", params ?? {}] as const,
  academicYearPage: (selectedYearId?: string) =>
    [...collegeAdminQueryKeys.all, "institution-academic-year-page", selectedYearId ?? ""] as const,
  calendarSettingsPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "institution-calendar-settings-page", params ?? {}] as const,
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
  campusesDashboard: () =>
    [...collegeAdminQueryKeys.all, "campuses-dashboard"] as const,
  campusDetailPage: (campusId: string) =>
    [...collegeAdminQueryKeys.all, "campus-detail-page", campusId] as const,
  campusContactPage: (campusId: string) =>
    [...collegeAdminQueryKeys.all, "campus-contact-page", campusId] as const,
  campuses: (activeOnly?: boolean) =>
    [...collegeAdminQueryKeys.all, "campuses", activeOnly ?? false] as const,
  campus: (id: string) => [...collegeAdminQueryKeys.all, "campus", id] as const,
  settings: () => [...collegeAdminQueryKeys.all, "institution-settings"] as const,
  configHistory: () =>
    [...collegeAdminQueryKeys.all, "configuration-history"] as const,
  configurationHistoryPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "configuration-history-page", params ?? {}] as const,
  userManagementDashboard: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "user-management-dashboard", params ?? {}] as const,
  allUsersListPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "all-users-list-page", params ?? {}] as const,
  userDetailsPage: (userId: string) =>
    [...collegeAdminQueryKeys.all, "user-details-page", userId] as const,
  createNewUserPage: () => [...collegeAdminQueryKeys.all, "create-new-user-page"] as const,
  editUserInformationPage: (userId: string) =>
    [...collegeAdminQueryKeys.all, "edit-user-information-page", userId] as const,
  bulkUserInvitationPage: (page?: number) =>
    [...collegeAdminQueryKeys.all, "bulk-user-invitation-page", page ?? 1] as const,
  roleManagementDashboard: (page?: number) =>
    [...collegeAdminQueryKeys.all, "role-management-dashboard", page ?? 1] as const,
  createEditRolePage: (roleId: string | null) =>
    [...collegeAdminQueryKeys.all, "create-edit-role-page", roleId ?? "new"] as const,
  permissionManagementPage: () =>
    [...collegeAdminQueryKeys.all, "permission-management-page"] as const,
  roleAssignmentPage: (userId: string | null, roleId: string | null) =>
    [
      ...collegeAdminQueryKeys.all,
      "role-assignment-page",
      userId ?? "none",
      roleId ?? "none",
    ] as const,
};