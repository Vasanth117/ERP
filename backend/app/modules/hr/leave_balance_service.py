"""Leave balance mutations with transaction audit."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.hr.leave_models import HrLeaveBalance, HrLeaveBalanceTransaction


async def get_or_create_balance(
    tenant_id: PydanticObjectId,
    employee_user_id: PydanticObjectId,
    leave_type: str,
    period_year: int,
    *,
    annual_entitlement: float = 0,
) -> HrLeaveBalance:
    row = await HrLeaveBalance.find_one(
        Eq(HrLeaveBalance.tenant_id, tenant_id),
        Eq(HrLeaveBalance.employee_user_id, employee_user_id),
        Eq(HrLeaveBalance.leave_type, leave_type),
        Eq(HrLeaveBalance.period_year, period_year),
    )
    if row:
        return row
    row = HrLeaveBalance(
        tenant_id=tenant_id,
        employee_user_id=employee_user_id,
        leave_type=leave_type,
        period_year=period_year,
        annual_entitlement=annual_entitlement,
        available=annual_entitlement,
    )
    await row.insert()
    return row


async def post_balance_transaction(
    *,
    tenant_id: PydanticObjectId,
    employee_user_id: PydanticObjectId,
    leave_type: str,
    period_year: int,
    transaction_type: str,
    amount_days: float,
    reason: str,
    actor_id: PydanticObjectId | None,
    reference_type: str | None = None,
    reference_id: str | None = None,
) -> HrLeaveBalance:
    bal = await get_or_create_balance(tenant_id, employee_user_id, leave_type, period_year)
    before = bal.available
    bal.available = round(bal.available + amount_days, 2)
    if transaction_type == "usage":
        bal.used = round(bal.used + abs(amount_days), 2)
    elif transaction_type == "pending_reserve":
        bal.pending = round(bal.pending + abs(amount_days), 2)
    elif transaction_type == "pending_release":
        bal.pending = round(max(0, bal.pending - abs(amount_days)), 2)
    elif transaction_type == "credit":
        bal.accrued = round(bal.accrued + amount_days, 2)
    bal.updated_at = utcnow()
    await bal.save()
    await HrLeaveBalanceTransaction(
        tenant_id=tenant_id,
        employee_user_id=employee_user_id,
        leave_type=leave_type,
        period_year=period_year,
        transaction_type=transaction_type,
        amount_days=amount_days,
        balance_before=before,
        balance_after=bal.available,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason,
        actor_id=actor_id,
    ).insert()
    return bal