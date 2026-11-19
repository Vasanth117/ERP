"""Marks validation against assessment configuration."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.core.exceptions import AppError
from app.modules.examinations.exam_cell_marks_enums import ExamMarksCandidateStatus
from app.modules.examinations.exam_cell_marks_schemas import ExamMarksComponentInput
from app.modules.examinations.exam_cell_assessment_models import ExamAssessmentComponent, ExamAssessmentConfig


async def load_assessment_components(
    tenant_id: PydanticObjectId, config_id: str
) -> dict[str, ExamAssessmentComponent]:
    rows = await ExamAssessmentComponent.find(
        Eq(ExamAssessmentComponent.tenant_id, tenant_id),
        Eq(ExamAssessmentComponent.config_id, config_id),
    ).to_list()
    return {row.code.strip().upper(): row for row in rows}


async def resolve_assessment_config(
    tenant_id: PydanticObjectId,
    *,
    course_code: str,
    academic_year_label: str,
    semester_label: str,
    programme_code: str | None,
    explicit_config_id: str | None,
) -> ExamAssessmentConfig | None:
    if explicit_config_id:
        cfg = await ExamAssessmentConfig.find_one(
            Eq(ExamAssessmentConfig.tenant_id, tenant_id),
            Eq(ExamAssessmentConfig.config_id, explicit_config_id),
        )
        if cfg is None:
            raise AppError(code="NOT_FOUND", message="Assessment configuration not found", status_code=404)
        return cfg

    filters: dict = {
        "tenant_id": tenant_id,
        "course_code": course_code.strip().upper(),
        "academic_year_label": academic_year_label,
        "semester_label": semester_label,
    }
    if programme_code:
        filters["programme_code"] = programme_code.strip().upper()
    row = await ExamAssessmentConfig.find_one(filters)
    return row


def validate_component_marks(
    payload: ExamMarksComponentInput,
    *,
    candidate_status: ExamMarksCandidateStatus,
    configured: ExamAssessmentComponent | None,
) -> None:
    if candidate_status != ExamMarksCandidateStatus.PRESENT:
        if payload.marks_obtained is not None and payload.marks_obtained > 0:
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Marks cannot be recorded when candidate status is {candidate_status.value}",
                status_code=422,
            )
        return

    max_marks = configured.max_marks if configured is not None else payload.max_marks
    min_marks = payload.min_marks
    if payload.marks_obtained is None:
        return
    if payload.marks_obtained < min_marks:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Marks below minimum for component {payload.component_code}",
            status_code=422,
        )
    if payload.marks_obtained > max_marks:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Marks exceed maximum ({max_marks}) for component {payload.component_code}",
            status_code=422,
        )