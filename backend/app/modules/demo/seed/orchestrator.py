"""Run all demo college seed steps."""

from app.modules.demo.constants import DEFAULT_FACULTY_COUNT, DEFAULT_STUDENT_COUNT, DEMO_PASSWORD, DEMO_TENANT_CODE
from app.modules.demo.seed.foundation import seed_foundation
from app.modules.demo.seed.operations import seed_operations
from app.modules.demo.seed.people import seed_people


async def seed_demo_college(
    *,
    student_count: int = DEFAULT_STUDENT_COUNT,
    faculty_count: int = DEFAULT_FACULTY_COUNT,
    reset: bool = False,
) -> dict:
    """Populate the showcase demo tenant. Idempotent unless ``reset`` is True."""
    ctx = await seed_foundation(student_target=student_count, reset=reset)
    ctx = await seed_people(ctx, student_count=student_count, faculty_count=faculty_count)
    await seed_operations(ctx)
    return {
        "tenant_code": DEMO_TENANT_CODE,
        "tenant_id": str(ctx.tenant.id),
        "is_demo": True,
        "student_count": len(ctx.student_users),
        "faculty_count": len(ctx.faculty_users),
        "admin_email": ctx.admin.email,
        "default_password": DEMO_PASSWORD,
        "staff_logins": {key: user.email for key, user in ctx.staff_users.items()},
        "departments": list(ctx.departments.keys()),
    }