"""Seed demo student and parent portal users (idempotent, local dev only)."""

import asyncio

from beanie.odm.operators.find.comparison import Eq

from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.parents.enums import ParentAccountStatus
from app.modules.parents.models import ParentProfile
from app.modules.students.models import StudentProfile
from app.modules.tenants.domain_utils import normalize_tenant_code
from app.modules.tenants.models import Tenant

DEV_TENANT_CODE = "demo-college"
DEV_STUDENT_ID = "STU-DEMO001"
DEV_STUDENT_EMAIL = "student.demo@demo-college.edu"
DEV_STUDENT_PASSWORD = "StudentDemo123!"
DEV_PARENT_ID = "PAR-DEMO001"
DEV_PARENT_EMAIL = "parent.demo@demo-college.edu"
DEV_PARENT_PASSWORD = "ParentDemo123!"


async def _ensure_user(
    *,
    tenant_id,
    email: str,
    password: str,
    full_name: str,
    role: Role,
) -> User:
    email = email.lower()
    user = await User.find_one(Eq(User.email, email), Eq(User.tenant_id, tenant_id))
    password_hash = hash_password(password)
    if user is None:
        user = User(
            email=email,
            hashed_password=password_hash,
            full_name=full_name,
            role=role,
            tenant_id=tenant_id,
            is_active=True,
        )
        await user.insert()
        print(f"created user {email} ({role.value})")
    else:
        user.hashed_password = password_hash
        user.role = role
        user.full_name = full_name
        user.is_active = True
        user.updated_at = utcnow()
        await user.save()
        print(f"updated user {email} ({role.value})")
    return user


async def main() -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        code = normalize_tenant_code(DEV_TENANT_CODE)
        tenant = await Tenant.find_one(Eq(Tenant.code, code))
        if tenant is None:
            print(f"tenant {code} missing — run bootstrap_dev_college_admin.py first")
            return

        student = await _ensure_user(
            tenant_id=tenant.id,
            email=DEV_STUDENT_EMAIL,
            password=DEV_STUDENT_PASSWORD,
            full_name="Demo Student",
            role=Role.STUDENT,
        )
        parent = await _ensure_user(
            tenant_id=tenant.id,
            email=DEV_PARENT_EMAIL,
            password=DEV_PARENT_PASSWORD,
            full_name="Demo Parent",
            role=Role.PARENT,
        )

        student_profile = await StudentProfile.find_one(
            Eq(StudentProfile.tenant_id, tenant.id),
            Eq(StudentProfile.user_id, student.id),
        )
        if student_profile is None:
            student_profile = StudentProfile(
                tenant_id=tenant.id,
                user_id=student.id,
                student_id=DEV_STUDENT_ID,
                roll_number="24CSE001",
                programme_name="B.Tech CSE",
                batch_label="2024",
                section_code="A",
            )
            await student_profile.insert()
            print(f"created student profile {DEV_STUDENT_ID}")
        else:
            student_profile.student_id = DEV_STUDENT_ID
            student_profile.roll_number = student_profile.roll_number or "24CSE001"
            student_profile.updated_at = utcnow()
            await student_profile.save()
            print(f"updated student profile {DEV_STUDENT_ID}")

        parent_profile = await ParentProfile.find_one(
            Eq(ParentProfile.tenant_id, tenant.id),
            Eq(ParentProfile.user_id, parent.id),
        )
        if parent_profile is None:
            parent_profile = ParentProfile(
                tenant_id=tenant.id,
                user_id=parent.id,
                parent_id=DEV_PARENT_ID,
                display_name="Demo Parent",
                account_status=ParentAccountStatus.ACTIVE,
                email_verified=True,
                mobile_verified=True,
                identity_verified=True,
                activated_at=utcnow(),
            )
            await parent_profile.insert()
            print(f"created parent profile {DEV_PARENT_ID}")
        else:
            parent_profile.parent_id = DEV_PARENT_ID
            parent_profile.account_status = ParentAccountStatus.ACTIVE
            parent_profile.email_verified = True
            parent_profile.updated_at = utcnow()
            await parent_profile.save()
            print(f"updated parent profile {DEV_PARENT_ID}")

        print()
        print("--- Dev portal users (local only) ---")
        print(f"College code:  {DEV_TENANT_CODE}")
        print(f"Student id:    {DEV_STUDENT_ID}")
        print(f"Student pass:  {DEV_STUDENT_PASSWORD}")
        print(f"Parent id:     {DEV_PARENT_ID}")
        print(f"Parent pass:   {DEV_PARENT_PASSWORD}")
        print("-------------------------------------")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())