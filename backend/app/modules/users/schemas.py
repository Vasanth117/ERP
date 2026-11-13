"""User administration payloads."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.roles import Role


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    role: Role
    tenant_id: str | None = None
    department_id: str | None = None
