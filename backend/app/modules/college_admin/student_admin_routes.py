"""College admin student administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.student_admin_schemas import (
    AdmissionCreate,
    AdmissionRead,
    BulkStudentImport,
    EnrollmentAssign,
    GuardianCreate,
    ProfileCorrectionDecision,
    PromotionCreate,
    StudentAcademicHistoryRead,
    StudentRecordCreate,
    StudentRecordRead,
    StudentRecordUpdate,
    StudentStatusChange,
    TransferCreate,
)
from app.modules.department_admin.phase3_schemas import SectionTransferRead, SectionTransferReview
from app.modules.department_admin.section_transfer_service import review_section_transfer
from app.modules.college_admin.all_students_list_page_service import get_all_students_list_page
from app.modules.college_admin.schemas import (
    AllStudentsListPageRead,
    NewStudentRegistrationDraftUpdate,
    NewStudentRegistrationPageRead,
    StudentAdministrationDashboardPageRead,
    StudentAcademicHistoryPageRead,
    StudentAdmissionPageRead,
    StudentDetailsPageRead,
    StudentDocumentVerificationDecisionPayload,
    StudentDocumentVerificationPageRead,
    StudentDocumentVerificationVerifyAllPayload,
    BatchSectionAllocationPageRead,
    BatchSectionAllocationRulesSubmit,
    StudentEnrollmentBulkEnrollPayload,
    StudentEnrollmentManagementPageRead,
    StudentPromotionManagementPageRead,
    StudentPromotionPromotePayload,
    StudentStatusApprovePayload,
    StudentStatusChangeSubmitPayload,
    StudentStatusManagementPageRead,
    StudentIdCardBulkPrintPayload,
    StudentIdCardIssuePayload,
    StudentIdCardManagementPageRead,
    StudentWithdrawalDiscontinuationPageRead,
    StudentWithdrawalSavePayload,
    StudentWithdrawalSubmitPayload,
    StudentTransferManagementPageRead,
    StudentTransferReviewSavePayload,
    StudentProfileManagementPageRead,
    StudentProfileManagementSavePayload,
)
from app.modules.college_admin.new_student_registration_page_service import (
    get_new_student_registration_page,
    save_new_student_registration_draft,
)
from app.modules.college_admin.student_document_verification_page_service import (
    get_student_document_verification_page,
    save_document_verification_decision,
    verify_all_student_documents,
)
from app.modules.college_admin.student_profile_management_page_service import (
    get_student_profile_management_page,
    save_student_profile_management,
)
from app.modules.college_admin.student_admission_page_service import get_student_admission_page
from app.modules.college_admin.batch_section_allocation_page_service import (
    auto_allocate_batch_section_allocation,
    confirm_batch_section_allocation,
    get_batch_section_allocation_page,
    save_batch_section_allocation_rules,
)
from app.modules.college_admin.student_enrollment_management_page_service import (
    bulk_enroll_students_for_term,
    get_student_enrollment_management_page,
)
from app.modules.college_admin.student_promotion_management_page_service import (
    get_student_promotion_management_page,
    preview_student_promotion,
    promote_eligible_students,
)
from app.modules.college_admin.student_status_management_page_service import (
    approve_student_status_change,
    get_student_status_management_page,
    submit_student_status_change,
)
from app.modules.college_admin.student_withdrawal_discontinuation_page_service import (
    cancel_student_withdrawal_draft,
    get_student_withdrawal_discontinuation_page,
    save_student_withdrawal_draft,
    submit_student_withdrawal_for_approval,
)
from app.modules.college_admin.student_id_card_management_page_service import (
    bulk_print_student_id_cards,
    get_student_id_card_management_page,
    issue_student_id_card,
)
from app.modules.college_admin.student_transfer_management_page_service import (
    get_student_transfer_management_page,
    save_student_transfer_review,
)
from app.modules.college_admin.student_details_page_service import get_student_details_page
from app.modules.college_admin.student_academic_history_page_service import get_student_academic_history_page
from app.modules.college_admin.student_administration_dashboard_page_service import (
    get_student_administration_dashboard_page,
)
from app.modules.college_admin.student_admin_service import (
    add_guardian,
    bulk_import_students,
    change_student_status,
    confirm_admission,
    create_admission,
    create_student_record,
    decide_profile_correction,
    enroll_student,
    get_student_record,
    list_admissions,
    list_student_records,
    process_promotion,
    process_transfer,
    student_academic_history,
    update_student_record,
)

router = APIRouter()


@router.get("/students/details/page", response_model=ApiResponse[StudentDetailsPageRead])
async def student_details_page_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentDetailsPageRead]:
    return success_response(
        await get_student_details_page(scope, record_id),
        request_id=get_request_id(),
    )


@router.get("/students/academic-history/page", response_model=ApiResponse[StudentAcademicHistoryPageRead])
async def student_academic_history_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    record_id: str | None = None,
) -> ApiResponse[StudentAcademicHistoryPageRead]:
    return success_response(
        await get_student_academic_history_page(scope, record_id=record_id or None),
        request_id=get_request_id(),
    )


@router.get("/students/list/page", response_model=ApiResponse[AllStudentsListPageRead])
async def all_students_list_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    search: str | None = None,
    programme_code: str | None = None,
    study_year: int | None = None,
    section_code: str | None = None,
    status_filter: str | None = None,
) -> ApiResponse[AllStudentsListPageRead]:
    return success_response(
        await get_all_students_list_page(
            scope,
            page=page,
            search=search,
            programme_code=programme_code or None,
            study_year=study_year,
            section_code=section_code or None,
            status_filter=status_filter or None,
        ),
        request_id=get_request_id(),
    )


@router.get("/students/profile-management/page", response_model=ApiResponse[StudentProfileManagementPageRead])
async def student_profile_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    record_id: str | None = None,
) -> ApiResponse[StudentProfileManagementPageRead]:
    return success_response(
        await get_student_profile_management_page(scope, record_id),
        request_id=get_request_id(),
    )


@router.get("/students/documents/verification/page", response_model=ApiResponse[StudentDocumentVerificationPageRead])
async def student_document_verification_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    record_id: str | None = None,
    document_key: str | None = None,
) -> ApiResponse[StudentDocumentVerificationPageRead]:
    return success_response(
        await get_student_document_verification_page(scope, record_id=record_id, document_key=document_key),
        request_id=get_request_id(),
    )


@router.post("/students/documents/verification/decide", response_model=ApiResponse[StudentDocumentVerificationPageRead])
async def student_document_verification_decide_route(
    payload: StudentDocumentVerificationDecisionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentDocumentVerificationPageRead]:
    return success_response(
        await save_document_verification_decision(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/students/documents/verification/verify-all", response_model=ApiResponse[StudentDocumentVerificationPageRead])
async def student_document_verification_verify_all_route(
    payload: StudentDocumentVerificationVerifyAllPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentDocumentVerificationPageRead]:
    return success_response(
        await verify_all_student_documents(scope, payload.record_id),
        request_id=get_request_id(),
    )


@router.post("/students/profile-management/save", response_model=ApiResponse[StudentProfileManagementPageRead])
async def student_profile_management_save_route(
    payload: StudentProfileManagementSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentProfileManagementPageRead]:
    return success_response(
        await save_student_profile_management(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/registrations/new/page", response_model=ApiResponse[NewStudentRegistrationPageRead])
async def new_student_registration_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    admission_id: str | None = None,
) -> ApiResponse[NewStudentRegistrationPageRead]:
    return success_response(
        await get_new_student_registration_page(scope, admission_id=admission_id),
        request_id=get_request_id(),
    )


@router.put("/registrations/new/draft", response_model=ApiResponse[NewStudentRegistrationPageRead])
async def new_student_registration_draft_route(
    payload: NewStudentRegistrationDraftUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[NewStudentRegistrationPageRead]:
    return success_response(
        await save_new_student_registration_draft(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/students/status/page", response_model=ApiResponse[StudentStatusManagementPageRead])
async def student_status_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    selected_request_id: str | None = None,
) -> ApiResponse[StudentStatusManagementPageRead]:
    return success_response(
        await get_student_status_management_page(
            scope,
            page=page,
            selected_request_id=selected_request_id or None,
        ),
        request_id=get_request_id(),
    )


@router.post("/students/status/submit", response_model=ApiResponse[StudentStatusManagementPageRead])
async def student_status_submit_route(
    payload: StudentStatusChangeSubmitPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentStatusManagementPageRead]:
    return success_response(
        await submit_student_status_change(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/students/status/approve", response_model=ApiResponse[StudentStatusManagementPageRead])
async def student_status_approve_route(
    payload: StudentStatusApprovePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentStatusManagementPageRead]:
    return success_response(
        await approve_student_status_change(scope, request_id=payload.request_id, page=payload.page),
        request_id=get_request_id(),
    )


@router.get("/students/withdrawal/page", response_model=ApiResponse[StudentWithdrawalDiscontinuationPageRead])
async def student_withdrawal_discontinuation_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    record_id: str | None = None,
    request_id: str | None = None,
) -> ApiResponse[StudentWithdrawalDiscontinuationPageRead]:
    return success_response(
        await get_student_withdrawal_discontinuation_page(
            scope,
            record_id=record_id or None,
            request_id=request_id or None,
        ),
        request_id=get_request_id(),
    )


@router.post("/students/withdrawal/save", response_model=ApiResponse[StudentWithdrawalDiscontinuationPageRead])
async def student_withdrawal_save_route(
    payload: StudentWithdrawalSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentWithdrawalDiscontinuationPageRead]:
    return success_response(
        await save_student_withdrawal_draft(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/students/withdrawal/submit", response_model=ApiResponse[StudentWithdrawalDiscontinuationPageRead])
async def student_withdrawal_submit_route(
    payload: StudentWithdrawalSubmitPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentWithdrawalDiscontinuationPageRead]:
    return success_response(
        await submit_student_withdrawal_for_approval(scope, payload),
        request_id=get_request_id(),
    )


@router.delete("/students/withdrawal/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def student_withdrawal_cancel_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> None:
    await cancel_student_withdrawal_draft(scope, request_id=request_id)


@router.get("/students/id-cards/page", response_model=ApiResponse[StudentIdCardManagementPageRead])
async def student_id_card_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
) -> ApiResponse[StudentIdCardManagementPageRead]:
    return success_response(
        await get_student_id_card_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.post("/students/id-cards/issue", response_model=ApiResponse[StudentIdCardManagementPageRead])
async def student_id_card_issue_route(
    payload: StudentIdCardIssuePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentIdCardManagementPageRead]:
    return success_response(
        await issue_student_id_card(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/students/id-cards/bulk-print", response_model=ApiResponse[StudentIdCardManagementPageRead])
async def student_id_card_bulk_print_route(
    payload: StudentIdCardBulkPrintPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentIdCardManagementPageRead]:
    return success_response(
        await bulk_print_student_id_cards(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/students/promotion/page", response_model=ApiResponse[StudentPromotionManagementPageRead])
async def student_promotion_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    transition_key: str | None = None,
    programme_code: str | None = None,
) -> ApiResponse[StudentPromotionManagementPageRead]:
    return success_response(
        await get_student_promotion_management_page(
            scope,
            transition_key=transition_key or None,
            programme_code=programme_code or None,
        ),
        request_id=get_request_id(),
    )


@router.post("/students/promotion/preview", response_model=ApiResponse[StudentPromotionManagementPageRead])
async def student_promotion_preview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    transition_key: str | None = None,
    programme_code: str | None = None,
) -> ApiResponse[StudentPromotionManagementPageRead]:
    return success_response(
        await preview_student_promotion(
            scope,
            transition_key=transition_key or None,
            programme_code=programme_code or None,
        ),
        request_id=get_request_id(),
    )


@router.post("/students/promotion/promote-eligible", response_model=ApiResponse[StudentPromotionManagementPageRead])
async def student_promotion_promote_route(
    payload: StudentPromotionPromotePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentPromotionManagementPageRead]:
    return success_response(
        await promote_eligible_students(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/students/transfers/page", response_model=ApiResponse[StudentTransferManagementPageRead])
async def student_transfer_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    selected_request_key: str | None = None,
) -> ApiResponse[StudentTransferManagementPageRead]:
    return success_response(
        await get_student_transfer_management_page(
            scope,
            page=page,
            selected_request_key=selected_request_key or None,
        ),
        request_id=get_request_id(),
    )


@router.post("/students/transfers/review", response_model=ApiResponse[StudentTransferManagementPageRead])
async def student_transfer_review_route(
    payload: StudentTransferReviewSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentTransferManagementPageRead]:
    return success_response(
        await save_student_transfer_review(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/students/batch-section-allocation/page", response_model=ApiResponse[BatchSectionAllocationPageRead])
async def batch_section_allocation_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    section_page: int = 1,
    unallocated_page: int = 1,
) -> ApiResponse[BatchSectionAllocationPageRead]:
    return success_response(
        await get_batch_section_allocation_page(
            scope,
            section_page=section_page,
            unallocated_page=unallocated_page,
        ),
        request_id=get_request_id(),
    )


@router.post("/students/batch-section-allocation/auto-allocate", response_model=ApiResponse[BatchSectionAllocationPageRead])
async def batch_section_allocation_auto_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    section_page: int = 1,
    unallocated_page: int = 1,
) -> ApiResponse[BatchSectionAllocationPageRead]:
    return success_response(
        await auto_allocate_batch_section_allocation(
            scope,
            section_page=section_page,
            unallocated_page=unallocated_page,
        ),
        request_id=get_request_id(),
    )


@router.post("/students/batch-section-allocation/confirm", response_model=ApiResponse[BatchSectionAllocationPageRead])
async def batch_section_allocation_confirm_route(
    payload: BatchSectionAllocationRulesSubmit,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[BatchSectionAllocationPageRead]:
    return success_response(
        await confirm_batch_section_allocation(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/students/batch-section-allocation/rules", response_model=ApiResponse[BatchSectionAllocationPageRead])
async def batch_section_allocation_rules_route(
    payload: BatchSectionAllocationRulesSubmit,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[BatchSectionAllocationPageRead]:
    return success_response(
        await save_batch_section_allocation_rules(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/students/enrollment/page", response_model=ApiResponse[StudentEnrollmentManagementPageRead])
async def student_enrollment_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    term_key: str | None = None,
    programme_code: str | None = None,
) -> ApiResponse[StudentEnrollmentManagementPageRead]:
    return success_response(
        await get_student_enrollment_management_page(
            scope,
            page=page,
            term_key=term_key or None,
            programme_code=programme_code or None,
        ),
        request_id=get_request_id(),
    )


@router.post("/students/enrollment/enroll-selected", response_model=ApiResponse[StudentEnrollmentManagementPageRead])
async def student_enrollment_bulk_route(
    payload: StudentEnrollmentBulkEnrollPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentEnrollmentManagementPageRead]:
    return success_response(
        await bulk_enroll_students_for_term(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/admissions/page", response_model=ApiResponse[StudentAdmissionPageRead])
async def student_admission_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    academic_year_code: str | None = None,
    programme_code: str | None = None,
    quota_filter: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
) -> ApiResponse[StudentAdmissionPageRead]:
    return success_response(
        await get_student_admission_page(
            scope,
            page=page,
            academic_year_code=academic_year_code or None,
            programme_code=programme_code or None,
            quota_filter=quota_filter or None,
            status_filter=status_filter or None,
            search=search or None,
        ),
        request_id=get_request_id(),
    )


@router.get("/dashboard/page", response_model=ApiResponse[StudentAdministrationDashboardPageRead])
async def student_administration_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_code: str | None = None,
    programme_code: str | None = None,
    study_year: int | None = None,
) -> ApiResponse[StudentAdministrationDashboardPageRead]:
    return success_response(
        await get_student_administration_dashboard_page(
            scope,
            academic_year_code=academic_year_code,
            programme_code=programme_code or None,
            study_year=study_year,
        ),
        request_id=get_request_id(),
    )


@router.post("/admissions", response_model=ApiResponse[AdmissionRead], status_code=status.HTTP_201_CREATED)
async def create_admission_route(
    payload: AdmissionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AdmissionRead]:
    return success_response(await create_admission(scope, payload), request_id=get_request_id())


@router.get("/admissions", response_model=ApiResponse[Page[AdmissionRead]])
async def list_admissions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AdmissionRead]]:
    return success_response(await list_admissions(scope, pagination), request_id=get_request_id())


@router.post("/admissions/{admission_id}/confirm", response_model=ApiResponse[AdmissionRead])
async def confirm_admission_route(
    admission_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AdmissionRead]:
    return success_response(await confirm_admission(scope, to_object_id(admission_id, "admission id")), request_id=get_request_id())


@router.post("/students", response_model=ApiResponse[StudentRecordRead], status_code=status.HTTP_201_CREATED)
async def create_student_route(
    payload: StudentRecordCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentRecordRead]:
    return success_response(await create_student_record(scope, payload), request_id=get_request_id())


@router.get("/students", response_model=ApiResponse[Page[StudentRecordRead]])
async def list_students_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[StudentRecordRead]]:
    return success_response(await list_student_records(scope, pagination), request_id=get_request_id())


@router.get("/students/{record_id}", response_model=ApiResponse[StudentRecordRead])
async def get_student_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentRecordRead]:
    return success_response(await get_student_record(scope, to_object_id(record_id, "record id")), request_id=get_request_id())


@router.patch("/students/{record_id}", response_model=ApiResponse[StudentRecordRead])
async def update_student_route(
    record_id: str,
    payload: StudentRecordUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentRecordRead]:
    return success_response(await update_student_record(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/status", response_model=ApiResponse[StudentRecordRead])
async def status_change_route(
    record_id: str,
    payload: StudentStatusChange,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentRecordRead]:
    return success_response(await change_student_status(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/enrollments", response_model=ApiResponse[dict])
async def enroll_route(
    record_id: str,
    payload: EnrollmentAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await enroll_student(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/transfer", response_model=ApiResponse[dict])
async def transfer_route(
    record_id: str,
    payload: TransferCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await process_transfer(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/promotion", response_model=ApiResponse[dict])
async def promotion_route(
    record_id: str,
    payload: PromotionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await process_promotion(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/guardians", response_model=ApiResponse[dict])
async def guardian_route(
    record_id: str,
    payload: GuardianCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await add_guardian(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.get("/students/{record_id}/academic-history", response_model=ApiResponse[StudentAcademicHistoryRead])
async def academic_history_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentAcademicHistoryRead]:
    return success_response(await student_academic_history(scope, to_object_id(record_id, "record id")), request_id=get_request_id())


@router.post("/students/bulk", response_model=ApiResponse[list[StudentRecordRead]])
async def bulk_import_route(
    payload: BulkStudentImport,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[StudentRecordRead]]:
    return success_response(await bulk_import_students(scope, payload), request_id=get_request_id())


@router.post("/profile-corrections/decide", response_model=ApiResponse[dict])
async def profile_correction_route(
    payload: ProfileCorrectionDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await decide_profile_correction(scope, payload), request_id=get_request_id())


@router.post("/section-transfer-requests/{request_id}/review", response_model=ApiResponse[SectionTransferRead])
async def college_section_transfer_review_route(
    request_id: str,
    payload: SectionTransferReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SectionTransferRead]:
    data = await review_section_transfer(scope, user, request_id, payload)
    return success_response(data, request_id=get_request_id())
