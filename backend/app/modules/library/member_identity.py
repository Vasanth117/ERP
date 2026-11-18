"""Validate library member links to institutional identities (no duplicate profiles)."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.library.member_enums import LibraryMemberCategory


async def assert_member_identity(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    category: LibraryMemberCategory,
) -> User:
    user = await User.find_one(Eq(User.id, user_id))
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="User not found in this college", status_code=422)
    if not user.is_active:
        raise AppError(code="VALIDATION_ERROR", message="User account is inactive", status_code=422)
    if category == LibraryMemberCategory.STUDENT and user.role != Role.STUDENT:
        raise AppError(code="VALIDATION_ERROR", message="Student category requires a student user account", status_code=422)
    if category == LibraryMemberCategory.FACULTY and user.role != Role.FACULTY:
        raise AppError(code="VALIDATION_ERROR", message="Faculty category requires a faculty user account", status_code=422)
    if category == LibraryMemberCategory.EMPLOYEE:
        employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, user_id))
        if employee is None:
            raise AppError(code="VALIDATION_ERROR", message="Employee record required for employee category", status_code=422)
    return user