"""Pure grading / GPA calculation helpers (policy-driven)."""

from math import ceil, floor

from app.modules.examinations.exam_cell_assessment_enums import ExamMarkRoundingMode
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultOutcome
from app.modules.examinations.exam_cell_grading_models import ExamGradeBoundary, ExamGradingPolicy
from app.modules.examinations.exam_cell_marks_enums import ExamMarksCandidateStatus


def round_value(value: float, mode: ExamMarkRoundingMode, precision: int) -> float:
    factor = 10**precision
    scaled = value * factor
    if mode == ExamMarkRoundingMode.CEILING:
        scaled = ceil(scaled)
    elif mode == ExamMarkRoundingMode.FLOOR:
        scaled = floor(scaled)
    elif mode == ExamMarkRoundingMode.HALF:
        scaled = floor(scaled + 0.5)
    else:
        scaled = round(scaled)
    return scaled / factor


def percentage_from_marks(marks: float | None, max_marks: float | None) -> float | None:
    if marks is None or max_marks is None or max_marks <= 0:
        return None
    return (marks / max_marks) * 100.0


def resolve_boundary(
    percent: float,
    boundaries: list[ExamGradeBoundary],
) -> ExamGradeBoundary | None:
    ordered = sorted(boundaries, key=lambda b: b.sort_order)
    for boundary in ordered:
        if boundary.min_percent <= percent <= boundary.max_percent:
            return boundary
    return None


def outcome_from_candidate_status(status: ExamMarksCandidateStatus) -> ExamSubjectResultOutcome | None:
    mapping = {
        ExamMarksCandidateStatus.ABSENT: ExamSubjectResultOutcome.ABSENT,
        ExamMarksCandidateStatus.MALPRACTICE: ExamSubjectResultOutcome.MALPRACTICE,
        ExamMarksCandidateStatus.WITHHELD: ExamSubjectResultOutcome.WITHHELD,
        ExamMarksCandidateStatus.EXEMPTED: ExamSubjectResultOutcome.EXEMPTED,
    }
    return mapping.get(status)


def credits_earned_for_outcome(
    outcome: ExamSubjectResultOutcome,
    *,
    credit_units: float,
    grade_point: float | None,
    policy: ExamGradingPolicy,
) -> float:
    if outcome == ExamSubjectResultOutcome.PASS:
        return credit_units
    if outcome == ExamSubjectResultOutcome.EXEMPTED:
        return credit_units
    if grade_point is not None and grade_point >= policy.min_grade_point_to_pass:
        return credit_units
    return 0.0


def compute_gpa(terms: list[tuple[float, float, float]]) -> tuple[float, float, float, float]:
    """Each term: (credit_units, grade_point, credits_earned). Returns attempted, earned, qp, gpa."""
    credits_attempted = sum(t[0] for t in terms)
    credits_earned = sum(t[2] for t in terms)
    quality_points = sum(t[0] * t[1] for t in terms if t[1] is not None)
    gpa = (quality_points / credits_attempted) if credits_attempted > 0 else 0.0
    return credits_attempted, credits_earned, quality_points, gpa


def apply_supplementary_cap(
    grade_point: float,
    policy: ExamGradingPolicy,
    *,
    is_supplementary: bool,
) -> float:
    if not is_supplementary:
        return grade_point
    cap = policy.supplementary_rules.get("max_grade_point")
    if cap is None:
        return grade_point
    return min(grade_point, float(cap))