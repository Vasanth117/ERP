"""Run all demo college seed steps."""

from app.common.time import utcnow
from app.modules.demo.constants import DEMO_PASSWORD, DEMO_TENANT_CODE
from app.modules.demo.models import DemoGenerationRun
from app.modules.demo.scale import resolve_demo_scale
from app.modules.demo.seed.analytics import seed_showcase_analytics
from app.modules.demo.seed.foundation import seed_foundation
from app.modules.demo.seed.operations import seed_operations
from app.modules.demo.seed.people import seed_people
from app.modules.demo.seed.validation import validate_showcase_tenant


async def seed_demo_college(
    *,
    student_count: int | None = None,
    faculty_count: int | None = None,
    reset: bool = False,
    profile: str | None = None,
) -> dict:
    """Populate the showcase demo tenant (Grand Horizon / GHIT)."""
    scale = resolve_demo_scale(profile)
    students = student_count if student_count is not None else scale.students
    faculty = faculty_count if faculty_count is not None else scale.faculty
    staff = scale.non_faculty_staff

    ctx = await seed_foundation(student_target=students, reset=reset)
    run = DemoGenerationRun(
        tenant_id=ctx.tenant.id,
        tenant_code=ctx.tenant.code,
        profile=scale.name,
        generator_version=scale.generator_version,
        status="generating",
    )
    await run.insert()

    try:
        ctx = await seed_people(ctx, student_count=students, faculty_count=faculty)
        await seed_operations(ctx)
        await seed_showcase_analytics(ctx, non_faculty_employees=staff)
        validation = await validate_showcase_tenant(ctx.tenant.id)
        run.status = validation["status"]
        run.record_counts = validation["counts"]
        run.validation = validation
        run.finished_at = utcnow()
        await run.save()
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)[:2000]
        run.finished_at = utcnow()
        await run.save()
        raise

    return {
        "tenant_code": DEMO_TENANT_CODE,
        "tenant_id": str(ctx.tenant.id),
        "is_demo": True,
        "profile": scale.name,
        "generator_version": scale.generator_version,
        "student_count": len(ctx.student_users),
        "faculty_count": len(ctx.faculty_users),
        "admin_email": ctx.admin.email,
        "default_password": DEMO_PASSWORD,
        "staff_logins": {key: user.email for key, user in ctx.staff_users.items()},
        "departments": list(ctx.departments.keys()),
        "validation": validation,
    }