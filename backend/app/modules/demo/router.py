"""Platform endpoints to (re)build the demo college — developers only."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from app.api.deps import AccessScope, require_permission
from app.authorization.permissions import Permission
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.roles import Role
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.demo.seed.orchestrator import seed_demo_college

router = APIRouter(prefix="/demo-college", tags=["demo-college"])


@router.post("/seed", response_model=ApiResponse[dict])
async def seed_demo_college_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_TENANT_MANAGE))],
    reset: Annotated[bool, Query(description="Delete existing demo tenant data before seeding")] = False,
    students: Annotated[int, Query(ge=20, le=5000)] = 180,
    faculty: Annotated[int, Query(ge=5, le=500)] = 36,
    x_demo_seed_secret: Annotated[str | None, Header(alias="X-Demo-Seed-Secret")] = None,
) -> ApiResponse[dict]:
    if scope.role not in {Role.SUPER_ADMIN, Role.PLATFORM_ADMIN}:
        raise AppError(code="FORBIDDEN", message="Only platform operators may refresh demo data", status_code=403)
    settings = get_settings()
    if settings.demo_seed_secret and x_demo_seed_secret != settings.demo_seed_secret:
        raise AppError(code="FORBIDDEN", message="Invalid demo seed secret", status_code=403)
    summary = await seed_demo_college(student_count=students, faculty_count=faculty, reset=reset)
    return success_response(summary, request_id=get_request_id())


@router.get("/status", response_model=ApiResponse[dict])
async def demo_college_status_route(
    scope: Annotated[AccessScope, Depends(require_permission(Permission.PLATFORM_TENANT_READ))],
) -> ApiResponse[dict]:
    from beanie.odm.operators.find.comparison import Eq

    from app.modules.demo.constants import DEMO_TENANT_CODE
    from app.modules.students.models import StudentProfile
    from app.modules.tenants.domain_utils import normalize_tenant_code
    from app.modules.tenants.models import Tenant

    code = normalize_tenant_code(DEMO_TENANT_CODE)
    tenant = await Tenant.find_one(Eq(Tenant.code, code))
    if tenant is None:
        return success_response({"seeded": False, "tenant_code": DEMO_TENANT_CODE}, request_id=get_request_id())
    students = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant.id)).count()
    return success_response(
        {
            "seeded": students > 0,
            "tenant_code": tenant.code,
            "tenant_id": str(tenant.id),
            "is_demo": tenant.is_demo,
            "student_profiles": students,
        },
        request_id=get_request_id(),
    )