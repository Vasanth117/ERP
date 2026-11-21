const collegeAdminRoot = ["college-admin"] as const;

export const createNewUserPageQueryKey = [
  ...collegeAdminRoot,
  "create-new-user-page",
] as const;

export const collegeAdminQueryKeys = {
  all: collegeAdminRoot,
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
  createNewUserPage: () => createNewUserPageQueryKey,
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
  accountStatusPage: (tab: string, page: number, userId: string | null) =>
    [
      ...collegeAdminQueryKeys.all,
      "account-status-page",
      tab,
      page,
      userId ?? "none",
    ] as const,
  loginAccountActivityPage: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "login-account-activity-page", params ?? {}] as const,
  departmentManagementDashboard: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "department-management-dashboard", params ?? {}] as const,
  academicConfigurationDashboard: () =>
    [...collegeAdminQueryKeys.all, "academic-configuration-dashboard"] as const,
  academicYearManagement: (page?: number) =>
    [...collegeAdminQueryKeys.all, "academic-year-management", page ?? 1] as const,
  semesterManagement: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "semester-management", params ?? {}] as const,
  programmeManagement: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "programme-management", params ?? {}] as const,
  subjectManagement: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "subject-management", params ?? {}] as const,
  curriculumManagement: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "curriculum-management", params ?? {}] as const,
  courseConfiguration: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "course-configuration", params ?? {}] as const,
  allDepartmentsListPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "all-departments-list-page", params ?? {}] as const,
  createEditDepartmentPage: (departmentId: string | null) =>
    [...collegeAdminQueryKeys.all, "create-edit-department-page", departmentId ?? "new"] as const,
  departmentDetailsPage: (departmentId: string | null) =>
    [...collegeAdminQueryKeys.all, "department-details-page", departmentId ?? "none"] as const,
  departmentHeadAssignmentPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "department-head-assignment-page", params ?? {}] as const,
  organizationalHierarchyPage: (selectedNodeId?: string) =>
    [...collegeAdminQueryKeys.all, "organizational-hierarchy-page", selectedNodeId ?? "default"] as const,
  programmeCourseMappingPage: (departmentId?: string) =>
    [...collegeAdminQueryKeys.all, "programme-course-mapping-page", departmentId ?? "default"] as const,
  departmentFacultyAllocationPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "department-faculty-allocation-page", params ?? {}] as const,
  departmentStatusHistoryPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "department-status-history-page", params ?? {}] as const,
  departmentResourceManagementPage: (departmentId?: string) =>
    [...collegeAdminQueryKeys.all, "department-resource-management-page", departmentId ?? "default"] as const,
};