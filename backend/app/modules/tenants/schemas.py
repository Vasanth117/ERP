"""College and department payloads."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.tenants.models import Department, Tenant


class NameCodeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.upper()


class TenantCreate(NameCodeCreate):
    pass


class DepartmentCreate(NameCodeCreate):
    pass


class TenantRead(BaseModel):
    id: str
    name: str
    code: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_document(cls, tenant: Tenant) -> "TenantRead":
        return cls(
            id=str(tenant.id),
            name=tenant.name,
            code=tenant.code,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
        )


class DepartmentRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_document(cls, department: Department) -> "DepartmentRead":
        return cls(
            id=str(department.id),
            tenant_id=str(department.tenant_id),
            name=department.name,
            code=department.code,
            is_active=department.is_active,
            created_at=department.created_at,
        )
