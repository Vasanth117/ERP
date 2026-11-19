"""Sync EmployeeRecord with HR snapshot and activity logs."""

from beanie import PydanticObjectId

from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.enums import HrStaffActivityType
from app.modules.hr.models import EmployeeProfileSnapshot
from app.modules.hr.operational_models import HrStaffActivityLog
from app.modules.tenants.models import Department


async def sync_employee_snapshot(employee: EmployeeRecord) -> None:
    dept_name = None
    if employee.department_id:
        dept = await Department.get(employee.department_id)
        if dept and dept.tenant_id == employee.tenant_id:
            dept_name = dept.name
    profile = await HrEmployeeProfile.find_one(
        Eq(HrEmployeeProfile.tenant_id, employee.tenant_id),
        Eq(HrEmployeeProfile.user_id, employee.user_id),
    )
    snapshot = await EmployeeProfileSnapshot.find_one(
        Eq(EmployeeProfileSnapshot.tenant_id, employee.tenant_id),
        Eq(EmployeeProfileSnapshot.employee_user_id, employee.user_id),
    )
    if snapshot is None:
        snapshot = EmployeeProfileSnapshot(tenant_id=employee.tenant_id, employee_user_id=employee.user_id)
    snapshot.employee_id = employee.employee_id
    snapshot.designation = employee.designation
    snapshot.department_name = dept_name
    snapshot.joining_date = employee.joining_date
    snapshot.employment_type = employee.employment_type
    snapshot.permitted_fields = {
        "employee_id": employee.employee_id,
        "employee_code": profile.employee_code if profile else employee.employee_id,
        "designation": employee.designation,
        "department_name": dept_name,
        "joining_date": employee.joining_date.isoformat() if employee.joining_date else None,
        "employment_type": employee.employment_type,
        "official_name": f"{profile.first_name} {profile.last_name}".strip() if profile else None,
    }
    snapshot.updated_at = utcnow()
    if snapshot.id is None:
        await snapshot.insert()
    else:
        await snapshot.save()


async def log_hr_activity(
    tenant_id: PydanticObjectId,
    activity_type: HrStaffActivityType,
    summary: str,
    *,
    actor_id: PydanticObjectId | None = None,
    employee_user_id: PydanticObjectId | None = None,
    department_id: PydanticObjectId | None = None,
    campus_id: PydanticObjectId | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    status_label: str | None = None,
    metadata: dict | None = None,
    mirror_institution_audit: bool = True,
) -> None:
    await HrStaffActivityLog(
        tenant_id=tenant_id,
        activity_type=activity_type,
        summary=summary[:500],
        actor_id=actor_id,
        employee_user_id=employee_user_id,
        department_id=department_id,
        campus_id=campus_id,
        resource_type=resource_type,
        resource_id=resource_id,
        status_label=status_label,
        metadata=metadata or {},
    ).insert()
    if mirror_institution_audit:
        from app.modules.college_admin.security_admin_service import append_institution_audit

        await append_institution_audit(
            tenant_id,
            actor_id=actor_id,
            action=f"hr.{activity_type.value}",
            module="hr",
            resource_type=resource_type or "hr_activity",
            resource_id=resource_id,
            metadata={
                "summary": summary[:200],
                **(metadata or {}),
                **({"employee_user_id": str(employee_user_id)} if employee_user_id else {}),
            },
        )