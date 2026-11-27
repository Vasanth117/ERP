"""Internal & external assessment page (CA 09.08)."""

from __future__ import annotations

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.exam_registration_management_page_service import _select_session
from app.modules.college_admin.examination_marks_assessment_nav import examination_marks_assessment_sub_nav
from app.modules.college_admin.examination_workflow import empty_state_for_step, workflow_chrome, workflow_href_after
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InternalExternalAssessmentComponentRow,
    InternalExternalAssessmentPageRead,
    InternalExternalAssessmentSavePayload,
    StudentAdminDashboardFilterOption,
)
from app.modules.examinations.exam_cell_assessment_enums import (
    ExamAssessmentComponentKind,
    ExamAssessmentConfigStatus,
)
from app.modules.examinations.exam_cell_assessment_models import ExamAssessmentComponent, ExamAssessmentConfig
from app.modules.examinations.exam_cell_assessment_schemas import ExamAssessmentConfigUpdate
from app.modules.examinations.exam_cell_assessment_service import update_assessment_config
from app.modules.examinations.exam_cell_models import ExamSession

_MODERATION_OPTIONS = [
    ("5", "±5 marks"),
    ("3", "±3 marks"),
    ("0", "No moderation"),
]
_PASS_MARK_OPTIONS = [
    ("40", "40%"),
    ("35", "35%"),
    ("45", "45%"),
]


def _source_label(comp: ExamAssessmentComponent) -> str:
    meta = comp.metadata or {}
    if label := meta.get("source_label"):
        return str(label)
    if meta.get("source") == "lms":
        return "LMS"
    if comp.assessment_type in (
        ExamAssessmentComponentKind.END_SEMESTER,
        ExamAssessmentComponentKind.THEORY,
    ):
        return "Exam Cell"
    if comp.assessment_type in (
        ExamAssessmentComponentKind.INTERNAL,
        ExamAssessmentComponentKind.CIA,
        ExamAssessmentComponentKind.MODEL_EXAM,
    ):
        return "Faculty"
    return "Faculty"


async def _resolve_config(tenant_id: PydanticObjectId, session: ExamSession) -> ExamAssessmentConfig | None:
    scope = {
        "tenant_id": tenant_id,
        "academic_year_label": session.academic_year_label,
        "semester_label": session.semester_label,
        "status": {
            "$in": [ExamAssessmentConfigStatus.ACTIVE.value, ExamAssessmentConfigStatus.DRAFT.value],
        },
    }
    programme_wide = await ExamAssessmentConfig.find_one({**scope, "course_code": None})
    if programme_wide is not None:
        return programme_wide
    return await ExamAssessmentConfig.find_one(scope)


def _moderation_label(rules: dict) -> str:
    raw = rules.get("moderation_range_marks")
    if raw is None:
        raw = rules.get("moderation_range")
    if raw is None:
        return "±5 marks"
    key = str(int(float(raw))) if str(raw).replace(".", "").isdigit() else str(raw)
    for value, label in _MODERATION_OPTIONS:
        if value == key:
            return label
    return f"±{raw} marks"


def _pass_mark_label(percent: float) -> str:
    key = str(int(round(percent)))
    for value, label in _PASS_MARK_OPTIONS:
        if value == key:
            return label
    return f"{int(round(percent))}%"


async def get_internal_external_assessment_page(
    scope: AccessScope,
    *,
    session_id: str | None = None,
) -> InternalExternalAssessmentPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-registration_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)
    empty_chrome = workflow_chrome("configure_subjects", session_id)
    empty = InternalExternalAssessmentPageRead(
        page_title="Internal & External Assessment",
        page_subtitle="Weightage and moderation",
        **empty_chrome,  # type: ignore[arg-type]
        save_label="Save draft",
        sub_nav=examination_marks_assessment_sub_nav("internal-external-assessment"),
        assessment_pattern_section_title="Assessment pattern",
        moderation_section_title="Moderation",
        table_headers=["Component", "Weight", "Max marks", "Source"],
        component_rows=[],
        total_weight_label="Total 0%",
        moderation_range_label="Moderation range",
        pass_mark_label="Pass mark (external)",
        selected_moderation_range="5",
        selected_pass_mark_percent="40",
        moderation_range_options=[StudentAdminDashboardFilterOption(value=v, label=l) for v, l in _MODERATION_OPTIONS],
        pass_mark_options=[StudentAdminDashboardFilterOption(value=v, label=l) for v, l in _PASS_MARK_OPTIONS],
        selected_config_id="",
        selected_session_id="",
        footer_disclaimer="Live institutional data · Assessment configuration · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )
    if session is None:
        return empty

    chrome = workflow_chrome("configure_subjects", session.session_id)
    page_subtitle = f"Configure subjects · {session.name}"

    config = await _resolve_config(tenant_id, session)
    if config is None:
        return empty.model_copy(
            update={
                "selected_session_id": session.session_id,
                "page_subtitle": page_subtitle,
                **chrome,
                "save_label": chrome["save_draft_label"],
                "panel_empty_state": empty_state_for_step("configure_subjects", session.session_id),
            }
        )

    components = await ExamAssessmentComponent.find(
        Eq(ExamAssessmentComponent.tenant_id, tenant_id),
        Eq(ExamAssessmentComponent.config_id, config.config_id),
    ).sort("+sort_order").to_list()

    rows = [
        InternalExternalAssessmentComponentRow(
            component_id=comp.component_id,
            component_label=comp.name,
            weight_label=f"{int(comp.weight_percent)}%",
            max_marks_label=str(int(comp.max_marks) if comp.max_marks == int(comp.max_marks) else comp.max_marks),
            source_label=_source_label(comp),
        )
        for comp in components
    ]
    total_weight = sum(c.weight_percent for c in components)
    rules = dict(config.theory_rules or {})
    mod_key = str(int(float(rules.get("moderation_range_marks", rules.get("moderation_range", 5)))))
    pass_key = str(int(round(config.passing_marks_percent)))

    panel_empty = empty_state_for_step("configure_subjects", session.session_id) if not rows else None
    return InternalExternalAssessmentPageRead(
        page_title="Internal & External Assessment",
        page_subtitle=page_subtitle,
        panel_empty_state=panel_empty,
        **chrome,  # type: ignore[arg-type]
        save_label=str(chrome["save_draft_label"]),
        sub_nav=examination_marks_assessment_sub_nav("internal-external-assessment"),
        assessment_pattern_section_title="Assessment pattern",
        moderation_section_title="Moderation",
        table_headers=["Component", "Weight", "Max marks", "Source"],
        component_rows=rows,
        total_weight_label=f"Total {int(round(total_weight))}%",
        moderation_range_label="Moderation range",
        pass_mark_label="Pass mark (external)",
        selected_moderation_range=mod_key if any(v == mod_key for v, _ in _MODERATION_OPTIONS) else "5",
        selected_pass_mark_percent=pass_key if any(v == pass_key for v, _ in _PASS_MARK_OPTIONS) else pass_key,
        moderation_range_options=[StudentAdminDashboardFilterOption(value=v, label=l) for v, l in _MODERATION_OPTIONS],
        pass_mark_options=[StudentAdminDashboardFilterOption(value=v, label=l) for v, l in _PASS_MARK_OPTIONS],
        selected_config_id=config.config_id,
        selected_session_id=session.session_id,
        footer_disclaimer="Live institutional data · Assessment configuration · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def save_internal_external_assessment_page(
    scope: AccessScope,
    payload: InternalExternalAssessmentSavePayload,
) -> InternalExternalAssessmentPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    user = await User.get(scope.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, payload.session_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)

    if payload.config_id.strip():
        config = await ExamAssessmentConfig.find_one(
            Eq(ExamAssessmentConfig.tenant_id, tenant_id),
            Eq(ExamAssessmentConfig.config_id, payload.config_id),
        )
        if config is None:
            raise AppError(code="NOT_FOUND", message="Assessment configuration not found", status_code=404)

        theory_rules = dict(config.theory_rules or {})
        theory_rules["moderation_range_marks"] = int(payload.moderation_range)
        passing = float(payload.pass_mark_percent)

        await update_assessment_config(
            scope,
            user,
            to_object_id(str(config.id), "config_id"),
            ExamAssessmentConfigUpdate(
                passing_marks_percent=passing,
                theory_rules=theory_rules,
            ),
        )

    page = await get_internal_external_assessment_page(scope, session_id=payload.session_id)
    if payload.advance_workflow:
        next_href = workflow_href_after("configure_subjects", payload.session_id)
        if next_href:
            return page.model_copy(update={"continue_href": next_href})
    return page