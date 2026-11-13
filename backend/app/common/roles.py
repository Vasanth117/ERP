"""Roles used by the ERP access checks."""

from enum import Enum


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    COLLEGE_ADMIN = "college_admin"
    DEPARTMENT_ADMIN = "department_admin"
    FACULTY = "faculty"
    STUDENT = "student"
    PARENT = "parent"
    FINANCE_STAFF = "finance_staff"


TENANT_ADMIN_ROLES = {Role.SUPER_ADMIN, Role.COLLEGE_ADMIN}
DEPARTMENT_SCOPED_ROLES = {Role.DEPARTMENT_ADMIN, Role.FACULTY}
TENANT_REQUIRED_ROLES = {
    Role.COLLEGE_ADMIN,
    Role.DEPARTMENT_ADMIN,
    Role.FACULTY,
    Role.STUDENT,
    Role.PARENT,
    Role.FINANCE_STAFF,
}
DEPARTMENT_REQUIRED_ROLES = {Role.DEPARTMENT_ADMIN, Role.FACULTY}
