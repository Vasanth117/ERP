"""Block mutating API calls against demo colleges for non-platform users."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.common.envelope import error_response
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.demo.guard import demo_blocks_mutation, resolve_effective_tenant_id

_MUTATION_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


async def _user_from_request(request: Request) -> User | None:
    token = _bearer_token(request)
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not isinstance(subject, str):
            return None
        from beanie import PydanticObjectId

        user = await User.get(PydanticObjectId(subject))
        if user is None or not user.is_active:
            return None
        return user
    except Exception:
        return None


class DemoMutationGuardMiddleware:
    """Reject writes on demo tenants except for platform operators and seed endpoints."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        settings = get_settings()
        prefix = settings.api_v1_prefix.rstrip("/")

        if request.method not in _MUTATION_METHODS:
            await self.app(scope, receive, send)
            return

        path = request.url.path
        if not path.startswith(f"{prefix}/"):
            await self.app(scope, receive, send)
            return

        relative = path[len(prefix) + 1 :]
        if relative.startswith("auth/") or relative.startswith("platform/demo-college/"):
            await self.app(scope, receive, send)
            return

        user = await _user_from_request(request)
        if user is None:
            await self.app(scope, receive, send)
            return

        tenant_id = await resolve_effective_tenant_id(user, request.headers.get("x-tenant-id"))
        seed_header = request.headers.get("x-demo-seed-secret")
        blocked = await demo_blocks_mutation(user, tenant_id, demo_seed_header=seed_header)
        if not blocked:
            await self.app(scope, receive, send)
            return

        body = error_response(
            code="DEMO_READ_ONLY",
            message=(
                "This is a read-only demo college. Data cannot be changed during client demos. "
                "Contact your developer to refresh demo data."
            ),
            request_id=request.headers.get("x-request-id"),
        )
        response = JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=body.model_dump())
        await response(scope, receive, send)