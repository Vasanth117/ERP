"""Standard API response envelope."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
  code: str
  message: str
  details: list[dict[str, Any]] = Field(default_factory=list)


class ApiMeta(BaseModel):
  request_id: str | None = None


class ApiResponse(BaseModel, Generic[T]):
  success: bool
  data: T | None = None
  error: ErrorBody | None = None
  meta: ApiMeta = Field(default_factory=ApiMeta)


def success_response(data: T, *, request_id: str | None = None) -> ApiResponse[T]:
  return ApiResponse(success=True, data=data, error=None, meta=ApiMeta(request_id=request_id))


def error_response(
  *,
  code: str,
  message: str,
  details: list[dict[str, Any]] | None = None,
  request_id: str | None = None,
) -> ApiResponse[None]:
  return ApiResponse(
    success=False,
    data=None,
    error=ErrorBody(code=code, message=message, details=details or []),
    meta=ApiMeta(request_id=request_id),
  )
