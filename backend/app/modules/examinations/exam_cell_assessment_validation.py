"""Assessment configuration validation."""

from app.core.exceptions import AppError
from app.modules.examinations.exam_cell_assessment_enums import ExamAssessmentComponentKind
from app.modules.examinations.exam_cell_assessment_schemas import ExamAssessmentComponentInput


_WEIGHT_TOLERANCE = 0.05


def validate_assessment_components(components: list[ExamAssessmentComponentInput]) -> None:
    if not components:
        raise AppError(code="VALIDATION_ERROR", message="At least one assessment component is required", status_code=422)
    codes: set[str] = set()
    total_weight = 0.0
    for comp in components:
        normalized = comp.code.strip().upper()
        if normalized in codes:
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Duplicate component code {normalized}",
                status_code=422,
            )
        codes.add(normalized)
        if comp.max_marks <= 0:
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Component {normalized} must have positive max marks",
                status_code=422,
            )
        if comp.passing_marks is not None and comp.passing_marks > comp.max_marks:
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Passing marks exceed max marks for component {normalized}",
                status_code=422,
            )
        if comp.contributes_to_final:
            total_weight += comp.weight_percent
    if abs(total_weight - 100.0) > _WEIGHT_TOLERANCE:
        raise AppError(
            code="WEIGHTAGE_MISMATCH",
            message=f"Contributing component weights must sum to 100 (got {total_weight:.2f})",
            status_code=422,
        )


def validate_theory_practical_rules(
    *,
    theory_rules: dict,
    practical_rules: dict,
    has_theory: bool,
    has_practical: bool,
) -> None:
    if has_theory and theory_rules.get("enabled") and theory_rules.get("minimum_marks") is not None:
        minimum = float(theory_rules["minimum_marks"])
        if minimum < 0:
            raise AppError(code="VALIDATION_ERROR", message="Theory minimum marks cannot be negative", status_code=422)
    if has_practical and practical_rules.get("enabled") and practical_rules.get("minimum_marks") is not None:
        minimum = float(practical_rules["minimum_marks"])
        if minimum < 0:
            raise AppError(code="VALIDATION_ERROR", message="Practical minimum marks cannot be negative", status_code=422)


def component_kind_flags(components: list[ExamAssessmentComponentInput]) -> tuple[bool, bool]:
    has_theory = any(
        c.assessment_type in {ExamAssessmentComponentKind.THEORY, ExamAssessmentComponentKind.END_SEMESTER}
        for c in components
    )
    has_practical = any(
        c.assessment_type in {ExamAssessmentComponentKind.PRACTICAL, ExamAssessmentComponentKind.LABORATORY}
        for c in components
    )
    return has_theory, has_practical