"""Request-scoped context."""

from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
tenant_impersonation_var: ContextVar[bool] = ContextVar("tenant_impersonation", default=False)


def get_request_id() -> str | None:
  return request_id_var.get()
