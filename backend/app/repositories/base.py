"""Tenant-scoped repository helpers."""

from typing import Any, TypeVar

from beanie import Document, PydanticObjectId
from beanie.odm.queries.find import FindMany

from app.core.exceptions import AppError

T = TypeVar("T", bound=Document)


class TenantScopedRepository[T: Document]:
  """Base repository enforcing tenant filters on queries."""

  def __init__(self, model: type[T]) -> None:
    self._model = model

  def _tenant_filter(self, tenant_id: PydanticObjectId | None) -> dict[str, Any]:
    if tenant_id is None:
      raise AppError(
        code="TENANT_REQUIRED",
        message="College context is required",
        status_code=403,
      )
    return {"tenant_id": tenant_id}

  def find_for_tenant(self, tenant_id: PydanticObjectId | None) -> FindMany[T]:
    return self._model.find(self._tenant_filter(tenant_id))

  async def get_for_tenant(
    self,
    tenant_id: PydanticObjectId | None,
    document_id: PydanticObjectId,
  ) -> T | None:
    document = await self._model.get(document_id)
    if document is None:
      return None
    if tenant_id is not None and getattr(document, "tenant_id", None) is not None:
      if str(document.tenant_id) != str(tenant_id):
        return None
    return document
