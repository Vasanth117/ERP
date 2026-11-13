"""Password hashing and JWT access tokens."""

import hashlib
import secrets
from datetime import timedelta
from typing import Any

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status

from app.common.time import utcnow
from app.core.config import get_settings

_argon2 = PasswordHasher(
  time_cost=3,
  memory_cost=65536,
  parallelism=4,
  hash_len=32,
  salt_len=16,
)

DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt()).decode()

CREDENTIALS_ERROR = HTTPException(
  status_code=status.HTTP_401_UNAUTHORIZED,
  detail="Could not validate credentials",
  headers={"WWW-Authenticate": "Bearer"},
)


def hash_password(password: str) -> str:
  return _argon2.hash(password)


def password_needs_upgrade(password_hash: str) -> bool:
  return not password_hash.startswith("$argon2")


def verify_password(password: str, password_hash: str) -> bool:
  if password_hash.startswith("$argon2"):
    try:
      return _argon2.verify(password_hash, password)
    except VerifyMismatchError:
      return False
  try:
    return bcrypt.checkpw(password.encode(), password_hash.encode())
  except ValueError:
    return False


def create_access_token(subject: str, *, extra_claims: dict[str, Any] | None = None) -> str:
  settings = get_settings()
  payload: dict[str, Any] = {
    "sub": subject,
    "iss": settings.jwt_issuer,
    "aud": settings.jwt_audience,
    "exp": utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
    "iat": utcnow(),
  }
  if extra_claims:
    payload.update(extra_claims)
  return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
  settings = get_settings()
  try:
    return jwt.decode(
      token,
      settings.jwt_secret,
      algorithms=[settings.jwt_algorithm],
      audience=settings.jwt_audience,
      issuer=settings.jwt_issuer,
    )
  except jwt.PyJWTError as exc:
    raise CREDENTIALS_ERROR from exc


def new_refresh_token_plaintext() -> str:
  return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
  return hashlib.sha256(token.encode()).hexdigest()
