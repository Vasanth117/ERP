"""Performance cycles, goals, reviews, feedback, PIPs and development plans."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import (
    HrDevelopmentPlanStatus,
    HrPerformanceCycleStatus,
    HrPerformanceGoalStatus,
    HrPerformancePipStatus,
    HrPerformanceReviewStatus,
)


class HrPerformanceCycle(Document):
    tenant_id: PydanticObjectId
    cycle_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    cycle_kind: str = Field(max_length=32)
    start_date: date
    end_date: date
    eligible_categories: list[str] = Field(default_factory=list)
    review_stages: list[str] = Field(default_factory=lambda: ["self_assessment", "manager_review", "hr_review"])
    rating_scale: dict[str, Any] = Field(default_factory=dict)
    criteria: list[dict[str, Any]] = Field(default_factory=list)
    approval_rules: dict[str, Any] = Field(default_factory=dict)
    deadlines: dict[str, date] = Field(default_factory=dict)
    status: HrPerformanceCycleStatus = HrPerformanceCycleStatus.DRAFT
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_performance_cycles"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("cycle_code", ASCENDING)], unique=True, name="unique_perf_cycle"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="perf_cycles_status"),
        ]


class HrPerformanceCriteria(Document):
    tenant_id: PydanticObjectId
    cycle_id: PydanticObjectId
    criteria_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    weight: str = "0"
    description: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_performance_criteria"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("cycle_id", ASCENDING), ("criteria_code", ASCENDING)],
                unique=True,
                name="unique_perf_criteria",
            ),
        ]


class EmployeePerformanceGoal(Document):
    tenant_id: PydanticObjectId
    cycle_id: PydanticObjectId | None = None
    employee_user_id: PydanticObjectId
    goal_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    goal_kind: str = Field(default="individual", max_length=64)
    department_id: PydanticObjectId | None = None
    measurement: str | None = None
    target_value: str | None = None
    priority: str = "medium"
    due_date: date | None = None
    reviewer_user_id: PydanticObjectId | None = None
    progress_percent: int = 0
    evidence_refs: list[str] = Field(default_factory=list)
    status: HrPerformanceGoalStatus = HrPerformanceGoalStatus.DRAFT
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_performance_goals"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("goal_code", ASCENDING)], name="perf_goals_employee"),
            IndexModel([("tenant_id", ASCENDING), ("cycle_id", ASCENDING)], name="perf_goals_cycle"),
        ]


class EmployeePerformanceReview(Document):
    tenant_id: PydanticObjectId
    cycle_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    manager_user_id: PydanticObjectId | None = None
    status: HrPerformanceReviewStatus = HrPerformanceReviewStatus.NOT_STARTED
    self_assessment: dict[str, Any] = Field(default_factory=dict)
    manager_assessment: dict[str, Any] = Field(default_factory=dict)
    hr_assessment: dict[str, Any] = Field(default_factory=dict)
    overall_rating: str | None = None
    weighted_scores: dict[str, str] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    finalized_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_performance_reviews"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("cycle_id", ASCENDING), ("employee_user_id", ASCENDING)],
                unique=True,
                name="unique_perf_review_per_cycle",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="perf_reviews_status"),
        ]


class EmployeePerformanceFeedback(Document):
    tenant_id: PydanticObjectId
    review_id: PydanticObjectId | None = None
    goal_id: PydanticObjectId | None = None
    author_user_id: PydanticObjectId
    recipient_user_id: PydanticObjectId
    feedback_text: str = Field(max_length=4000)
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    training_recommendations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_performance_feedback"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("recipient_user_id", ASCENDING), ("created_at", DESCENDING)], name="perf_feedback_recipient"),
        ]


class EmployeePerformanceImprovementPlan(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    review_id: PydanticObjectId | None = None
    title: str = Field(max_length=200)
    improvement_areas: list[str] = Field(default_factory=list)
    expectations: list[dict[str, Any]] = Field(default_factory=list)
    action_steps: list[dict[str, Any]] = Field(default_factory=list)
    manager_user_id: PydanticObjectId | None = None
    review_dates: list[date] = Field(default_factory=list)
    progress_notes: list[dict[str, Any]] = Field(default_factory=list)
    outcome: str | None = Field(default=None, max_length=2000)
    status: HrPerformancePipStatus = HrPerformancePipStatus.DRAFT
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_performance_improvement_plans"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("status", ASCENDING)], name="perf_pip_employee"),
        ]


class EmployeeDevelopmentPlan(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    review_id: PydanticObjectId | None = None
    skill_gaps: list[str] = Field(default_factory=list)
    training_requirements: list[str] = Field(default_factory=list)
    activities: list[dict[str, Any]] = Field(default_factory=list)
    mentor_user_id: PydanticObjectId | None = None
    deadlines: dict[str, date] = Field(default_factory=dict)
    progress: dict[str, Any] = Field(default_factory=dict)
    status: HrDevelopmentPlanStatus = HrDevelopmentPlanStatus.DRAFT
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "employee_development_plans"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("employee_user_id", ASCENDING)], name="development_plans_employee"),
        ]