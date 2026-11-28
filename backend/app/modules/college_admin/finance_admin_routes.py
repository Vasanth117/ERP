"""College admin finance administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.finance_admin_schemas import (
    ConcessionCreate,
    FeeAssessmentBulkAssign,
    FeeAssessmentCreate,
    FeeAssessmentGroupAssign,
    FeeStructureRead,
    FeeStructureUpsert,
    FinancialPeriodUpsert,
    OfflineCollectionCreate,
    ReconciliationConfirm,
    RefundDecision,
)
from app.modules.college_admin.finance_admin_service import (
    approve_concession,
    create_concession,
    assign_fee_assessments_bulk,
    assign_fee_assessments_group,
    create_fee_assessment,
    decide_refund,
    finance_report,
    list_transactions,
    publish_fee_structure,
    reconcile_payment,
    record_offline_collection,
    request_refund,
    student_ledger,
    upsert_fee_structure,
    upsert_financial_period,
)
from app.modules.college_admin.fee_structure_management_page_service import get_fee_structure_management_page
from app.modules.college_admin.fee_demand_invoice_management_page_service import (
    get_fee_demand_invoice_management_page,
)
from app.modules.college_admin.student_fee_assign_page_service import get_student_fee_assign_page
from app.modules.college_admin.student_fee_management_page_service import get_student_fee_management_page
from app.modules.college_admin.fee_structure_creation_page_service import get_fee_structure_creation_page
from app.modules.college_admin.finance_dashboard_page_service import export_finance_dashboard_csv, get_finance_dashboard_page
from app.modules.college_admin.finance_payments_pages_service import (
    get_offline_payment_collection_page,
    get_online_payment_monitoring_page,
    get_payment_transactions_page,
    verify_pending_online_payments,
)
from app.modules.college_admin.finance_aid_pages_service import (
    get_concession_waiver_management_page,
    get_refund_management_page,
    get_scholarship_management_page,
)
from app.modules.college_admin.finance_reconciliation_reports_pages_service import (
    get_financial_reports_page,
    get_payment_reconciliation_page,
)
from app.modules.college_admin.finance_settings_page_service import (
    get_finance_settings_page,
    save_finance_settings_page,
)
from app.modules.college_admin.finance_receipts_dues_pages_service import (
    get_outstanding_dues_management_page,
    get_receipt_management_page,
)
from app.modules.college_admin.schemas import (
    FeeStructureCreationPageRead,
    FeeStructureManagementPageRead,
    FinanceDashboardPageRead,
    FeeDemandInvoiceManagementPageRead,
    FinanceSettingsPageRead,
    FinanceSettingsSave,
    OfflinePaymentCollectionPageRead,
    OnlinePaymentMonitoringPageRead,
    ConcessionWaiverManagementPageRead,
    FinancialReportsPageRead,
    OutstandingDuesManagementPageRead,
    PaymentReconciliationPageRead,
    PaymentTransactionsPageRead,
    ReceiptManagementPageRead,
    RefundManagementPageRead,
    ScholarshipManagementPageRead,
    StudentFeeAssignPageRead,
    StudentFeeManagementPageRead,
)

router = APIRouter()


@router.get("/invoices/page", response_model=ApiResponse[FeeDemandInvoiceManagementPageRead])
async def fee_demand_invoice_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[FeeDemandInvoiceManagementPageRead]:
    return success_response(
        await get_fee_demand_invoice_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/assessments/assign/page", response_model=ApiResponse[StudentFeeAssignPageRead])
async def student_fee_assign_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentFeeAssignPageRead]:
    return success_response(await get_student_fee_assign_page(scope), request_id=get_request_id())


@router.get("/assessments/page", response_model=ApiResponse[StudentFeeManagementPageRead])
async def student_fee_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[StudentFeeManagementPageRead]:
    return success_response(
        await get_student_fee_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/fee-structures/create/page", response_model=ApiResponse[FeeStructureCreationPageRead])
async def fee_structure_creation_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    return success_response(await get_fee_structure_creation_page(scope), request_id=get_request_id())


@router.get("/fee-structures/page", response_model=ApiResponse[FeeStructureManagementPageRead])
async def fee_structure_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[FeeStructureManagementPageRead]:
    return success_response(
        await get_fee_structure_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/settings/page", response_model=ApiResponse[FinanceSettingsPageRead])
async def finance_settings_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FinanceSettingsPageRead]:
    return success_response(await get_finance_settings_page(scope), request_id=get_request_id())


@router.put("/settings/page", response_model=ApiResponse[FinanceSettingsPageRead])
async def finance_settings_page_save_route(
    payload: FinanceSettingsSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FinanceSettingsPageRead]:
    return success_response(await save_finance_settings_page(scope, payload), request_id=get_request_id())


@router.get("/reconciliation/page", response_model=ApiResponse[PaymentReconciliationPageRead])
async def payment_reconciliation_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[PaymentReconciliationPageRead]:
    return success_response(
        await get_payment_reconciliation_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/reports/financial/page", response_model=ApiResponse[FinancialReportsPageRead])
async def financial_reports_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[FinancialReportsPageRead]:
    return success_response(
        await get_financial_reports_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/aid/scholarships/page", response_model=ApiResponse[ScholarshipManagementPageRead])
async def scholarship_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[ScholarshipManagementPageRead]:
    return success_response(
        await get_scholarship_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/aid/concessions/page", response_model=ApiResponse[ConcessionWaiverManagementPageRead])
async def concession_waiver_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[ConcessionWaiverManagementPageRead]:
    return success_response(
        await get_concession_waiver_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/aid/refunds/page", response_model=ApiResponse[RefundManagementPageRead])
async def refund_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[RefundManagementPageRead]:
    return success_response(
        await get_refund_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/receipts/page", response_model=ApiResponse[ReceiptManagementPageRead])
async def receipt_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[ReceiptManagementPageRead]:
    return success_response(
        await get_receipt_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/dues/outstanding/page", response_model=ApiResponse[OutstandingDuesManagementPageRead])
async def outstanding_dues_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[OutstandingDuesManagementPageRead]:
    return success_response(
        await get_outstanding_dues_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/payments/online/page", response_model=ApiResponse[OnlinePaymentMonitoringPageRead])
async def online_payment_monitoring_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[OnlinePaymentMonitoringPageRead]:
    return success_response(
        await get_online_payment_monitoring_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.post("/payments/online/verify-pending", response_model=ApiResponse[dict])
async def verify_pending_online_payments_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await verify_pending_online_payments(scope), request_id=get_request_id())


@router.get("/payments/offline/page", response_model=ApiResponse[OfflinePaymentCollectionPageRead])
async def offline_payment_collection_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[OfflinePaymentCollectionPageRead]:
    return success_response(
        await get_offline_payment_collection_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/payments/transactions/page", response_model=ApiResponse[PaymentTransactionsPageRead])
async def payment_transactions_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    search: Annotated[str | None, Query()] = None,
    month: Annotated[str | None, Query()] = None,
    method: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> ApiResponse[PaymentTransactionsPageRead]:
    return success_response(
        await get_payment_transactions_page(
            scope,
            page=page,
            search=search,
            month=month,
            method=method,
            status=status,
        ),
        request_id=get_request_id(),
    )


@router.get("/dashboard/export")
async def finance_dashboard_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_code: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
):
    return PlainTextResponse(
        content=await export_finance_dashboard_csv(
            scope,
            academic_year_code=academic_year_code,
            programme_code=programme_code,
        ),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="finance-dashboard.csv"'},
    )


@router.get("/dashboard/page", response_model=ApiResponse[FinanceDashboardPageRead])
async def finance_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    academic_year_code: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[FinanceDashboardPageRead]:
    return success_response(
        await get_finance_dashboard_page(
            scope,
            page=page,
            academic_year_code=academic_year_code,
            programme_code=programme_code,
        ),
        request_id=get_request_id(),
    )


@router.put("/fee-structures", response_model=ApiResponse[FeeStructureRead])
async def fee_structure_route(
    payload: FeeStructureUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FeeStructureRead]:
    return success_response(await upsert_fee_structure(scope, payload), request_id=get_request_id())


@router.post("/fee-structures/{structure_id}/publish", response_model=ApiResponse[FeeStructureRead])
async def publish_structure_route(
    structure_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FeeStructureRead]:
    return success_response(await publish_fee_structure(scope, structure_id), request_id=get_request_id())


@router.post("/assessments", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def assessment_route(
    payload: FeeAssessmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_fee_assessment(scope, payload), request_id=get_request_id())


@router.post("/assessments/assign/group", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def assessment_group_assign_route(
    payload: FeeAssessmentGroupAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await assign_fee_assessments_group(scope, payload), request_id=get_request_id())


@router.post("/assessments/assign/bulk", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def assessment_bulk_assign_route(
    payload: FeeAssessmentBulkAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await assign_fee_assessments_bulk(scope, payload), request_id=get_request_id())


@router.post("/collections/offline", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def offline_collection_route(
    payload: OfflineCollectionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await record_offline_collection(scope, payload), request_id=get_request_id())


@router.get("/transactions", response_model=ApiResponse[Page[dict]])
async def transactions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await list_transactions(scope, pagination), request_id=get_request_id())


@router.post("/reconciliation", response_model=ApiResponse[dict])
async def reconciliation_route(
    payload: ReconciliationConfirm,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await reconcile_payment(scope, payload), request_id=get_request_id())


@router.get("/ledger/{student_user_id}", response_model=ApiResponse[Page[dict]])
async def ledger_route(
    student_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await student_ledger(scope, student_user_id, pagination), request_id=get_request_id())


@router.post("/concessions", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def concession_route(
    payload: ConcessionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_concession(scope, payload), request_id=get_request_id())


@router.post("/concessions/{concession_id}/approve", response_model=ApiResponse[dict])
async def approve_concession_route(
    concession_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await approve_concession(scope, concession_id), request_id=get_request_id())


@router.post("/refunds", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def refund_request_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    student_user_id: Annotated[str, Query()],
    transaction_id: Annotated[str, Query()],
    amount: Annotated[float, Query(ge=0)],
) -> ApiResponse[dict]:
    return success_response(await request_refund(scope, student_user_id, transaction_id, amount), request_id=get_request_id())


@router.post("/refunds/decide", response_model=ApiResponse[dict])
async def refund_decide_route(
    payload: RefundDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await decide_refund(scope, payload), request_id=get_request_id())


@router.put("/periods", response_model=ApiResponse[dict])
async def financial_period_route(
    payload: FinancialPeriodUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_financial_period(scope, payload), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[dict])
async def finance_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await finance_report(scope), request_id=get_request_id())
