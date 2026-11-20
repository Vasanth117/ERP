"""Shared campus aggregation helpers."""

from __future__ import annotations

from collections import defaultdict

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.students.models import StudentProfile


async def campus_student_counts(tenant_id: PydanticObjectId, campus_ids: list[str]) -> dict[str, int]:
    if not campus_ids:
        return {}
    main_campus_id = campus_ids[0]
    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_to_campuses: dict[PydanticObjectId, list[PydanticObjectId]] = {}
    for dept in departments:
        targets = list(dept.campus_ids)
        if not targets and main_campus_id:
            targets = [PydanticObjectId(main_campus_id)]
        dept_to_campuses[dept.id] = targets

    counts: dict[str, int] = defaultdict(int)
    students = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    for student in students:
        if student.department_id is None:
            if main_campus_id:
                counts[main_campus_id] += 1
            continue
        campus_targets = dept_to_campuses.get(student.department_id)
        if not campus_targets:
            if main_campus_id:
                counts[main_campus_id] += 1
            continue
        for cid in campus_targets:
            counts[str(cid)] += 1
    return counts


async def campus_staff_counts(tenant_id: PydanticObjectId, campus_oid: PydanticObjectId) -> int:
    dept_ids = {
        dept.id
        for dept in await InstitutionDepartment.find(
            Eq(InstitutionDepartment.tenant_id, tenant_id),
            Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
        ).to_list()
        if campus_oid in dept.campus_ids or not dept.campus_ids
    }
    employees = await EmployeeRecord.find(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.employment_status, FacultyEmploymentStatus.ACTIVE),
    ).to_list()
    total = 0
    for emp in employees:
        if emp.campus_id == campus_oid:
            total += 1
        elif emp.department_id in dept_ids:
            total += 1
    return total