"""Application settings loaded from the environment."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  app_env: Literal["development", "test", "production"] = "development"
  app_name: str = "ERP System API"
  api_v1_prefix: str = "/api/v1"
  mongodb_url: str = Field(repr=False)
  mongodb_db_name: str = "erp"
  redis_url: str = "redis://localhost:6379/0"
  rabbitmq_url: str = Field(repr=False)
  jwt_secret: str = Field(repr=False)
  jwt_algorithm: str = "HS256"
  jwt_issuer: str = "erp-system"
  jwt_audience: str = "erp-api"
  access_token_expire_minutes: int = 60
  refresh_token_expire_days: int = 14
  login_rate_limit_per_minute: int = 20
  cors_origins: str = "http://localhost:3000"

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
  )

  @computed_field
  @property
  def cors_origin_list(self) -> list[str]:
    return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

  @model_validator(mode="after")
  def reject_placeholder_secret_in_production(self) -> "Settings":
    placeholder = self.jwt_secret == "dev-only-change-me"
    too_short = len(self.jwt_secret) < 32
    if self.app_env == "production" and (placeholder or too_short):
      raise ValueError("Set a JWT_SECRET of at least 32 characters in production")
    return self


@lru_cache
def get_settings() -> Settings:
  return Settings()
