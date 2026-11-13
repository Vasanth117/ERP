"""Create the first super admin account."""

import argparse
import asyncio
import os

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.modules.auth.models import User


async def _create(email: str, password: str, full_name: str) -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        existing = await User.find_one(User.email == email)
        if existing is not None:
            print(f"User already exists: {email}")
            return 1
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=Role.SUPER_ADMIN,
            tenant_id=None,
            department_id=None,
            is_active=True,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        await user.insert()
        print(f"Super admin created: {user.email} ({user.id})")
        return 0
    finally:
        await close_mongo()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first ERP super admin.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--password", default=os.environ.get("ERP_BOOTSTRAP_PASSWORD"))
    args = parser.parse_args()

    if not args.password or len(args.password) < 8:
        raise SystemExit("Pass --password or ERP_BOOTSTRAP_PASSWORD with at least 8 characters")

    try:
        email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    except ValidationError as exc:
        raise SystemExit("Invalid email") from exc

    full_name = args.full_name.strip()
    if not full_name:
        raise SystemExit("Full name is required")

    raise SystemExit(asyncio.run(_create(email, args.password, full_name)))


if __name__ == "__main__":
    main()
