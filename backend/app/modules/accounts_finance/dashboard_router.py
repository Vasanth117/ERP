"""Finance dashboard routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.dashboard_schemas import FinanceDashboardOverview
from app.modules.accounts_finance.dashboard_service import get_finance_dashboard
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.auth.models import User

router = APIRouter(prefix="/dashboard", tags=["accounts-finance-dashboard"])


@router.get("", response_model=ApiResponse[FinanceDashboardOverview])
async def finance_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    financial_year: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    fee_category_code: Annotated[str | None, Query()] = None,
    invoice_status: Annotated[str | None, Query()] = None,
    payment_status: Annotated[str | None, Query()] = None,
    payment_method: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> ApiResponse[FinanceDashboardOverview]:
    return success_response(
        await get_finance_dashboard(
            scope,
            financial_year=financial_year,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
            programme_code=programme_code,
            department_id=department_id,
            fee_category_code=fee_category_code,
            invoice_status=invoice_status,
            payment_status=payment_status,
            payment_method=payment_method,
            campus_id=campus_id,
            date_from=date_from,
            date_to=date_to,
        ),
        request_id=get_request_id(),
    )