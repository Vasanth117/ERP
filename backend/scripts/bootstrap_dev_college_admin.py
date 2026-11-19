"""Seed a demo college tenant and college admin for local development (idempotent)."""

import asyncio

from beanie.odm.operators.find.comparison import Eq

from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.tenants.domain_utils import normalize_tenant_code
from app.modules.tenants.models import Tenant

DEV_TENANT_CODE = "demo-college"
DEV_TENANT_NAME = "Demo College"
DEV_ADMIN_EMAIL = "admin@demo-college.edu"
DEV_ADMIN_PASSWORD = "CollegeAdmin123!"
DEV_ADMIN_NAME = "Demo College Admin"


async def main() -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        code = normalize_tenant_code(DEV_TENANT_CODE)
        tenant = await Tenant.find_one(Eq(Tenant.code, code))
        if tenant is None:
            tenant = Tenant(
                name=DEV_TENANT_NAME,
                code=code,
                institution_email=DEV_ADMIN_EMAIL,
                institution_type="college",
            )
            await tenant.insert()
            print(f"created tenant {code}")
        else:
            print(f"tenant {code} already exists")

        email = DEV_ADMIN_EMAIL.lower()
        user = await User.find_one(Eq(User.email, email), Eq(User.tenant_id, tenant.id))
        password_hash = hash_password(DEV_ADMIN_PASSWORD)
        if user is None:
            user = User(
                email=email,
                hashed_password=password_hash,
                full_name=DEV_ADMIN_NAME,
                role=Role.COLLEGE_ADMIN,
                tenant_id=tenant.id,
                is_active=True,
            )
            await user.insert()
            print(f"created college admin {email}")
        else:
            user.hashed_password = password_hash
            user.role = Role.COLLEGE_ADMIN
            user.is_active = True
            user.full_name = DEV_ADMIN_NAME
            user.updated_at = utcnow()
            await user.save()
            print(f"updated college admin {email}")

        print()
        print("--- Dev college admin (local only) ---")
        print(f"College code: {DEV_TENANT_CODE}")
        print(f"Email:        {DEV_ADMIN_EMAIL}")
        print(f"Password:     {DEV_ADMIN_PASSWORD}")
        print(f"Admin URL:    /college-admin/dashboard")
        print("--------------------------------------")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())