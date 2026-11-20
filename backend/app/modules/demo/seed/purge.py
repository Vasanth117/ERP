"""Remove all data owned by a tenant (for demo re-seed)."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.core.database import document_models
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant


async def purge_tenant_completely(tenant_id: PydanticObjectId) -> None:
    """Delete tenant-scoped documents and the tenant record."""
    for model in document_models():
        if model is Tenant:
            continue
        fields = getattr(model, "model_fields", {})
        if "tenant_id" not in fields:
            continue
        await model.find(Eq(model.tenant_id, tenant_id)).delete()
    await User.find(Eq(User.tenant_id, tenant_id)).delete()
    tenant = await Tenant.get(tenant_id)
    if tenant is not None:
        await tenant.delete()