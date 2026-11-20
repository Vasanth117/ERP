"""Students, faculty, and role-based staff accounts."""

from datetime import date

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.security import hash_password
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.auth.models import User
from app.modules.demo.constants import (
    DEMO_ACADEMIC_YEAR,
    DEMO_PASSWORD,
    DEMO_SEMESTER,
    DEPARTMENTS,
    ROLE_ACCOUNTS,
)
from app.modules.demo.seed.context import DemoSeedContext
from app.common.time import utcnow
from app.modules.parents.enums import ParentRelationshipType
from app.modules.parents.enums import ParentRelationshipStatus
from app.modules.parents.models import ParentStudentRelationship
from app.modules.students.models import StudentAcademicRecord, StudentProfile


_FIRST_NAMES = (
    "Aarav",
    "Diya",
    "Vikram",
    "Kavya",
    "Rohan",
    "Ananya",
    "Karthik",
    "Meera",
    "Arjun",
    "Sneha",
    "Harish",
    "Pooja",
    "Naveen",
    "Lakshmi",
    "Gaurav",
    "Divya",
    "Sanjay",
    "Nithya",
    "Rahul",
    "Ishita",
)
_LAST_NAMES = ("Kumar", "Sharma", "Iyer", "Reddy", "Nair", "Patel", "Singh", "Menon", "Rao", "Pillai")


def _role_from_key(key: str) -> Role:
    return Role(key)


async def seed_people(ctx: DemoSeedContext, *, student_count: int, faculty_count: int) -> DemoSeedContext:
    tenant_id = ctx.tenant.id
    existing_students = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).count()
    if existing_students >= student_count // 2:
        ctx.student_users = await User.find(Eq(User.tenant_id, tenant_id), Eq(User.role, Role.STUDENT)).to_list()
        ctx.faculty_users = await User.find(Eq(User.tenant_id, tenant_id), Eq(User.role, Role.FACULTY)).to_list()
        for _key, email, _name, role_key in ROLE_ACCOUNTS:
            user = await User.find_one(Eq(User.email, email.lower()), Eq(User.tenant_id, tenant_id))
            if user is not None:
                ctx.staff_users[_key] = user
        ctx.staff_users["college_admin"] = ctx.admin
        return ctx

    password_hash = hash_password(DEMO_PASSWORD)
    dept_codes = [d[0] for d in DEPARTMENTS]

    for key, email, full_name, role_key in ROLE_ACCOUNTS:
        if key == "college_admin":
            continue
        role = _role_from_key(role_key)
        dept_id = ctx.departments["CSE"].id if role == Role.DEPARTMENT_ADMIN else None
        user = await User.find_one(Eq(User.email, email.lower()), Eq(User.tenant_id, tenant_id))
        if user is None:
            user = User(
                email=email.lower(),
                hashed_password=password_hash,
                full_name=full_name,
                role=role,
                tenant_id=tenant_id,
                department_id=dept_id,
                is_active=True,
            )
            await user.insert()
        ctx.staff_users[key] = user

    faculty_users: list[User] = []
    for i in range(faculty_count):
        dept_code = dept_codes[i % len(dept_codes)]
        dept = ctx.departments[dept_code]
        email = f"faculty{i+1:03d}@sviet-demo.edu"
        user = await User.find_one(Eq(User.email, email), Eq(User.tenant_id, tenant_id))
        if user is None:
            fname = _FIRST_NAMES[i % len(_FIRST_NAMES)]
            lname = _LAST_NAMES[i % len(_LAST_NAMES)]
            user = User(
                email=email,
                hashed_password=password_hash,
                full_name=f"Prof. {fname} {lname}",
                role=Role.FACULTY,
                tenant_id=tenant_id,
                department_id=dept.id,
                is_active=True,
            )
            await user.insert()
        faculty_users.append(user)

    student_users: list[User] = []
    student_docs: list[StudentProfile] = []
    roster_docs: list[EnrollmentRosterEntry] = []
    academic_docs: list[StudentAcademicRecord] = []

    for i in range(student_count):
        dept_code = dept_codes[i % len(dept_codes)]
        dept = ctx.departments[dept_code]
        prog_code = next(p[2] for p in DEPARTMENTS if p[0] == dept_code)
        prog_name = next(p[3] for p in DEPARTMENTS if p[0] == dept_code)
        email = f"student{i+1:04d}@sviet-demo.edu"
        user = await User.find_one(Eq(User.email, email), Eq(User.tenant_id, tenant_id))
        if user is None:
            fname = _FIRST_NAMES[i % len(_FIRST_NAMES)]
            lname = _LAST_NAMES[(i // len(_FIRST_NAMES)) % len(_LAST_NAMES)]
            user = User(
                email=email,
                hashed_password=password_hash,
                full_name=f"{fname} {lname}",
                role=Role.STUDENT,
                tenant_id=tenant_id,
                department_id=dept.id,
                is_active=True,
            )
            await user.insert()
            batch = "2022" if i % 3 == 0 else "2023" if i % 3 == 1 else "2024"
            section = "A" if i % 2 == 0 else "B"
            roll = f"{batch[-2:]}{dept_code}{i+1:03d}"
            student_docs.append(
                StudentProfile(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    student_id=f"STU-{i+1:05d}",
                    roll_number=roll,
                    admission_number=f"ADM-{batch}-{i+1:04d}",
                    admission_date=date(int(batch), 7, 15),
                    department_id=dept.id,
                    programme_code=prog_code,
                    programme_name=prog_name,
                    batch_label=batch,
                    section_code=section,
                )
            )
            roster_docs.append(
                EnrollmentRosterEntry(
                    tenant_id=tenant_id,
                    course_id=f"{dept_code.lower()}101",
                    course_code=f"{dept_code}101",
                    section_code=section,
                    student_user_id=user.id,
                    roll_number=roll,
                    display_name=user.full_name or roll,
                    academic_year_label=DEMO_ACADEMIC_YEAR,
                    semester_label=DEMO_SEMESTER,
                )
            )
            academic_docs.append(
                StudentAcademicRecord(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    academic_year_label=DEMO_ACADEMIC_YEAR,
                    semester_label=DEMO_SEMESTER,
                    fee_snapshot={
                        "status": "partial",
                        "outstanding_amount": 12000 + (i % 5) * 1500,
                        "currency": "INR",
                        "paid_percentage": 72 + (i % 20),
                    },
                )
            )
        student_users.append(user)

    if student_docs:
        await StudentProfile.insert_many(student_docs)
    if roster_docs:
        await EnrollmentRosterEntry.insert_many(roster_docs)
    if academic_docs:
        await StudentAcademicRecord.insert_many(academic_docs)

    parent_user = ctx.staff_users.get("parent")
    if parent_user and student_users:
        linked = student_users[:3]
        for student in linked:
            exists = await ParentStudentRelationship.find_one(
                Eq(ParentStudentRelationship.tenant_id, tenant_id),
                Eq(ParentStudentRelationship.parent_user_id, parent_user.id),
                Eq(ParentStudentRelationship.student_user_id, student.id),
            )
            if exists is None:
                await ParentStudentRelationship(
                    tenant_id=tenant_id,
                    parent_user_id=parent_user.id,
                    student_user_id=student.id,
                    relationship_type=ParentRelationshipType.FATHER,
                    status=ParentRelationshipStatus.ACTIVE,
                    verified_at=utcnow(),
                    verified_by=ctx.admin.id,
                ).insert()

    ctx.faculty_users = faculty_users
    ctx.student_users = student_users
    return ctx