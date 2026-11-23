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
  financeDashboardPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "finance-dashboard-page", params ?? {}] as const,
  feeStructureManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "fee-structure-management-page", params ?? {}] as const,
  studentFeeManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-fee-management-page", params ?? {}] as const,
  feeDemandInvoiceManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "fee-demand-invoice-management-page", params ?? {}] as const,
  onlinePaymentMonitoringPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "online-payment-monitoring-page", params ?? {}] as const,
  offlinePaymentCollectionPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "offline-payment-collection-page", params ?? {}] as const,
  paymentTransactionsPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "payment-transactions-page", params ?? {}] as const,
  receiptManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "receipt-management-page", params ?? {}] as const,
  outstandingDuesManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "outstanding-dues-management-page", params ?? {}] as const,
  scholarshipManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "scholarship-management-page", params ?? {}] as const,
  feeConcessionWaiverManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "fee-concession-waiver-management-page", params ?? {}] as const,
  refundManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "refund-management-page", params ?? {}] as const,
  paymentReconciliationPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "payment-reconciliation-page", params ?? {}] as const,
  financialReportsPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "financial-reports-page", params ?? {}] as const,
  financeSettingsPage: () => [...collegeAdminQueryKeys.all, "finance-settings-page"] as const,
  pendingApprovalsOverview: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "pending-approvals-overview", params ?? {}] as const,
  recentActivitiesOverview: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "recent-activities-overview", params ?? {}] as const,
  alertsOverview: () => [...collegeAdminQueryKeys.all, "alerts-overview"] as const,
  campusesDashboard: () =>
    [...collegeAdminQueryKeys.all, "campuses-dashboard"] as const,
  campusCreationPage: (campusId?: string) =>
    [...collegeAdminQueryKeys.all, "campus-creation-page", campusId ?? ""] as const,
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
  studentAdministrationDashboard: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-administration-dashboard", params ?? {}] as const,
  facultyEmployeeDashboard: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "faculty-employee-dashboard", params ?? {}] as const,
  attendanceDashboard: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "attendance-dashboard", params ?? {}] as const,
  studentAttendanceOverview: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-attendance-overview", params ?? {}] as const,
  departmentWiseAttendance: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "department-wise-attendance", params ?? {}] as const,
  subjectWiseAttendance: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "subject-wise-attendance", params ?? {}] as const,
  facultyAttendanceOverview: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "faculty-attendance-overview", params ?? {}] as const,
  attendanceMonitoring: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "attendance-monitoring", params ?? {}] as const,
  attendanceCorrectionRequests: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "attendance-correction-requests", params ?? {}] as const,
  attendanceApproval: (requestId?: string) =>
    [...collegeAdminQueryKeys.all, "attendance-approval", requestId ?? "default"] as const,
  attendanceConfiguration: () =>
    [...collegeAdminQueryKeys.all, "attendance-configuration"] as const,
  attendanceRulesPolicies: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "attendance-rules-policies", params ?? {}] as const,
  attendanceReports: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "attendance-reports", params ?? {}] as const,
  facultyDirectoryPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "faculty-directory-page", params ?? {}] as const,
  employeeDirectoryPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "employee-directory-page", params ?? {}] as const,
  facultyProfilePage: (recordId: string) =>
    [...collegeAdminQueryKeys.all, "faculty-profile-page", recordId] as const,
  addNewFacultyEmployeePage: () =>
    [...collegeAdminQueryKeys.all, "add-new-faculty-employee-page"] as const,
  employeeProfileManagementPage: (recordId?: string) =>
    [...collegeAdminQueryKeys.all, "employee-profile-management-page", recordId ?? "picker"] as const,
  departmentDesignationAssignmentPage: (recordId?: string) =>
    [...collegeAdminQueryKeys.all, "department-designation-assignment-page", recordId ?? "picker"] as const,
  facultySubjectAllocationPage: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "faculty-subject-allocation-page", params ?? {}] as const,
  facultyWorkloadManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "faculty-workload-management-page", params ?? {}] as const,
  facultyTimetablePage: (recordId?: string) =>
    [...collegeAdminQueryKeys.all, "faculty-timetable-page", recordId ?? "picker"] as const,
  employeeDocumentVerificationPage: (documentId?: string) =>
    [...collegeAdminQueryKeys.all, "employee-document-verification-page", documentId ?? ""] as const,
  employeeStatusManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "employee-status-management-page", params ?? {}] as const,
  facultyEmployeeHistoryPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "faculty-employee-history-page", params ?? {}] as const,
  allStudentsListPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "all-students-list-page", params ?? {}] as const,
  studentDetailsPage: (recordId: string) =>
    [...collegeAdminQueryKeys.all, "student-details-page", recordId] as const,
  studentAdmissionPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-admission-page", params ?? {}] as const,
  newStudentRegistrationPage: (admissionId?: string) =>
    [...collegeAdminQueryKeys.all, "new-student-registration-page", admissionId ?? "new"] as const,
  studentProfileManagementPage: (recordId?: string) =>
    [...collegeAdminQueryKeys.all, "student-profile-management-page", recordId ?? "picker"] as const,
  studentDocumentVerificationPage: (recordId?: string, documentKey?: string) =>
    [...collegeAdminQueryKeys.all, "student-document-verification-page", recordId ?? "none", documentKey ?? ""] as const,
  studentEnrollmentManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-enrollment-management-page", params ?? {}] as const,
  examRegistrationManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "exam-registration-management-page", params ?? {}] as const,
  examinationDashboardPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "examination-dashboard-page", params ?? {}] as const,
  examinationSessionManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "examination-session-management-page", params ?? {}] as const,
  examinationConfigurationPage: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "examination-configuration-page", params ?? {}] as const,
  examTimetableManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "exam-timetable-management-page", params ?? {}] as const,
  studentExamEligibilityPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-exam-eligibility-page", params ?? {}] as const,
  hallTicketAdministrationPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "hall-ticket-administration-page", params ?? {}] as const,
  examinationHallSeatingManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "examination-hall-seating-management-page", params ?? {}] as const,
  invigilatorAllocationPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "invigilator-allocation-page", params ?? {}] as const,
  marksEntryManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "marks-entry-management-page", params ?? {}] as const,
  internalExternalAssessmentPage: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "internal-external-assessment-page", params ?? {}] as const,
  resultProcessingPage: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "result-processing-page", params ?? {}] as const,
  resultApprovalPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "result-approval-page", params ?? {}] as const,
  resultPublicationPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "result-publication-page", params ?? {}] as const,
  revaluationManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "revaluation-management-page", params ?? {}] as const,
  supplementaryExaminationManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "supplementary-examination-management-page", params ?? {}] as const,
  batchSectionAllocationPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "batch-section-allocation-page", params ?? {}] as const,
  studentTransferManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-transfer-management-page", params ?? {}] as const,
  studentTransferCreatePage: () => [...collegeAdminQueryKeys.all, "student-transfer-create-page"] as const,
  studentPromotionManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-promotion-management-page", params ?? {}] as const,
  studentStatusManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-status-management-page", params ?? {}] as const,
  studentWithdrawalDiscontinuationPage: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-withdrawal-discontinuation-page", params ?? {}] as const,
  studentIdCardManagementPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "student-id-card-management-page", params ?? {}] as const,
  studentAcademicHistoryPage: (recordId?: string) =>
    [...collegeAdminQueryKeys.all, "student-academic-history-page", recordId ?? ""] as const,
  newAcademicYearWizard: (draftId?: string) =>
    [...collegeAdminQueryKeys.all, "new-academic-year-wizard", draftId ?? "new"] as const,
  academicYearDetails: (yearId: string) =>
    [...collegeAdminQueryKeys.all, "academic-year-details", yearId] as const,
  academicYearManagement: (page?: number) =>
    [...collegeAdminQueryKeys.all, "academic-year-management", page ?? 1] as const,
  semesterManagement: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "semester-management", params ?? {}] as const,
  programmeManagement: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "programme-management", params ?? {}] as const,
  programmeDetails: (programmeId: string) =>
    [...collegeAdminQueryKeys.all, "programme-details", programmeId] as const,
  subjectManagement: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "subject-management", params ?? {}] as const,
  curriculumManagement: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "curriculum-management", params ?? {}] as const,
  courseConfiguration: (params?: Record<string, string | undefined>) =>
    [...collegeAdminQueryKeys.all, "course-configuration", params ?? {}] as const,
  creditConfiguration: () => [...collegeAdminQueryKeys.all, "credit-configuration"] as const,
  gradingSystemConfiguration: () => [...collegeAdminQueryKeys.all, "grading-system-configuration"] as const,
  regulationManagement: (regulationCode?: string) =>
    [...collegeAdminQueryKeys.all, "regulation-management", regulationCode ?? ""] as const,
  academicCalendarConfiguration: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "academic-calendar-configuration", params ?? {}] as const,
  batchSectionConfiguration: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "batch-section-configuration", params ?? {}] as const,
  academicConfigurationHistoryPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "academic-configuration-history-page", params ?? {}] as const,
  allDepartmentsListPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "all-departments-list-page", params ?? {}] as const,
  createEditDepartmentPage: (departmentId: string | null) =>
    [...collegeAdminQueryKeys.all, "create-edit-department-page", departmentId ?? "new"] as const,
  departmentDetailsPage: (departmentId: string | null) =>
    [...collegeAdminQueryKeys.all, "department-details-page", departmentId ?? "none"] as const,
  departmentHeadAssignmentPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "department-head-assignment-page", params ?? {}] as const,
  organizationalHierarchyPage: (selectedNodeId?: string, editMode?: boolean) =>
    [
      ...collegeAdminQueryKeys.all,
      "organizational-hierarchy-page",
      selectedNodeId ?? "default",
      editMode ? "edit" : "view",
    ] as const,
  programmeCourseMappingPage: (departmentId?: string) =>
    [...collegeAdminQueryKeys.all, "programme-course-mapping-page", departmentId ?? "default"] as const,
  departmentFacultyAllocationPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "department-faculty-allocation-page", params ?? {}] as const,
  departmentStatusHistoryPage: (params?: Record<string, string | number | undefined>) =>
    [...collegeAdminQueryKeys.all, "department-status-history-page", params ?? {}] as const,
  departmentResourceManagementPage: (departmentId?: string) =>
    [...collegeAdminQueryKeys.all, "department-resource-management-page", departmentId ?? "default"] as const,
};