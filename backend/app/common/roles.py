"""Roles used by the ERP access checks."""

from enum import Enum


class Role(str, Enum):
  SUPER_ADMIN = "super_admin"
  PLATFORM_ADMIN = "platform_admin"
  COLLEGE_ADMIN = "college_admin"
  DEPARTMENT_ADMIN = "department_admin"
  EXAMINATION_CELL = "examination_cell"
  HR_STAFF = "hr_staff"
  ACCOUNTS_STAFF = "accounts_staff"
  FINANCE_STAFF = "finance_staff"
  HOSTEL_ADMIN = "hostel_admin"
  LIBRARIAN = "librarian"
  FACULTY = "faculty"
  STUDENT = "student"
  PARENT = "parent"


TENANT_ADMIN_ROLES = {Role.SUPER_ADMIN, Role.COLLEGE_ADMIN}
DEPARTMENT_SCOPED_ROLES = {Role.DEPARTMENT_ADMIN, Role.FACULTY}
TENANT_REQUIRED_ROLES = {
  Role.COLLEGE_ADMIN,
  Role.DEPARTMENT_ADMIN,
  Role.FACULTY,
  Role.STUDENT,
  Role.PARENT,
  Role.FINANCE_STAFF,
  Role.HR_STAFF,
  Role.EXAMINATION_CELL,
  Role.HOSTEL_ADMIN,
  Role.LIBRARIAN,
  Role.ACCOUNTS_STAFF,
}
DEPARTMENT_REQUIRED_ROLES = {Role.DEPARTMENT_ADMIN, Role.FACULTY}
PLATFORM_ROLES = {Role.SUPER_ADMIN, Role.PLATFORM_ADMIN}
