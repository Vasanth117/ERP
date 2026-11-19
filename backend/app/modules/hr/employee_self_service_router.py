"""Employee HR self-service routes (own data only)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.attendance_schedule_schemas import AttendanceCorrectionCreate
from app.modules.hr.deps import employee_self_user
from app.modules.hr.employee_profile_schemas import ProfileCorrectionSubmit
from app.modules.hr.employee_self_service_schemas import (
    SelfServiceLeaveApply,
    SelfServiceNotificationRead,
    SelfServiceProfileRead,
    SelfServiceRequestCreate,
    SelfServiceRequestRead,
    SelfServiceSalaryRead,
)
from app.modules.hr.employee_self_service_service import (
    get_my_profile,
    list_self_service_requests,
    my_apply_leave,
    my_attendance_correction,
    my_attendance_day,
    my_attendance_monthly,
    my_benefits,
    my_documents,
    my_employment_info,
    my_leave_balances,
    my_leave_requests,
    my_notifications,
    my_onboarding,
    my_payroll_documents,
    my_payslip_detail,
    my_payslips,
    my_salary,
    my_tax_declaration_save,
    my_tax_declaration_submit,
    my_tax_declarations,
    request_profile_correction,
    submit_self_service_request,
)
from app.modules.hr.statutory_tax_schemas import TaxDeclarationRead, TaxDeclarationUpsert

router = APIRouter(prefix="/self-service", tags=["hr-employee-self-service"])


@router.get("/profile", response_model=ApiResponse[SelfServiceProfileRead])
async def profile_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await get_my_profile(scope, user), request_id=get_request_id())


@router.post("/profile/corrections", response_model=ApiResponse)
async def profile_correction_route(payload: ProfileCorrectionSubmit, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await request_profile_correction(scope, user, payload), request_id=get_request_id())


@router.get("/documents", response_model=ApiResponse)
async def documents_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_documents(scope, user), request_id=get_request_id())


@router.get("/attendance", response_model=ApiResponse)
async def attendance_route(start: date, end: date, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_attendance_day(scope, user, start, end), request_id=get_request_id())


@router.get("/attendance/monthly", response_model=ApiResponse)
async def attendance_monthly_route(year: int, month: int, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_attendance_monthly(scope, user, year, month), request_id=get_request_id())


@router.post("/attendance/corrections", response_model=ApiResponse)
async def attendance_correction_route(payload: AttendanceCorrectionCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_attendance_correction(scope, user, payload), request_id=get_request_id())


@router.get("/leave/balances", response_model=ApiResponse)
async def leave_balances_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)], year: int | None = None):
    return success_response(await my_leave_balances(scope, user, year), request_id=get_request_id())


@router.post("/leave/applications", response_model=ApiResponse)
async def leave_apply_route(payload: SelfServiceLeaveApply, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_apply_leave(scope, user, payload), request_id=get_request_id())


@router.get("/leave/applications", response_model=ApiResponse)
async def leave_list_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_leave_requests(scope, user), request_id=get_request_id())


@router.get("/salary", response_model=ApiResponse[SelfServiceSalaryRead])
async def salary_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_salary(scope, user), request_id=get_request_id())


@router.get("/payslips", response_model=ApiResponse)
async def payslips_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_payslips(scope, user), request_id=get_request_id())


@router.get("/payslips/{payslip_id}", response_model=ApiResponse)
async def payslip_detail_route(payslip_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_payslip_detail(scope, user, payslip_id), request_id=get_request_id())


@router.get("/payroll-documents", response_model=ApiResponse)
async def payroll_documents_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_payroll_documents(scope, user), request_id=get_request_id())


@router.get("/tax/declarations", response_model=ApiResponse[list[TaxDeclarationRead]])
async def tax_declarations_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_tax_declarations(scope, user), request_id=get_request_id())


@router.post("/tax/declarations/draft", response_model=ApiResponse[TaxDeclarationRead])
async def tax_declaration_draft_route(payload: TaxDeclarationUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_tax_declaration_save(scope, user, payload), request_id=get_request_id())


@router.post("/tax/declarations/{declaration_id}/submit", response_model=ApiResponse[TaxDeclarationRead])
async def tax_declaration_submit_route(declaration_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_tax_declaration_submit(scope, user, declaration_id), request_id=get_request_id())


@router.post("/requests", response_model=ApiResponse[SelfServiceRequestRead])
async def create_request_route(payload: SelfServiceRequestCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await submit_self_service_request(scope, user, payload), request_id=get_request_id())


@router.get("/requests", response_model=ApiResponse[list[SelfServiceRequestRead]])
async def list_requests_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await list_self_service_requests(scope, user), request_id=get_request_id())


@router.get("/employment", response_model=ApiResponse)
async def employment_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_employment_info(scope, user), request_id=get_request_id())


@router.get("/onboarding", response_model=ApiResponse)
async def onboarding_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_onboarding(scope, user), request_id=get_request_id())


@router.get("/benefits", response_model=ApiResponse)
async def benefits_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    return success_response(await my_benefits(scope, user), request_id=get_request_id())


@router.get("/notifications", response_model=ApiResponse[list[SelfServiceNotificationRead]])
async def notifications_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)], limit: int = 50):
    return success_response(await my_notifications(scope, user, limit), request_id=get_request_id())