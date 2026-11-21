"""Resolve institutional login identifiers to user emails."""

from __future__ import annotations

import re

from beanie import PydanticObjectId

from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.parents.models import ParentProfile
from app.modules.students.models import StudentProfile


def _looks_like_email(value: str) -> bool:
  return "@" in value


async def resolve_login_email(
  raw_login: str,
  tenant_id: PydanticObjectId | None,
) -> str:
  """Map email or tenant-scoped student/parent id to the user's canonical email."""
  login = raw_login.strip()
  if not login:
    raise AppError(
      code="VALIDATION_ERROR",
      message="Login identifier is required",
      status_code=422,
    )

  if _looks_like_email(login):
    return login.lower()

  if tenant_id is None:
    raise AppError(
      code="TENANT_REQUIRED",
      message=(
        "College context is required for this sign-in. "
        "Use a college code or configure LOGIN_DEFAULT_TENANT_CODE for single-college deployments."
      ),
      status_code=422,
    )

  escaped = re.escape(login.strip())
  student_profile = await StudentProfile.find_one(
    {
      "tenant_id": tenant_id,
      "student_id": {"$regex": f"^{escaped}$", "$options": "i"},
    }
  )
  if student_profile is not None:
    user = await User.get(student_profile.user_id)
    if user is None:
      raise AppError(
        code="INVALID_CREDENTIALS",
        message="Invalid email or password",
        status_code=401,
      )
    return user.email.lower()

  parent_profile = await ParentProfile.find_one(
    {
      "tenant_id": tenant_id,
      "parent_id": {"$regex": f"^{escaped}$", "$options": "i"},
    }
  )
  if parent_profile is not None:
    user = await User.get(parent_profile.user_id)
    if user is None:
      raise AppError(
        code="INVALID_CREDENTIALS",
        message="Invalid email or password",
        status_code=401,
      )
    return user.email.lower()

  raise AppError(
    code="INVALID_CREDENTIALS",
    message="Invalid email or password",
    status_code=401,
  )