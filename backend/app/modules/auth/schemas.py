"""Authentication payloads."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.roles import Role
from app.modules.auth.models import User


class LoginRequest(BaseModel):
  model_config = ConfigDict(str_strip_whitespace=True)

  email: EmailStr
  password: str = Field(min_length=1, max_length=128)
  tenant_code: str | None = Field(
    default=None,
    description="College code for college users. Omit for platform super admins.",
  )


class TokenResponse(BaseModel):
  access_token: str
  refresh_token: str
  token_type: str = "bearer"
  expires_in: int


class RefreshRequest(BaseModel):
  refresh_token: str = Field(min_length=10, max_length=512)


class LogoutRequest(BaseModel):
  refresh_token: str | None = Field(default=None, max_length=512)


class UserRead(BaseModel):
  id: str
  email: EmailStr
  full_name: str
  role: Role
  tenant_id: str | None
  department_id: str | None
  is_active: bool
  created_at: datetime

  @classmethod
  def from_document(cls, user: User) -> "UserRead":
    return cls(
      id=str(user.id),
      email=user.email,
      full_name=user.full_name,
      role=user.role,
      tenant_id=str(user.tenant_id) if user.tenant_id else None,
      department_id=str(user.department_id) if user.department_id else None,
      is_active=user.is_active,
      created_at=user.created_at,
    )
