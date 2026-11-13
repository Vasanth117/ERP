"""MongoDB connection.

The ERP database is MongoDB. Beanie stores Pydantic documents through Motor.
SQLAlchemy and Alembic target relational databases, so they are not part of this
service. Tenant isolation is enforced on each request in the API and repositories.
"""

import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def document_models() -> list[type]:
    from app.modules.audit.models import AuditLog
    from app.modules.auth.models import RefreshToken, User
    from app.modules.tenants.models import Department, Tenant
    from app.modules.platform_identity.models import (
        PlatformAccessReview,
        PlatformInvitation,
        PlatformOperatorProfile,
        PlatformRoleAssignment,
        PlatformRoleDefinition,
        PlatformSession,
    )
    from app.modules.platform_security.models import PlatformAuditLog, SecurityEvent
    from app.modules.support_access.models import (
        SupportAccessActivity,
        SupportAccessApproval,
        SupportAccessRequest,
        SupportAccessSession,
    )
    from app.modules.platform_ops.models import (
        BackgroundJobFailure,
        BackgroundJobRegistry,
        IncidentAssignment,
        IncidentHistory,
        PlatformIncident,
        PlatformService,
        ServiceHealthSnapshot,
    )
    from app.modules.integrations.models import (
        IntegrationConfiguration,
        IntegrationConfigurationHistory,
        IntegrationHealth,
        IntegrationProvider,
        IntegrationSyncHistory,
        ProviderCredentialReference,
        WebhookDeliveryEvent,
    )
    from app.modules.data_governance.models import (
        TenantArchivalRecord,
        TenantDeletionManifest,
        TenantDeletionRequest,
        TenantExportArtifact,
        TenantExportDownload,
        TenantExportJob,
        TenantExportRequest,
        TenantLegalHold,
        TenantOffboardingRecord,
        TenantRetentionExecution,
        TenantRetentionPolicy,
    )
    from app.modules.subscriptions.models import (
        PlanEntitlement,
        SubscriptionHistory,
        SubscriptionInvoice,
        SubscriptionPayment,
        SubscriptionPlan,
        SubscriptionUsageMetric,
        SubscriptionWebhookEvent,
        TenantSubscription,
    )
    from app.modules.configuration.models import (
        ConfigurationChangeHistory,
        ConfigurationVersion,
        PlatformConfiguration,
        TenantBranding,
        TenantConfiguration,
        TenantFeatureFlags,
    )
    from app.modules.college_admin.models import (
        CollegeDashboardPreferences,
        InstitutionActivityLog,
        InstitutionBranding,
        InstitutionCampus,
        InstitutionConfigurationVersion,
        InstitutionProfile,
        InstitutionSettings,
    )
    from app.modules.college_admin.identity_models import (
        DepartmentHeadAssignment,
        DepartmentHierarchy,
        DepartmentHistory,
        DepartmentStaffAssociation,
        InstitutionAccessHistory,
        InstitutionDepartment,
        InstitutionOrganizationUnit,
        InstitutionPermission,
        InstitutionRole,
        InstitutionRoleAssignment,
        InstitutionUser,
        InstitutionUserInvitation,
    )
    from app.modules.college_admin.academic_config_models import (
        AcademicCalendar,
        AcademicConfigurationVersion,
        AcademicProgramme,
        AcademicRegulation,
        AcademicTerm,
        AcademicYear,
    )
    from app.modules.college_admin.student_admin_models import (
        StudentAdmission,
        StudentGuardianRelationship,
        StudentPromotionRecord,
        StudentRecord,
        StudentStatusHistory,
        StudentTransfer,
    )
    from app.modules.college_admin.faculty_admin_models import (
        EmployeeRecord,
        FacultyDepartmentAssignment,
        FacultyDocumentReference,
        FacultyEmploymentHistory,
        FacultyRecord,
        FacultyTeachingAssignment,
        FacultyWorkloadRecord,
    )
    from app.modules.college_admin.attendance_admin_models import (
        AttendanceComplianceSnapshot,
        AttendanceCorrectionApproval,
        AttendanceSubmissionMonitoring,
        InstitutionAttendancePolicy,
    )
    from app.modules.college_admin.examination_admin_models import (
        ExaminationApprovalRecord,
        ExaminationConfiguration,
        ExaminationEligibilityRecord,
        ExaminationMarkRecord,
        ExaminationResultPublicationRecord,
        InstitutionExaminationSchedule,
        ExaminationSessionRecord,
        HallTicketRecord,
    )
    from app.modules.college_admin.finance_admin_models import (
        FinancialApprovalRecord,
        FinancialPeriod,
        InstitutionFeeStructure,
        PaymentReconciliationRecord,
        RefundRequest,
        StudentFeeAssessment,
    )
    from app.modules.college_admin.hr_admin_models import (
        EmployeeBenefitRecord,
        EmployeeLeaveApproval,
        EmployeeLeavePolicy,
        EmployeeOffboardingRecord,
        EmployeeOnboardingRecord,
        EmployeePerformanceRecord,
        HrPolicy,
        PayrollConfiguration,
        RecruitmentRecord,
    )
    from app.modules.college_admin.library_admin_models import (
        LibraryAcquisition,
        LibraryBookCopyRecord,
        LibraryBorrowingPolicy,
        LibraryBranch,
        LibraryCatalogueEntry,
        LibraryCirculationRecord,
        LibraryInventoryHistory,
        LibraryMembershipReference,
    )
    from app.modules.academics.curriculum_models import (
        CourseLearningOutcome,
        CourseRecord,
        CourseSubjectMapping,
        CurriculumRecord,
        EnrollmentRosterEntry,
        SectionOffering,
        SubjectRecord,
        SyllabusRecord,
    )
    from app.modules.academics.models import (
        AcademicCalendarEvent,
        AcademicYearContext,
        ClassSession,
        ExaminationSchedule,
        PendingAssignmentEvaluation,
        PendingAttendanceSubmission,
        TimetableChangeLog,
        TimetableEntry,
        UpcomingAssessment,
    )
    from app.modules.hr.models import EmployeeProfileSnapshot, LeaveRequest, PayslipReference
    from app.modules.faculty.communication_models import (
        AcademicMessage,
        CommunicationRecipient,
        FacultyAnnouncement,
        FacultyNotificationDeliveryLog,
        FacultyNotificationPreferences,
    )
    from app.modules.faculty.self_service_models import (
        FacultyDocumentAccessLog,
        FacultyPersonalDocument,
        FacultyReportExport,
    )
    from app.modules.attendance.models import (
        AttendanceCorrectionRequest,
        AttendancePolicyReference,
        AttendanceRecord,
        AttendanceSession,
    )
    from app.modules.examinations.models import (
        Assessment,
        AssessmentComponent,
        FacultyAssessmentAssignment,
        GradingPolicy,
        MarksApprovalHistory,
        MarksCorrectionRequest,
        MarksSubmissionBatch,
        StudentAssessmentMark,
    )
    from app.modules.examinations.semester_examination_models import (
        ExaminationAnnouncement,
        ExaminationCentre,
        ExaminationRegulation,
        ExaminationScheduleChange,
        SemesterExaminationSeason,
        SemesterExaminationSession,
        StudentExaminationEligibility,
    )
    from app.modules.examinations.examination_registration_models import (
        ExaminationFeePayment,
        ExaminationRegistrationWindow,
    )
    from app.modules.examinations.hall_ticket_models import ExaminationHallTicket
    from app.modules.examinations.result_publication_models import (
        SemesterResultPublication,
        SemesterResultSubjectMark,
    )
    from app.modules.examinations.academic_document_models import AcademicDocumentPublication
    from app.modules.examinations.arrear_examination_models import (
        ArrearEligibilityRecord,
        ExaminationAttemptRecord,
        SupplementaryExaminationSeason,
    )
    from app.modules.examinations.exam_review_models import ExaminationReviewFeePayment, ExaminationReviewWindow
    from app.modules.faculty.support_models import (
        AcademicPerformanceSnapshot,
        FacultyAcademicReport,
        StudentAcademicFollowup,
        StudentCounsellingSession,
        StudentImprovementPlan,
        StudentMentoringRecord,
    )
    from app.modules.lms.models import (
        AssignmentEvaluation,
        AssignmentFeedback,
        AssignmentResubmissionHistory,
        AssignmentRule,
        AssignmentSubmission,
        CourseAssignment,
        LearningMaterial,
    )
    from app.modules.faculty.models import (
        ClassSessionUpdateRequest,
        CourseCoverage,
        FacultyActivityLog,
        FacultyAssignment,
        FacultyDashboardPreferences,
        FacultyNotification,
        FacultyProfile,
        FacultyTimetableNotification,
        FacultyWorkload,
    )
    from app.modules.tenants.lifecycle_models import DomainVerificationRecord, TenantLifecycleOperation
    from app.modules.students.assessment_models import (
        StudentAssessmentNotification,
        StudentAssignmentProgress,
        StudentCiaViewPreferences,
    )
    from app.modules.students.examination_portal_models import (
        StudentExaminationNotification,
        StudentExaminationPreferences,
    )
    from app.modules.students.examination_registration_models import (
        StudentExamRegistration,
        StudentExamRegistrationHistory,
        StudentExamRegistrationSubject,
        StudentHallTicketDownloadLog,
        StudentHallTicketReference,
        StudentResultNotification,
        StudentResultViewPreferences,
    )
    from app.modules.students.academic_document_models import (
        StudentAcademicDocumentRequest,
        StudentDocumentDownloadLog,
        StudentGradeCardReference,
        StudentMarksheetReference,
        StudentTranscriptReference,
    )
    from app.modules.students.arrear_backlog_models import (
        StudentArrearReference,
        StudentExamAttemptHistory,
        StudentSupplementaryRegistration,
    )
    from app.modules.students.exam_review_models import (
        StudentExamReviewPaymentReference,
        StudentExamReviewRequestHistory,
        StudentMarksCorrectionRequest,
        StudentRecheckingRequest,
        StudentRevaluationRequest,
    )
    from app.modules.finance.finance_models import (
        FeeConcession,
        FeeInstallmentSchedule,
        OfficialScholarshipApplication,
        PaymentReceipt,
        PaymentTransaction,
        RefundRecord,
        ScholarshipProgram,
        StudentFeeDemand,
        StudentFeeInvoice,
        StudentFeeStructure,
        StudentFinancialLedgerEntry,
        StudentScholarshipEligibility,
    )
    from app.modules.students.student_lms_models import (
        StudentLearningProgress,
        StudentLmsNotificationLog,
        StudentLmsPreferences,
        StudentMaterialAccessLog,
    )
    from app.modules.students.student_finance_models import (
        StudentFeeViewPreferences,
        StudentFinancialDocumentReference,
        StudentPaymentAttempt,
        StudentPaymentNotificationLog,
        StudentScholarshipApplication,
    )
    from app.modules.library.library_models import (
        LibraryCatalogItem,
        LibraryCirculation,
        LibraryCopy,
        LibraryDigitalResource,
        LibraryFine,
        LibraryReservation,
    )
    from app.modules.hostel.hostel_models import (
        HostelApplication,
        HostelNotice,
        HostelRoomAllocation,
        HostelServiceRequest,
    )
    from app.modules.transport.transport_models import (
        TransportAllocation,
        TransportNotification,
        TransportRoute,
        TransportSchedule,
        TransportServiceRequest,
        TransportStop,
    )
    from app.modules.student_services.catalog_models import InstitutionalService
    from app.modules.students.student_portal_models import (
        StudentCommunicationPreferences,
        StudentDocumentReference,
        StudentDocumentRequest,
        StudentHostelRequestReference,
        StudentLibraryActivityView,
        StudentNotificationReadStatus,
        StudentProfileCorrectionRequest,
        StudentReportDownloadLog,
        StudentReportExport,
        StudentServiceRequest,
        StudentServiceRequestHistory,
        StudentTransportRequestReference,
    )
    from app.modules.students.student_schedule_models import (
        AcademicCalendarReference,
        AttendanceNotificationRecord,
        StudentAttendanceDiscrepancyRequest,
        StudentTimetableView,
    )
    from app.modules.students.curriculum_models import (
        CourseCatalogReference,
        CoursePrerequisite,
        CourseRegistrationRequest,
        CurriculumReference,
        ElectiveGroup,
        ElectiveOption,
        RegistrationHistoryEntry,
        RegistrationPolicyReference,
        StudentCourseRegistration,
        StudentElectiveSelection,
        SubjectCatalogReference,
        SyllabusReference,
    )
    from app.modules.students.models import (
        StudentAcademicRecord,
        StudentAcademicRequest,
        StudentActivityLog,
        StudentDashboardPreferences,
        StudentEnrollment,
        StudentEnrollmentHistory,
        StudentProfile,
    )
    from app.modules.tenants.platform_models import (
        PlatformAlert,
        PlatformMetricsSnapshot,
        TenantAdminInvitation,
        TenantDomain,
        TenantOnboarding,
        TenantProvisioningJob,
        TenantStatusHistory,
    )

    return [
        User,
        RefreshToken,
        Tenant,
        Department,
        AuditLog,
        TenantOnboarding,
        TenantDomain,
        TenantAdminInvitation,
        TenantProvisioningJob,
        TenantStatusHistory,
        PlatformMetricsSnapshot,
        PlatformAlert,
        TenantLifecycleOperation,
        DomainVerificationRecord,
        PlatformConfiguration,
        TenantConfiguration,
        TenantBranding,
        TenantFeatureFlags,
        InstitutionProfile,
        InstitutionCampus,
        InstitutionSettings,
        InstitutionBranding,
        InstitutionConfigurationVersion,
        CollegeDashboardPreferences,
        InstitutionActivityLog,
        InstitutionUser,
        InstitutionRole,
        InstitutionPermission,
        InstitutionRoleAssignment,
        InstitutionUserInvitation,
        InstitutionAccessHistory,
        InstitutionOrganizationUnit,
        InstitutionDepartment,
        DepartmentHierarchy,
        DepartmentHeadAssignment,
        DepartmentStaffAssociation,
        DepartmentHistory,
        AcademicYear,
        AcademicTerm,
        AcademicCalendar,
        AcademicProgramme,
        AcademicRegulation,
        AcademicConfigurationVersion,
        StudentAdmission,
        StudentRecord,
        StudentStatusHistory,
        StudentTransfer,
        StudentPromotionRecord,
        StudentGuardianRelationship,
        EmployeeRecord,
        FacultyRecord,
        FacultyEmploymentHistory,
        FacultyDepartmentAssignment,
        FacultyTeachingAssignment,
        FacultyWorkloadRecord,
        FacultyDocumentReference,
        InstitutionAttendancePolicy,
        AttendanceSubmissionMonitoring,
        AttendanceCorrectionApproval,
        AttendanceComplianceSnapshot,
        ExaminationConfiguration,
        ExaminationSessionRecord,
        InstitutionExaminationSchedule,
        ExaminationEligibilityRecord,
        HallTicketRecord,
        ExaminationMarkRecord,
        ExaminationApprovalRecord,
        ExaminationResultPublicationRecord,
        InstitutionFeeStructure,
        StudentFeeAssessment,
        FinancialPeriod,
        PaymentReconciliationRecord,
        FinancialApprovalRecord,
        RefundRequest,
        HrPolicy,
        RecruitmentRecord,
        EmployeeOnboardingRecord,
        EmployeeOffboardingRecord,
        EmployeeLeavePolicy,
        EmployeeLeaveApproval,
        PayrollConfiguration,
        EmployeeBenefitRecord,
        EmployeePerformanceRecord,
        LibraryBranch,
        LibraryCatalogueEntry,
        LibraryBookCopyRecord,
        LibraryMembershipReference,
        LibraryBorrowingPolicy,
        LibraryCirculationRecord,
        LibraryAcquisition,
        LibraryInventoryHistory,
        ConfigurationVersion,
        ConfigurationChangeHistory,
        PlatformRoleDefinition,
        PlatformOperatorProfile,
        PlatformRoleAssignment,
        PlatformInvitation,
        PlatformSession,
        PlatformAccessReview,
        SecurityEvent,
        PlatformAuditLog,
        SupportAccessRequest,
        SupportAccessApproval,
        SupportAccessSession,
        SupportAccessActivity,
        PlatformService,
        ServiceHealthSnapshot,
        PlatformIncident,
        IncidentAssignment,
        IncidentHistory,
        BackgroundJobRegistry,
        BackgroundJobFailure,
        IntegrationProvider,
        IntegrationConfiguration,
        ProviderCredentialReference,
        IntegrationHealth,
        IntegrationSyncHistory,
        WebhookDeliveryEvent,
        IntegrationConfigurationHistory,
        TenantExportRequest,
        TenantExportJob,
        TenantExportArtifact,
        TenantExportDownload,
        TenantRetentionPolicy,
        TenantRetentionExecution,
        TenantArchivalRecord,
        TenantDeletionRequest,
        TenantDeletionManifest,
        TenantLegalHold,
        TenantOffboardingRecord,
        SubscriptionPlan,
        PlanEntitlement,
        TenantSubscription,
        SubscriptionHistory,
        SubscriptionInvoice,
        SubscriptionPayment,
        SubscriptionWebhookEvent,
        SubscriptionUsageMetric,
        FacultyProfile,
        FacultyAssignment,
        FacultyWorkload,
        FacultyDashboardPreferences,
        FacultyActivityLog,
        FacultyNotification,
        FacultyTimetableNotification,
        ClassSessionUpdateRequest,
        CourseCoverage,
        AcademicYearContext,
        TimetableEntry,
        ClassSession,
        ExaminationSchedule,
        TimetableChangeLog,
        PendingAttendanceSubmission,
        UpcomingAssessment,
        PendingAssignmentEvaluation,
        AcademicCalendarEvent,
        CourseRecord,
        SubjectRecord,
        CourseSubjectMapping,
        CurriculumRecord,
        SyllabusRecord,
        CourseLearningOutcome,
        SectionOffering,
        EnrollmentRosterEntry,
        AttendancePolicyReference,
        AttendanceSession,
        AttendanceRecord,
        AttendanceCorrectionRequest,
        LearningMaterial,
        AssignmentRule,
        CourseAssignment,
        AssignmentSubmission,
        AssignmentEvaluation,
        AssignmentFeedback,
        AssignmentResubmissionHistory,
        GradingPolicy,
        Assessment,
        AssessmentComponent,
        FacultyAssessmentAssignment,
        MarksSubmissionBatch,
        StudentAssessmentMark,
        MarksCorrectionRequest,
        MarksApprovalHistory,
        StudentMentoringRecord,
        StudentCounsellingSession,
        StudentAcademicFollowup,
        StudentImprovementPlan,
        AcademicPerformanceSnapshot,
        FacultyAcademicReport,
        FacultyAnnouncement,
        AcademicMessage,
        CommunicationRecipient,
        FacultyNotificationPreferences,
        FacultyNotificationDeliveryLog,
        FacultyPersonalDocument,
        FacultyReportExport,
        FacultyDocumentAccessLog,
        LeaveRequest,
        PayslipReference,
        EmployeeProfileSnapshot,
        StudentProfile,
        StudentAcademicRecord,
        StudentEnrollment,
        StudentEnrollmentHistory,
        StudentDashboardPreferences,
        StudentAcademicRequest,
        StudentActivityLog,
        CourseCatalogReference,
        SubjectCatalogReference,
        CurriculumReference,
        SyllabusReference,
        CoursePrerequisite,
        ElectiveGroup,
        ElectiveOption,
        RegistrationPolicyReference,
        StudentCourseRegistration,
        StudentElectiveSelection,
        CourseRegistrationRequest,
        RegistrationHistoryEntry,
        StudentTimetableView,
        AcademicCalendarReference,
        StudentAttendanceDiscrepancyRequest,
        AttendanceNotificationRecord,
        StudentCiaViewPreferences,
        StudentAssignmentProgress,
        StudentAssessmentNotification,
        ExaminationCentre,
        SemesterExaminationSeason,
        SemesterExaminationSession,
        StudentExaminationEligibility,
        ExaminationRegulation,
        ExaminationAnnouncement,
        ExaminationScheduleChange,
        StudentExaminationPreferences,
        StudentExaminationNotification,
        ExaminationRegistrationWindow,
        ExaminationFeePayment,
        ExaminationHallTicket,
        SemesterResultPublication,
        SemesterResultSubjectMark,
        StudentExamRegistration,
        StudentExamRegistrationSubject,
        StudentExamRegistrationHistory,
        StudentHallTicketReference,
        StudentHallTicketDownloadLog,
        StudentResultViewPreferences,
        StudentResultNotification,
        AcademicDocumentPublication,
        StudentMarksheetReference,
        StudentGradeCardReference,
        StudentTranscriptReference,
        StudentAcademicDocumentRequest,
        StudentDocumentDownloadLog,
        SupplementaryExaminationSeason,
        ExaminationAttemptRecord,
        ArrearEligibilityRecord,
        ExaminationReviewWindow,
        ExaminationReviewFeePayment,
        StudentArrearReference,
        StudentExamAttemptHistory,
        StudentSupplementaryRegistration,
        StudentRevaluationRequest,
        StudentRecheckingRequest,
        StudentMarksCorrectionRequest,
        StudentExamReviewRequestHistory,
        StudentExamReviewPaymentReference,
        StudentFeeStructure,
        StudentFeeDemand,
        StudentFeeInvoice,
        StudentFinancialLedgerEntry,
        PaymentTransaction,
        PaymentReceipt,
        FeeInstallmentSchedule,
        ScholarshipProgram,
        StudentScholarshipEligibility,
        OfficialScholarshipApplication,
        FeeConcession,
        RefundRecord,
        StudentLearningProgress,
        StudentMaterialAccessLog,
        StudentLmsPreferences,
        StudentLmsNotificationLog,
        StudentFeeViewPreferences,
        StudentPaymentAttempt,
        StudentScholarshipApplication,
        StudentFinancialDocumentReference,
        StudentPaymentNotificationLog,
        LibraryCatalogItem,
        LibraryCopy,
        LibraryCirculation,
        LibraryReservation,
        LibraryFine,
        LibraryDigitalResource,
        HostelApplication,
        HostelRoomAllocation,
        HostelNotice,
        HostelServiceRequest,
        TransportRoute,
        TransportStop,
        TransportSchedule,
        TransportAllocation,
        TransportServiceRequest,
        TransportNotification,
        InstitutionalService,
        StudentServiceRequest,
        StudentServiceRequestHistory,
        StudentHostelRequestReference,
        StudentTransportRequestReference,
        StudentLibraryActivityView,
        StudentCommunicationPreferences,
        StudentNotificationReadStatus,
        StudentDocumentReference,
        StudentDocumentRequest,
        StudentProfileCorrectionRequest,
        StudentReportExport,
        StudentReportDownloadLog,
    ]


async def connect_to_mongo() -> None:
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    await _client.admin.command("ping")
    await init_beanie(
        database=_client[settings.mongodb_db_name],
        document_models=document_models(),
    )
    logger.info("Connected to MongoDB database %s", settings.mongodb_db_name)


async def close_mongo() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ping_mongo() -> None:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized")
    await _client.admin.command("ping")


def get_database_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized")
    return _client
