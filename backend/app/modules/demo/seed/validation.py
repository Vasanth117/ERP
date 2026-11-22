"""Post-seed integrity checks for the showcase tenant."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.roles import Role
from app.modules.attendance.models import AttendanceRecord, AttendanceSession
from app.modules.auth.models import User
from app.modules.faculty.models import FacultyProfile
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand
from app.modules.hr.models import EmployeeProfileSnapshot
from app.modules.students.models import StudentProfile


async def validate_showcase_tenant(tenant_id: PydanticObjectId) -> dict:
    """Summarize record counts and critical relationship checks."""
    students = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).count()
    faculty_profiles = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).count()
    faculty_users = await User.find(Eq(User.tenant_id, tenant_id), Eq(User.role, Role.FACULTY)).count()
    employees = await EmployeeProfileSnapshot.find(Eq(EmployeeProfileSnapshot.tenant_id, tenant_id)).count()
    sessions = await AttendanceSession.find(Eq(AttendanceSession.tenant_id, tenant_id)).count()
    attendance_rows = await AttendanceRecord.find(Eq(AttendanceRecord.tenant_id, tenant_id)).count()
    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).count()
    payments = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).count()

    issues: list[str] = []
    if students > 0 and faculty_profiles < min(faculty_users, 1):
        issues.append("Faculty users exist without FacultyProfile rows")
    if students > 0 and demands == 0:
        issues.append("Students exist without fee demands")
    if faculty_users > 0 and faculty_profiles < faculty_users * 0.9:
        issues.append("Faculty profile coverage below 90%")
    if students > faculty_profiles and students > 500 and employees < faculty_profiles:
        issues.append("Employee snapshots fewer than faculty profiles")

    counts = {
        "students": students,
        "faculty_users": faculty_users,
        "faculty_profiles": faculty_profiles,
        "employee_snapshots": employees,
        "attendance_sessions": sessions,
        "attendance_records": attendance_rows,
        "fee_demands": demands,
        "payments": payments,
    }
    critical_ok = len(issues) == 0 and students >= 100 and faculty_profiles >= 50
    return {
        "status": "ready" if critical_ok else "needs_attention",
        "counts": counts,
        "issues": issues,
    }