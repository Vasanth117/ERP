"""LMS administration API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.college_admin.lms_admin_models import LmsAccessPolicy


class LmsSettingsRead(BaseModel):
    default_access: LmsAccessPolicy
    allowed_material_types: list[str]
    assignment_late_penalty_cap: float
    quiz_enabled: bool
    moderation_required: bool
    integration_provider_code: str | None
    version: int
    updated_at: datetime


class LmsSettingsUpdate(BaseModel):
    default_access: LmsAccessPolicy | None = None
    allowed_material_types: list[str] | None = None
    assignment_late_penalty_cap: float | None = Field(default=None, ge=0, le=100)
    quiz_enabled: bool | None = None
    moderation_required: bool | None = None
    integration_provider_code: str | None = None


class LmsCourseMappingUpsert(BaseModel):
    course_id: str
    course_code: str
    lms_course_key: str
    department_id: str | None = None
    published: bool = True


class LmsCourseMappingRead(BaseModel):
    course_code: str
    course_id: str
    lms_course_key: str
    department_id: str | None
    published: bool
    updated_at: datetime


class LmsContentCategoryUpsert(BaseModel):
    category_code: str
    title: str
    parent_code: str | None = None
    sort_order: int = 0


class LmsContentCategoryRead(BaseModel):
    category_code: str
    title: str
    parent_code: str | None
    sort_order: int


class LmsPublishingPolicyUpsert(BaseModel):
    policy_code: str = "default"
    material_requires_approval: bool = False
    assignment_publish_window_hours: int = Field(default=168, ge=0)
    allowed_extensions: list[str] | None = None
    max_file_size_bytes: int | None = Field(default=None, ge=1)
    late_submission_allowed: bool | None = None
    late_penalty_percent: float | None = Field(default=None, ge=0, le=100)


class LmsPublishingPolicyRead(BaseModel):
    policy_code: str
    material_requires_approval: bool
    assignment_publish_window_hours: int
    version: int
    updated_at: datetime


class LmsOperationalStats(BaseModel):
    materials_total: int
    materials_published: int
    materials_draft: int
    assignments_total: int
    assignments_published: int
    submissions_total: int
    active_learners: int
    course_mappings: int


class LmsMonitorSummary(BaseModel):
    content_availability: dict[str, int]
    assignment_publication: dict[str, int]
    submission_activity: dict[str, int]
    learning_progress: dict[str, int]


class LmsConfigurationHistoryItem(BaseModel):
    scope: str
    resource_id: str
    version_number: int
    created_at: datetime
    actor_id: str | None