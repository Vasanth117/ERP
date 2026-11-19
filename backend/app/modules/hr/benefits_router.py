"""Benefits and claims routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.benefits_schemas import (
    BenefitClaimCreate,
    BenefitClaimPaymentConfirm,
    BenefitClaimRead,
    BenefitClaimReview,
    BenefitEnrollmentCreate,
    BenefitEnrollmentRead,
    BenefitEnrollmentReview,
    BenefitEligibilityRead,
    BenefitProgramRead,
    BenefitProgramUpsert,
    BenefitsDashboard,
    BenefitsReports,
)
from app.modules.hr.benefits_service import (
    benefits_dashboard,
    benefits_reports,
    check_eligibility,
    confirm_claim_payment,
    create_claim,
    create_enrollment,
    list_benefit_programs,
    list_claims,
    review_claim,
    review_enrollment,
    submit_claim_for_payment,
    upsert_benefit_program,
)
from app.modules.hr.deps import employee_self_user, hr_staff_user

router = APIRouter(prefix="/benefits", tags=["hr-benefits"])


@router.get("/dashboard", response_model=ApiResponse[BenefitsDashboard])
async def dashboard_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await benefits_dashboard(scope), request_id=get_request_id())


@router.post("/programs", response_model=ApiResponse[BenefitProgramRead])
async def upsert_program_route(payload: BenefitProgramUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_benefit_program(scope, payload), request_id=get_request_id())


@router.get("/programs", response_model=ApiResponse[list[BenefitProgramRead]])
async def list_programs_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_benefit_programs(scope), request_id=get_request_id())


@router.get("/programs/{program_id}/eligibility", response_model=ApiResponse[BenefitEligibilityRead])
async def eligibility_route(program_id: str, employee_user_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)]):
    return success_response(await check_eligibility(scope, program_id, employee_user_id), request_id=get_request_id())


@router.post("/enrollments", response_model=ApiResponse[BenefitEnrollmentRead])
async def hr_enroll_route(payload: BenefitEnrollmentCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_enrollment(scope, payload, self_service=False), request_id=get_request_id())


@router.post("/enrollments/{enrollment_id}/review", response_model=ApiResponse[BenefitEnrollmentRead])
async def review_enrollment_route(enrollment_id: str, payload: BenefitEnrollmentReview, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await review_enrollment(scope, enrollment_id, payload), request_id=get_request_id())


@router.post("/claims", response_model=ApiResponse[BenefitClaimRead])
async def hr_claim_route(payload: BenefitClaimCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_claim(scope, payload, self_service=False), request_id=get_request_id())


@router.post("/claims/{claim_id}/review", response_model=ApiResponse[BenefitClaimRead])
async def review_claim_route(claim_id: str, payload: BenefitClaimReview, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await review_claim(scope, claim_id, payload), request_id=get_request_id())


@router.post("/claims/{claim_id}/submit-payment", response_model=ApiResponse)
async def submit_payment_route(claim_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await submit_claim_for_payment(scope, claim_id), request_id=get_request_id())


@router.post("/claims/{claim_id}/confirm-payment", response_model=ApiResponse[BenefitClaimRead])
async def confirm_payment_route(claim_id: str, payload: BenefitClaimPaymentConfirm, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await confirm_claim_payment(scope, claim_id, payload), request_id=get_request_id())


@router.get("/claims", response_model=ApiResponse[list[BenefitClaimRead]])
async def list_claims_route(scope: Annotated[AccessScope, Depends(get_access_scope)], employee_user_id: str | None = None, _: Annotated[User, Depends(hr_staff_user)] = None):
    return success_response(await list_claims(scope, employee_user_id), request_id=get_request_id())


@router.get("/reports", response_model=ApiResponse[BenefitsReports])
async def reports_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await benefits_reports(scope), request_id=get_request_id())


@router.post("/self/enrollments", response_model=ApiResponse[BenefitEnrollmentRead])
async def self_enroll_route(payload: BenefitEnrollmentCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    payload.employee_user_id = str(user.id)
    return success_response(await create_enrollment(scope, payload, self_service=True), request_id=get_request_id())


@router.post("/self/claims", response_model=ApiResponse[BenefitClaimRead])
async def self_claim_route(payload: BenefitClaimCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    payload.employee_user_id = str(user.id)
    return success_response(await create_claim(scope, payload, self_service=True), request_id=get_request_id())