"""Recruitment pipeline stage transition rules."""

from app.modules.hr.enums import HrApplicationPipelineStage, TERMINAL_APPLICATION_STAGES

DEFAULT_PIPELINE_STAGES: tuple[HrApplicationPipelineStage, ...] = (
    HrApplicationPipelineStage.APPLICATION_SUBMITTED,
    HrApplicationPipelineStage.INITIAL_SCREENING,
    HrApplicationPipelineStage.UNDER_REVIEW,
    HrApplicationPipelineStage.SHORTLISTED,
    HrApplicationPipelineStage.ASSESSMENT,
    HrApplicationPipelineStage.INTERVIEW_SCHEDULED,
    HrApplicationPipelineStage.INTERVIEW_COMPLETED,
    HrApplicationPipelineStage.FINAL_EVALUATION,
    HrApplicationPipelineStage.SELECTED,
    HrApplicationPipelineStage.OFFER_ISSUED,
    HrApplicationPipelineStage.OFFER_ACCEPTED,
    HrApplicationPipelineStage.OFFER_DECLINED,
    HrApplicationPipelineStage.REJECTED,
    HrApplicationPipelineStage.WITHDRAWN,
    HrApplicationPipelineStage.POSITION_CLOSED,
)

# Allowed forward/side transitions (institution may configure stage list; rules stay consistent).
ALLOWED_STAGE_TRANSITIONS: dict[HrApplicationPipelineStage, frozenset[HrApplicationPipelineStage]] = {
    HrApplicationPipelineStage.APPLICATION_SUBMITTED: frozenset(
        {
            HrApplicationPipelineStage.INITIAL_SCREENING,
            HrApplicationPipelineStage.UNDER_REVIEW,
            HrApplicationPipelineStage.REJECTED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.INITIAL_SCREENING: frozenset(
        {
            HrApplicationPipelineStage.UNDER_REVIEW,
            HrApplicationPipelineStage.SHORTLISTED,
            HrApplicationPipelineStage.REJECTED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.UNDER_REVIEW: frozenset(
        {
            HrApplicationPipelineStage.SHORTLISTED,
            HrApplicationPipelineStage.ASSESSMENT,
            HrApplicationPipelineStage.REJECTED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.SHORTLISTED: frozenset(
        {
            HrApplicationPipelineStage.ASSESSMENT,
            HrApplicationPipelineStage.INTERVIEW_SCHEDULED,
            HrApplicationPipelineStage.FINAL_EVALUATION,
            HrApplicationPipelineStage.REJECTED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.ASSESSMENT: frozenset(
        {
            HrApplicationPipelineStage.INTERVIEW_SCHEDULED,
            HrApplicationPipelineStage.FINAL_EVALUATION,
            HrApplicationPipelineStage.REJECTED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.INTERVIEW_SCHEDULED: frozenset(
        {
            HrApplicationPipelineStage.INTERVIEW_COMPLETED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.INTERVIEW_COMPLETED: frozenset(
        {
            HrApplicationPipelineStage.FINAL_EVALUATION,
            HrApplicationPipelineStage.SELECTED,
            HrApplicationPipelineStage.REJECTED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.FINAL_EVALUATION: frozenset(
        {
            HrApplicationPipelineStage.SELECTED,
            HrApplicationPipelineStage.REJECTED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.SELECTED: frozenset(
        {
            HrApplicationPipelineStage.OFFER_ISSUED,
            HrApplicationPipelineStage.REJECTED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.OFFER_ISSUED: frozenset(
        {
            HrApplicationPipelineStage.OFFER_ACCEPTED,
            HrApplicationPipelineStage.OFFER_DECLINED,
            HrApplicationPipelineStage.WITHDRAWN,
        }
    ),
    HrApplicationPipelineStage.OFFER_ACCEPTED: frozenset(),
    HrApplicationPipelineStage.OFFER_DECLINED: frozenset(),
    HrApplicationPipelineStage.REJECTED: frozenset(),
    HrApplicationPipelineStage.WITHDRAWN: frozenset(),
    HrApplicationPipelineStage.POSITION_CLOSED: frozenset(),
}


def assert_stage_enabled(tenant_stages: list[str] | None, target: HrApplicationPipelineStage) -> None:
    from app.core.exceptions import AppError

    if not tenant_stages:
        return
    if target.value not in tenant_stages:
        raise AppError(code="VALIDATION_ERROR", message=f"Stage {target.value} is disabled for this institution", status_code=422)


def assert_stage_transition(current: HrApplicationPipelineStage, target: HrApplicationPipelineStage) -> None:
    from app.core.exceptions import AppError

    if current in TERMINAL_APPLICATION_STAGES:
        raise AppError(
            code="CONFLICT",
            message=f"Application is in terminal stage {current.value}",
            status_code=409,
        )
    allowed = ALLOWED_STAGE_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Cannot transition from {current.value} to {target.value}",
            status_code=422,
        )