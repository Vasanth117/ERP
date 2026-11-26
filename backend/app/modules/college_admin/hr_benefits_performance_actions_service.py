"""College admin benefits & performance actions."""

from __future__ import annotations

from datetime import date

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.hr.enums import HrPerformanceCycleStatus
from app.modules.hr.performance_models import HrPerformanceCycle
from app.modules.hr.performance_schemas import PerformanceCycleUpsert
from app.modules.hr.performance_service import activate_performance_cycle, upsert_performance_cycle


def _academic_year_bounds(today: date) -> tuple[date, date, str]:
    if today.month >= 4:
        start = date(today.year, 4, 1)
        end = date(today.year + 1, 3, 31)
        label = f"{today.year}-{str(today.year + 1)[-2:]}"
    else:
        start = date(today.year - 1, 4, 1)
        end = date(today.year, 3, 31)
        label = f"{today.year - 1}-{str(today.year)[-2:]}"
    return start, end, label


async def college_admin_open_performance_cycle(scope: AccessScope, *, cycle_id: str | None = None) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)

    active = await HrPerformanceCycle.find_one(
        Eq(HrPerformanceCycle.tenant_id, tenant_id),
        Eq(HrPerformanceCycle.status, HrPerformanceCycleStatus.ACTIVE),
    )
    if active:
        return {"cycle_id": str(active.id), "status": active.status.value, "already_active": True}

    target: HrPerformanceCycle | None = None
    if cycle_id:
        from app.common.ids import to_object_id

        target = await HrPerformanceCycle.get(to_object_id(cycle_id, "cycle_id"))
        if target is None or target.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Performance cycle not found", status_code=404)
    else:
        target = await HrPerformanceCycle.find_one(
            Eq(HrPerformanceCycle.tenant_id, tenant_id),
            Eq(HrPerformanceCycle.status, HrPerformanceCycleStatus.DRAFT),
        )

    if target is None:
        today = utcnow().date()
        start, end, label = _academic_year_bounds(today)
        code = f"AP-{label.replace('-', '')}"
        created = await upsert_performance_cycle(
            scope,
            PerformanceCycleUpsert(
                cycle_code=code,
                title=f"Appraisal cycle {label}",
                cycle_kind="annual",
                start_date=start,
                end_date=end,
                eligible_categories=[],
                criteria=[],
            ),
        )
        from app.common.ids import to_object_id

        target = await HrPerformanceCycle.get(to_object_id(created.id, "cycle_id"))

    if target is None:
        raise AppError(code="CONFLICT", message="Could not prepare performance cycle", status_code=409)

    result = await activate_performance_cycle(scope, str(target.id))
    refreshed = await HrPerformanceCycle.get(target.id)
    return {
        "cycle_id": str(target.id),
        "status": refreshed.status.value if refreshed else HrPerformanceCycleStatus.ACTIVE.value,
        **result,
    }