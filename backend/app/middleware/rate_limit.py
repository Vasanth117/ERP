"""Redis-backed rate limiting for sensitive routes."""

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import get_settings
from app.core.redis import get_redis


class LoginRateLimitMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
    settings = get_settings()
    if request.url.path.endswith("/auth/login") and request.method == "POST":
      client = request.client.host if request.client else "unknown"
      key = f"rl:login:{client}"
      redis = get_redis()
      count = await redis.incr(key)
      if count == 1:
        await redis.expire(key, 60)
      if count > settings.login_rate_limit_per_minute:
        return Response(
          status_code=status.HTTP_429_TOO_MANY_REQUESTS,
          content='{"success":false,"error":{"code":"RATE_LIMITED","message":"Too many login attempts"}}',
          media_type="application/json",
        )
    return await call_next(request)
