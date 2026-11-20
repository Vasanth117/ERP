"""Institutional policy library and review schedule."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class InstitutionPolicy(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    title: str = Field(max_length=200)
    category: str = Field(max_length=64)
    audience: str = Field(max_length=64)
    version_label: str = Field(max_length=32)
    effective_from: date | None = None
    status: str = Field(max_length=32)
    owner_label: str | None = Field(default=None, max_length=200)
    approved_by_label: str | None = Field(default=None, max_length=300)
    acknowledgement_requirement: str | None = Field(default=None, max_length=200)
    acknowledgement_completed: int | None = Field(default=None, ge=0)
    acknowledgement_required: int | None = Field(default=None, ge=0)
    detail_href: str | None = Field(default=None, max_length=500)
    search_text: str | None = Field(default=None, max_length=500)
    sort_order: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_policies"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING)],
                unique=True,
                name="unique_institution_policy",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="policies_by_status"),
            IndexModel([("tenant_id", ASCENDING), ("category", ASCENDING)], name="policies_by_category"),
        ]


class InstitutionPolicyReview(Document):
    tenant_id: PydanticObjectId
    review_id: str
    policy_id: str | None = None
    title: str = Field(max_length=200)
    subtitle: str = Field(default="", max_length=500)
    status_code: str = Field(max_length=32)
    status_label: str = Field(max_length=64)
    due_date: date | None = None
    sort_order: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_policy_reviews"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("review_id", ASCENDING)],
                unique=True,
                name="unique_institution_policy_review",
            ),
        ]


class InstitutionPolicyAcknowledgement(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    user_id: PydanticObjectId
    acknowledged_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_policy_acknowledgements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_policy_ack",
            ),
        ]