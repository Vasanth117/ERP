"""Authentication payloads."""

from datetime import datetime

from email_validator import EmailNotValidError, validate_email

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.common.roles import Role
from app.modules.auth.models import User


class LoginRequest(BaseModel):
  model_config = ConfigDict(str_strip_whitespace=True)

  email: str = Field(
    min_length=1,
    max_length=254,
    description="Email address or institutional login id (student id / parent id within a college).",
  )
  password: str = Field(min_length=1, max_length=128)
  tenant_code: str | None = Field(
    default=None,
    description="College code for college users. Omit for platform super admins.",
  )

  @field_validator("email")
  @classmethod
  def validate_email_or_institutional_id(cls, value: str) -> str:
    trimmed = value.strip()
    if not trimmed:
      raise ValueError("Login is required")
    if "@" in trimmed:
      try:
        validate_email(trimmed, check_deliverability=False)
      except EmailNotValidError as exc:
        raise ValueError("Enter a valid email address") from exc
    return trimmed


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
