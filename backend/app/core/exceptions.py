"""Application errors with stable API codes."""

from typing import Any


class AppError(Exception):
  """Raised from services; mapped to HTTP responses in main."""

  def __init__(
    self,
    *,
    code: str,
    message: str,
    status_code: int = 400,
    details: list[dict[str, Any]] | None = None,
  ) -> None:
    self.code = code
    self.message = message
    self.status_code = status_code
    self.details = details or []
    super().__init__(message)
