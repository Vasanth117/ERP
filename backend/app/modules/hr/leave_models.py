"""Leave configuration, balances, and audit."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HrLeaveTypeConfig(Document):
    tenant_id: PydanticObjectId
    leave_type_code: str = Field(max_length=64)
    title: str = Field(max_length=120)
    rules: dict[str, Any] = Field(default_factory=dict)
    employee_categories: list[str] = Field(default_factory=list)
    is_active: bool = True
    effective_from: date | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_leave_type_configs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("leave_type_code", ASCENDING)],
                unique=True,
                name="unique_leave_type_code",
            ),
        ]


class HrLeaveBalance(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    leave_type: str = Field(max_length=64)
    period_year: int
    opening_balance: float = 0
    annual_entitlement: float = 0
    accrued: float = 0
    used: float = 0
    pending: float = 0
    carry_forward: float = 0
    expired: float = 0
    available: float = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_leave_balances"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("leave_type", ASCENDING), ("period_year", ASCENDING)],
                unique=True,
                name="unique_leave_balance",
            ),
        ]


class HrLeaveBalanceTransaction(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    leave_type: str = Field(max_length=64)
    period_year: int
    transaction_type: str = Field(max_length=64)
    amount_days: float
    balance_before: float
    balance_after: float
    reference_type: str | None = Field(default=None, max_length=64)
    reference_id: str | None = None
    reason: str = Field(max_length=2000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_leave_balance_transactions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="leave_tx_by_employee",
            ),
        ]