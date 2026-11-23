"""Students, faculty, and role-based staff accounts."""

from beanie.odm.operators.find.comparison import Eq

from app.common.roles import Role
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.demo.constants import DEMO_PASSWORD, DEPARTMENTS, ROLE_ACCOUNTS
from app.modules.demo.seed.context import DemoSeedContext
from app.modules.demo.seed.people_bulk import bulk_seed_faculty, bulk_seed_students
from app.common.time import utcnow
from app.modules.parents.enums import ParentRelationshipType
from app.modules.parents.enums import ParentRelationshipStatus
from app.modules.parents.models import ParentStudentRelationship
from app.modules.students.models import StudentProfile
def _role_from_key(key: str) -> Role:
    return Role(key)


async def seed_people(ctx: DemoSeedContext, *, student_count: int, faculty_count: int) -> DemoSeedContext:
    tenant_id = ctx.tenant.id
    existing_students = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).count()
    existing_faculty_users = await User.find(
        Eq(User.tenant_id, tenant_id),
        Eq(User.role, Role.FACULTY),
    ).count()
    if existing_students >= student_count and existing_faculty_users >= faculty_count:
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
        first_dept_code = dept_codes[0]
        dept_id = ctx.departments[first_dept_code].id if role == Role.DEPARTMENT_ADMIN else None
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

    if existing_faculty_users < faculty_count:
        faculty_users = await bulk_seed_faculty(
            ctx,
            faculty_count=faculty_count,
            password_hash=password_hash,
            start_index=existing_faculty_users,
        )
    else:
        faculty_users = await User.find(Eq(User.tenant_id, tenant_id), Eq(User.role, Role.FACULTY)).to_list()

    if existing_students < student_count:
        student_users = await bulk_seed_students(
            ctx,
            student_count=student_count,
            password_hash=password_hash,
            start_index=existing_students,
        )
    else:
        student_users = await User.find(Eq(User.tenant_id, tenant_id), Eq(User.role, Role.STUDENT)).to_list()

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