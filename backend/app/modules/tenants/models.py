"""Colleges and departments."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.tenants.enums import TenantLifecycleStatus, TenantOperationalStatus
from app.modules.tenants.platform_models import AcademicSettings, InstitutionAddress


class Tenant(Document):
    name: str
    code: str
    status: TenantOperationalStatus = TenantOperationalStatus.ACTIVE
    lifecycle_status: TenantLifecycleStatus = TenantLifecycleStatus.ACTIVE
    is_active: bool = True
    institution_email: str | None = None
    contact_phone: str | None = None
    address: InstitutionAddress = Field(default_factory=InstitutionAddress)
    institution_type: str | None = None
    timezone: str = "UTC"
    locale: str = "en-US"
    academic_settings: AcademicSettings = Field(default_factory=AcademicSettings)
    primary_domain: str | None = None
    activated_at: datetime | None = None
    suspended_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenants"
        indexes = [
            IndexModel([("code", ASCENDING)], unique=True, name="unique_tenant_code"),
            IndexModel([("status", ASCENDING), ("created_at", DESCENDING)], name="tenants_by_status"),
            IndexModel(
                [("lifecycle_status", ASCENDING), ("created_at", DESCENDING)],
                name="tenants_by_lifecycle_status",
            ),
            IndexModel([("created_at", DESCENDING)], name="tenants_by_created"),
            IndexModel([("activated_at", DESCENDING)], name="tenants_by_activated"),
        ]


class Department(Document):
    tenant_id: PydanticObjectId
    name: str
    code: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "departments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("code", ASCENDING)],
                unique=True,
                name="unique_department_code_per_tenant",
            ),
        ]
