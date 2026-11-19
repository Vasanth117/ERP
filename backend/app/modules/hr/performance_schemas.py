"""Performance management API schemas."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrPerformanceCycleStatus, HrPerformanceGoalStatus, HrPerformanceReviewStatus
from app.modules.hr.performance_models import EmployeePerformanceGoal, EmployeePerformanceReview, HrPerformanceCycle


class PerformanceCycleUpsert(BaseModel):
    cycle_code: str
    title: str
    cycle_kind: str = "annual"
    start_date: date
    end_date: date
    eligible_categories: list[str] = Field(default_factory=list)
    review_stages: list[str] = Field(default_factory=lambda: ["self_assessment", "manager_review", "hr_review"])
    rating_scale: dict[str, Any] = Field(default_factory=dict)
    criteria: list[dict[str, Any]] = Field(default_factory=list)
    approval_rules: dict[str, Any] = Field(default_factory=dict)
    deadlines: dict[str, date] = Field(default_factory=dict)
    status: HrPerformanceCycleStatus = HrPerformanceCycleStatus.DRAFT


class PerformanceCycleRead(BaseModel):
    id: str
    cycle_code: str
    title: str
    status: str

    @classmethod
    def from_doc(cls, doc: HrPerformanceCycle) -> "PerformanceCycleRead":
        return cls(id=str(doc.id), cycle_code=doc.cycle_code, title=doc.title, status=doc.status.value)


class PerformanceGoalCreate(BaseModel):
    employee_user_id: str
    cycle_id: str | None = None
    goal_code: str
    title: str
    description: str | None = None
    goal_kind: str = "individual"
    due_date: date | None = None
    target_value: str | None = None
    reviewer_user_id: str | None = None


class PerformanceGoalProgress(BaseModel):
    progress_percent: int = Field(ge=0, le=100)
    evidence_refs: list[str] = Field(default_factory=list)


class PerformanceGoalRead(BaseModel):
    id: str
    employee_user_id: str
    title: str
    status: HrPerformanceGoalStatus

    @classmethod
    def from_doc(cls, doc: EmployeePerformanceGoal) -> "PerformanceGoalRead":
        return cls(id=str(doc.id), employee_user_id=str(doc.employee_user_id), title=doc.title, status=doc.status)


class PerformanceSelfAssessment(BaseModel):
    achievements: str | None = None
    challenges: str | None = None
    training_needs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    responses: dict[str, Any] = Field(default_factory=dict)


class PerformanceManagerAssessment(BaseModel):
    rating: str | None = None
    feedback: str | None = None
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    training_recommendations: list[str] = Field(default_factory=list)
    weighted_scores: dict[str, str] = Field(default_factory=dict)


class PerformanceHrAction(BaseModel):
    action: str = Field(pattern="^(return|finalize)$")
    note: str | None = None
    overall_rating: str | None = None


class PerformanceReviewRead(BaseModel):
    id: str
    cycle_id: str
    employee_user_id: str
    status: HrPerformanceReviewStatus
    overall_rating: str | None

    @classmethod
    def from_doc(cls, doc: EmployeePerformanceReview) -> "PerformanceReviewRead":
        return cls(
            id=str(doc.id),
            cycle_id=str(doc.cycle_id),
            employee_user_id=str(doc.employee_user_id),
            status=doc.status,
            overall_rating=doc.overall_rating,
        )


class PipCreate(BaseModel):
    employee_user_id: str
    title: str
    improvement_areas: list[str] = Field(default_factory=list)
    expectations: list[dict[str, Any]] = Field(default_factory=list)
    action_steps: list[dict[str, Any]] = Field(default_factory=list)
    manager_user_id: str | None = None
    review_dates: list[date] = Field(default_factory=list)


class DevelopmentPlanUpsert(BaseModel):
    employee_user_id: str
    review_id: str | None = None
    skill_gaps: list[str] = Field(default_factory=list)
    training_requirements: list[str] = Field(default_factory=list)
    activities: list[dict[str, Any]] = Field(default_factory=list)
    mentor_user_id: str | None = None
    deadlines: dict[str, date] = Field(default_factory=dict)