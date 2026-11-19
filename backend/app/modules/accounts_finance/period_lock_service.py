"""Financial period lock checks for backdated and closed-period mutations."""

from datetime import date

from beanie.odm.operators.find.comparison import Eq

from app.core.exceptions import AppError
from app.modules.college_admin.finance_admin_models import FinancialPeriod, FinancialPeriodStatus
from app.modules.accounts_finance.phase8_enums import PeriodLifecycleStatus


async def assert_period_open_for_date(tenant_id, on_date: date | None = None) -> None:
    when = on_date or date.today()
    periods = await FinancialPeriod.find(Eq(FinancialPeriod.tenant_id, tenant_id)).to_list()
    for period in periods:
        if period.start_date <= when <= period.end_date:
            if period.locked or period.lifecycle_status in (
                PeriodLifecycleStatus.CLOSED.value,
                PeriodLifecycleStatus.LOCKED.value,
                PeriodLifecycleStatus.ARCHIVED.value,
            ):
                raise AppError(
                    code="PERIOD_LOCKED",
                    message=f"Financial period {period.period_code} is closed or locked",
                    status_code=409,
                )
            if period.status == FinancialPeriodStatus.CLOSED:
                raise AppError(
                    code="PERIOD_CLOSED",
                    message=f"Financial period {period.period_code} is closed",
                    status_code=409,
                )