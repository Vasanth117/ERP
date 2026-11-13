"""Seed platform role definitions."""

import asyncio

from app.authorization.platform_roles import PLATFORM_ROLE_PERMISSIONS
from app.core.database import close_mongo, connect_to_mongo
from app.core.logging import configure_logging
from app.modules.platform_identity.enums import PlatformRoleCode
from app.modules.platform_identity.models import PlatformRoleDefinition


async def main() -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        for code, perms in PLATFORM_ROLE_PERMISSIONS.items():
            existing = await PlatformRoleDefinition.find_one(PlatformRoleDefinition.code == code)
            if existing is None:
                await PlatformRoleDefinition(
                    code=code,
                    name=code.value.replace("_", " ").title(),
                    permission_codes=sorted(p.value for p in perms),
                    is_privileged=code
                    in {
                        PlatformRoleCode.PLATFORM_OWNER,
                        PlatformRoleCode.PLATFORM_SUPER_ADMIN,
                    },
                    requires_mfa=code
                    in {
                        PlatformRoleCode.PLATFORM_OWNER,
                        PlatformRoleCode.PLATFORM_SUPER_ADMIN,
                        PlatformRoleCode.PLATFORM_OPS_ADMIN,
                    },
                ).insert()
                print(f"seeded role {code.value}")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
