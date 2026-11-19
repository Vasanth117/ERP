"""Examination cell — assessment configuration service."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_assessment_enums import ExamAssessmentConfigStatus
from app.modules.examinations.exam_cell_assessment_models import (
    ExamAssessmentComponent,
    ExamAssessmentConfig,
    ExamAssessmentPolicyVersion,
)
from app.modules.examinations.exam_cell_assessment_schemas import (
    ExamAssessmentConfigCreate,
    ExamAssessmentConfigRead,
    ExamAssessmentConfigUpdate,
    ExamAssessmentPolicyVersionRead,
)
from app.modules.examinations.exam_cell_assessment_validation import (
    component_kind_flags,
    validate_assessment_components,
    validate_theory_practical_rules,
)
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_assessment_manage,
    require_examination_cell_tenant,
)
from app.modules.students.curriculum_models import SubjectCatalogReference


def _config_id() -> str:
    return f"eac_{uuid4().hex[:10]}"


def _component_id() -> str:
    return f"cmp_{uuid4().hex[:8]}"


async def _load_components(tenant_id: PydanticObjectId, config_id: str) -> list[ExamAssessmentComponent]:
    return await ExamAssessmentComponent.find(
        Eq(ExamAssessmentComponent.tenant_id, tenant_id),
        Eq(ExamAssessmentComponent.config_id, config_id),
    ).to_list()


async def _assert_subject_if_present(
    tenant_id: PydanticObjectId,
    *,
    subject_code: str | None,
    programme_code: str | None,
    academic_year_label: str,
    semester_label: str,
    course_code: str | None,
) -> None:
    if not subject_code:
        return
    filters: dict = {
        "tenant_id": tenant_id,
        "subject_code": subject_code.strip().upper(),
        "academic_year_label": academic_year_label,
        "semester_label": semester_label,
    }
    if programme_code:
        filters["programme_code"] = programme_code.strip().upper()
    row = await SubjectCatalogReference.find_one(filters)
    if row is None:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Subject {subject_code} is not in the academic catalogue for the given scope",
            status_code=422,
        )


async def _save_policy_version(
    tenant_id: PydanticObjectId,
    config: ExamAssessmentConfig,
    components: list[ExamAssessmentComponent],
    *,
    actor_id: PydanticObjectId | None,
    change_summary: str | None,
) -> None:
    await ExamAssessmentPolicyVersion(
        tenant_id=tenant_id,
        config_id=config.config_id,
        version_number=config.version,
        snapshot={
            "config": config.model_dump(mode="json"),
            "components": [c.model_dump(mode="json") for c in components],
        },
        change_summary=change_summary,
        created_by=actor_id,
    ).insert()


async def _replace_components(
    tenant_id: PydanticObjectId,
    config_id: str,
    components_input,
) -> list[ExamAssessmentComponent]:
    await ExamAssessmentComponent.find(
        Eq(ExamAssessmentComponent.tenant_id, tenant_id),
        Eq(ExamAssessmentComponent.config_id, config_id),
    ).delete()
    stored: list[ExamAssessmentComponent] = []
    for comp in components_input:
        row = ExamAssessmentComponent(
            tenant_id=tenant_id,
            config_id=config_id,
            component_id=_component_id(),
            code=comp.code,
            name=comp.name,
            assessment_type=comp.assessment_type,
            max_marks=comp.max_marks,
            weight_percent=comp.weight_percent,
            passing_marks=comp.passing_marks,
            contributes_to_final=comp.contributes_to_final,
            sort_order=comp.sort_order,
            metadata=dict(comp.metadata),
        )
        await row.insert()
        stored.append(row)
    return stored


async def create_assessment_config(
    scope: AccessScope,
    user: User,
    payload: ExamAssessmentConfigCreate,
) -> ExamAssessmentConfigRead:
    authorize_examination_cell_assessment_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    code = payload.config_code.strip().upper()
    if await ExamAssessmentConfig.find_one(Eq(ExamAssessmentConfig.tenant_id, tenant_id), Eq(ExamAssessmentConfig.config_code, code)):
        raise AppError(code="DUPLICATE_CONFIG_CODE", message="Assessment config code already exists", status_code=409)
    validate_assessment_components(payload.components)
    has_theory, has_practical = component_kind_flags(payload.components)
    validate_theory_practical_rules(
        theory_rules=payload.theory_rules,
        practical_rules=payload.practical_rules,
        has_theory=has_theory,
        has_practical=has_practical,
    )
    await _assert_subject_if_present(
        tenant_id,
        subject_code=payload.subject_code,
        programme_code=payload.programme_code,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        course_code=payload.course_code,
    )
    config_id = _config_id()
    doc = ExamAssessmentConfig(
        tenant_id=tenant_id,
        config_id=config_id,
        config_code=code,
        title=payload.title.strip(),
        programme_code=payload.programme_code,
        semester_label=payload.semester_label.strip(),
        academic_year_label=payload.academic_year_label.strip(),
        course_code=payload.course_code,
        subject_code=payload.subject_code,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        passing_marks_percent=payload.passing_marks_percent,
        minimum_eligibility_percent=payload.minimum_eligibility_percent,
        attendance_eligibility_percent=payload.attendance_eligibility_percent,
        mark_rounding=payload.mark_rounding,
        decimal_precision=payload.decimal_precision,
        theory_rules=dict(payload.theory_rules),
        practical_rules=dict(payload.practical_rules),
        internal_calculation_rules=dict(payload.internal_calculation_rules),
        created_by=user.id,
        updated_by=user.id,
    )
    await doc.insert()
    components = await _replace_components(tenant_id, config_id, payload.components)
    await _save_policy_version(tenant_id, doc, components, actor_id=user.id, change_summary="Initial configuration")
    await record_exam_activity(
        tenant_id,
        actor_id=user.id,
        action="exam_assessment_config.created",
        summary=f"Created assessment configuration {code}",
        metadata={"config_id": config_id},
    )
    return ExamAssessmentConfigRead.from_documents(doc, components)


async def update_assessment_config(
    scope: AccessScope,
    user: User,
    config_oid: PydanticObjectId,
    payload: ExamAssessmentConfigUpdate,
) -> ExamAssessmentConfigRead:
    authorize_examination_cell_assessment_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamAssessmentConfig.find_one(Eq(ExamAssessmentConfig.tenant_id, tenant_id), Eq(ExamAssessmentConfig.id, config_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Assessment configuration not found", status_code=404)
    if doc.status == ExamAssessmentConfigStatus.ARCHIVED:
        raise AppError(code="CONFIG_ARCHIVED", message="Archived configurations cannot be edited", status_code=409)
    components = await _load_components(tenant_id, doc.config_id)
    if payload.components is not None:
        validate_assessment_components(payload.components)
        has_theory, has_practical = component_kind_flags(payload.components)
        validate_theory_practical_rules(
            theory_rules=payload.theory_rules or doc.theory_rules,
            practical_rules=payload.practical_rules or doc.practical_rules,
            has_theory=has_theory,
            has_practical=has_practical,
        )
        components = await _replace_components(tenant_id, doc.config_id, payload.components)
    if payload.title is not None:
        doc.title = payload.title.strip()
    if payload.effective_from is not None:
        doc.effective_from = payload.effective_from
    if payload.effective_to is not None:
        doc.effective_to = payload.effective_to
    if payload.passing_marks_percent is not None:
        doc.passing_marks_percent = payload.passing_marks_percent
    if payload.minimum_eligibility_percent is not None:
        doc.minimum_eligibility_percent = payload.minimum_eligibility_percent
    if payload.attendance_eligibility_percent is not None:
        doc.attendance_eligibility_percent = payload.attendance_eligibility_percent
    if payload.mark_rounding is not None:
        doc.mark_rounding = payload.mark_rounding
    if payload.decimal_precision is not None:
        doc.decimal_precision = payload.decimal_precision
    if payload.theory_rules is not None:
        doc.theory_rules = dict(payload.theory_rules)
    if payload.practical_rules is not None:
        doc.practical_rules = dict(payload.practical_rules)
    if payload.internal_calculation_rules is not None:
        doc.internal_calculation_rules = dict(payload.internal_calculation_rules)
    doc.version += 1
    doc.updated_by = user.id
    doc.updated_at = utcnow()
    await doc.save()
    await _save_policy_version(tenant_id, doc, components, actor_id=user.id, change_summary="Configuration updated")
    await record_exam_activity(
        tenant_id,
        actor_id=user.id,
        action="exam_assessment_config.updated",
        summary=f"Updated assessment configuration {doc.config_code}",
        metadata={"config_id": doc.config_id, "version": doc.version},
    )
    return ExamAssessmentConfigRead.from_documents(doc, components)


async def activate_assessment_config(scope: AccessScope, user: User, config_oid: PydanticObjectId) -> ExamAssessmentConfigRead:
    authorize_examination_cell_assessment_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamAssessmentConfig.find_one(Eq(ExamAssessmentConfig.tenant_id, tenant_id), Eq(ExamAssessmentConfig.id, config_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Assessment configuration not found", status_code=404)
    previous_active = await ExamAssessmentConfig.find(
        {
            "tenant_id": tenant_id,
            "status": ExamAssessmentConfigStatus.ACTIVE.value,
            "programme_code": doc.programme_code,
            "semester_label": doc.semester_label,
            "course_code": doc.course_code,
            "config_code": {"$ne": doc.config_code},
        }
    ).to_list()
    for row in previous_active:
        row.status = ExamAssessmentConfigStatus.SUPERSEDED
        row.updated_at = utcnow()
        await row.save()
    doc.status = ExamAssessmentConfigStatus.ACTIVE
    doc.updated_by = user.id
    doc.updated_at = utcnow()
    await doc.save()
    components = await _load_components(tenant_id, doc.config_id)
    return ExamAssessmentConfigRead.from_documents(doc, components)


async def get_assessment_config(scope: AccessScope, config_oid: PydanticObjectId) -> ExamAssessmentConfigRead:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamAssessmentConfig.find_one(Eq(ExamAssessmentConfig.tenant_id, tenant_id), Eq(ExamAssessmentConfig.id, config_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Assessment configuration not found", status_code=404)
    components = await _load_components(tenant_id, doc.config_id)
    return ExamAssessmentConfigRead.from_documents(doc, components)


async def list_assessment_configs(
    scope: AccessScope,
    *,
    programme_code: str | None,
    semester_label: str | None,
    pagination: Pagination,
) -> Page[ExamAssessmentConfigRead]:
    tenant_id = require_examination_cell_tenant(scope)
    query: dict = {"tenant_id": tenant_id}
    if programme_code:
        query["programme_code"] = programme_code.strip().upper()
    if semester_label:
        query["semester_label"] = semester_label.strip()
    rows = await ExamAssessmentConfig.find(query).sort("-updated_at").skip(pagination.offset).limit(pagination.limit).to_list()
    total = await ExamAssessmentConfig.find(query).count()
    items: list[ExamAssessmentConfigRead] = []
    for row in rows:
        components = await _load_components(tenant_id, row.config_id)
        items.append(ExamAssessmentConfigRead.from_documents(row, components))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def list_assessment_policy_versions(
    scope: AccessScope,
    config_oid: PydanticObjectId,
) -> list[ExamAssessmentPolicyVersionRead]:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamAssessmentConfig.find_one(Eq(ExamAssessmentConfig.tenant_id, tenant_id), Eq(ExamAssessmentConfig.id, config_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Assessment configuration not found", status_code=404)
    rows = await ExamAssessmentPolicyVersion.find(
        Eq(ExamAssessmentPolicyVersion.tenant_id, tenant_id),
        Eq(ExamAssessmentPolicyVersion.config_id, doc.config_id),
    ).sort("-version_number").to_list()
    return [
        ExamAssessmentPolicyVersionRead(
            config_id=r.config_id,
            version_number=r.version_number,
            change_summary=r.change_summary,
            created_at=r.created_at,
        )
        for r in rows
    ]