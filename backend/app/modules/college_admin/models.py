"""College admin MongoDB collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.college_admin.enums import DashboardDateRange, InstitutionActivityKind
from app.modules.tenants.platform_models import InstitutionAddress


class InstitutionProfile(Document):
    """Extended institution identity (tenant registry remains platform-owned for code/lifecycle)."""

    tenant_id: PydanticObjectId
    legal_name: str
    display_name: str
    institution_code: str | None = None
    secondary_codes: list[str] = Field(default_factory=list)
    institution_email: str | None = None
    contact_phone: str | None = None
    official_website: str | None = Field(default=None, max_length=500)
    address: InstitutionAddress = Field(default_factory=InstitutionAddress)
    institution_type: str | None = None
    affiliation_name: str | None = Field(default=None, max_length=200)
    affiliation_type: str | None = Field(default=None, max_length=64)
    affiliation_id: str | None = Field(default=None, max_length=64)
    primary_campus_id: PydanticObjectId | None = None
    version: int = 1
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_profiles"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_institution_profile_per_tenant"),
            IndexModel(
                [("tenant_id", ASCENDING), ("institution_code", ASCENDING)],
                unique=True,
                name="unique_institution_code_per_tenant",
                partialFilterExpression={"institution_code": {"$type": "string"}},
            ),
        ]


class InstitutionCampus(Document):
    tenant_id: PydanticObjectId
    campus_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    is_main: bool = False
    is_active: bool = True
    address: InstitutionAddress = Field(default_factory=InstitutionAddress)
    contact_email: str | None = Field(default=None, max_length=254)
    contact_phone: str | None = Field(default=None, max_length=32)
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, max_length=16)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "institution_campuses"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("campus_code", ASCENDING)],
                unique=True,
                name="unique_campus_code_per_tenant",
            ),
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], name="campuses_active_by_tenant"),
        ]


class InstitutionSettings(Document):
    tenant_id: PydanticObjectId
    settings: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "institution_settings"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_institution_settings_per_tenant"),
        ]


class InstitutionBranding(Document):
    tenant_id: PydanticObjectId
    display_name: str
    logo_file_id: str | None = None
    favicon_file_id: str | None = None
    primary_color: str = "#1E40AF"
    secondary_color: str = "#64748B"
    theme: dict[str, str] = Field(default_factory=dict)
    version: int = 1
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "institution_branding"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_institution_branding_per_tenant"),
        ]


class InstitutionConfigurationVersion(Document):
    tenant_id: PydanticObjectId
    scope: str
    version_number: int
    snapshot: dict[str, Any] = Field(default_factory=dict)
    changed_keys: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId | None = None

    class Settings:
        name = "institution_configuration_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("scope", ASCENDING), ("version_number", DESCENDING)],
                name="institution_config_versions_by_scope",
            ),
            IndexModel([("created_at", DESCENDING)], expireAfterSeconds=31536000, name="institution_config_ttl"),
        ]


class CollegeDashboardPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    default_date_range: DashboardDateRange = DashboardDateRange.WEEK
    default_department_id: PydanticObjectId | None = None
    default_campus_id: PydanticObjectId | None = None
    default_academic_year_label: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "college_dashboard_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_college_dashboard_prefs",
            ),
        ]


class InstitutionActivityLog(Document):
    tenant_id: PydanticObjectId
    actor_id: PydanticObjectId | None = None
    activity_kind: InstitutionActivityKind
    resource_type: str
    resource_id: str | None = None
    summary: str = Field(max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_activity_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("created_at", DESCENDING)],
                name="institution_activity_by_tenant",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("activity_kind", ASCENDING), ("created_at", DESCENDING)],
                name="institution_activity_by_kind",
            ),
        ]
