"""Apply approved leave to employee day attendance."""

from datetime import timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.hr.enums import EmployeeAttendanceDayStatus
from app.modules.hr.models import LeaveRequest
from app.modules.hr.operational_models import EmployeeDayAttendance


async def apply_leave_to_attendance(leave: LeaveRequest) -> None:
    day = leave.start_date
    while day <= leave.end_date:
        if day.weekday() < 5:
            existing = await EmployeeDayAttendance.find_one(
                Eq(EmployeeDayAttendance.tenant_id, leave.tenant_id),
                Eq(EmployeeDayAttendance.employee_user_id, leave.employee_user_id),
                Eq(EmployeeDayAttendance.attendance_date, day),
            )
            if existing is None:
                await EmployeeDayAttendance(
                    tenant_id=leave.tenant_id,
                    employee_user_id=leave.employee_user_id,
                    attendance_date=day,
                    status=EmployeeAttendanceDayStatus.ON_LEAVE,
                    remarks=f"Leave {leave.leave_type}",
                ).insert()
            elif existing.status != EmployeeAttendanceDayStatus.ON_LEAVE:
                existing.status = EmployeeAttendanceDayStatus.ON_LEAVE
                existing.remarks = f"Leave {leave.leave_type}"
                existing.updated_at = utcnow()
                await existing.save()
        day += timedelta(days=1)