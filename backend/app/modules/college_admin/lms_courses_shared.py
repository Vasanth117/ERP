"""Shared helpers for LMS course management pages."""

from __future__ import annotations

from collections import defaultdict

from beanie.odm.operators.find.comparison import Eq, In

from app.common.ids import to_object_id
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.lms_admin_models import LmsCourseMapping
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment
from app.modules.lms.models import CourseAssignment, LearningMaterial
from app.modules.students.student_lms_models import StudentLearningProgress


def status_presentation(*, published: bool | None, configuration_status: str | None = None) -> tuple[str, str]:
    if published is True:
        return "Published", "success"
    if published is False:
        return "Draft", "warning"
    key = (configuration_status or "draft").lower()
    if key == "published":
        return "Published", "success"
    return "Draft", "warning"


async def load_course_context(tenant_id) -> dict:
    mappings = await LmsCourseMapping.find(Eq(LmsCourseMapping.tenant_id, tenant_id)).to_list()
    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).sort("+name").to_list()
    materials = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).to_list()
    assignments = await CourseAssignment.find(Eq(CourseAssignment.tenant_id, tenant_id)).to_list()
    progress_rows = await StudentLearningProgress.find(Eq(StudentLearningProgress.tenant_id, tenant_id)).to_list()
    faculty_assignments = await FacultyAssignment.find(Eq(FacultyAssignment.tenant_id, tenant_id)).to_list()

    mappings_by_code = {m.course_code.upper(): m for m in mappings}
    title_by_code: dict[str, str] = {}
    faculty_by_code: dict[str, str] = {}
    for mat in materials:
        if mat.course_code:
            title_by_code.setdefault(mat.course_code.upper(), mat.title)
        if mat.faculty_user_id:
            faculty_by_code.setdefault(mat.course_code.upper(), str(mat.faculty_user_id))
    for assign in assignments:
        if assign.course_code:
            title_by_code.setdefault(assign.course_code.upper(), assign.title)
            if assign.faculty_user_id:
                faculty_by_code.setdefault(assign.course_code.upper(), str(assign.faculty_user_id))

    students_by_code: dict[str, set] = defaultdict(set)
    for row in progress_rows:
        students_by_code[row.course_code.upper()].add(row.user_id)

    faculty_by_code_from_assign: dict[str, tuple[str, str]] = {}
    section_by_code: dict[str, str] = {}
    for fa in faculty_assignments:
        if fa.status != AssignmentStatus.ACTIVE:
            continue
        code = (fa.course_code or "").upper()
        if not code:
            continue
        if code not in section_by_code and fa.section:
            section_by_code[code] = fa.section
        if code not in faculty_by_code_from_assign:
            faculty_by_code_from_assign[code] = (str(fa.user_id), fa.subject_name or fa.course_name or "—")

    dept_ids = {c.department_id for c in courses if c.department_id}
    dept_ids.update(m.department_id for m in mappings if m.department_id)
    dept_by_id: dict = {}
    if dept_ids:
        for dept in await InstitutionDepartment.find(In(InstitutionDepartment.id, list(dept_ids))).to_list():
            dept_by_id[dept.id] = dept.name or "—"

    faculty_ids = {faculty_by_code.get(c) for c in faculty_by_code}
    faculty_ids.update(uid for uid, _ in faculty_by_code_from_assign.values())
    faculty_users: dict[str, User] = {}
    oid_ids = []
    for raw in faculty_ids:
        if not raw:
            continue
        try:
            oid_ids.append(to_object_id(raw, "faculty_user_id"))
        except Exception:
            continue
    if oid_ids:
        for user in await User.find(In(User.id, oid_ids)).to_list():
            faculty_users[str(user.id)] = user

    def faculty_label(code: str) -> str:
        uid = faculty_by_code.get(code) or faculty_by_code_from_assign.get(code, (None, None))[0]
        if uid:
            user = faculty_users.get(uid)
            if user and user.full_name:
                return user.full_name
        return "—"

    return {
        "mappings_by_code": mappings_by_code,
        "courses": courses,
        "mappings": mappings,
        "title_by_code": title_by_code,
        "students_by_code": students_by_code,
        "dept_by_id": dept_by_id,
        "faculty_label": faculty_label,
        "section_by_code": section_by_code,
        "faculty_assignments": faculty_assignments,
        "faculty_users": faculty_users,
    }