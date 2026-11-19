"""Bridge HR activity logs to institution audit (via log_hr_activity mirror)."""

from beanie import PydanticObjectId

from app.modules.hr.employee_sync import log_hr_activity
from app.modules.hr.enums import HrStaffActivityType


async def record_hr_audit(
    tenant_id: PydanticObjectId,
    activity_type: HrStaffActivityType,
    summary: str,
    *,
    actor_id: PydanticObjectId | None = None,
    employee_user_id: PydanticObjectId | None = None,
    department_id: PydanticObjectId | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    await log_hr_activity(
        tenant_id,
        activity_type,
        summary,
        actor_id=actor_id,
        employee_user_id=employee_user_id,
        department_id=department_id,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata,
        mirror_institution_audit=True,
    )