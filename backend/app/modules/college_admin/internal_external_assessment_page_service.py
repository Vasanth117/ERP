"""Internal & external assessment page (CA 09.08)."""

from __future__ import annotations

from uuid import uuid4

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
from app.modules.college_admin.exam_timetable_management_page_service import regenerate_exam_timetable_page
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ExamTimetableManagementActionPayload,
    InternalExternalAssessmentComponentDraft,
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
from app.modules.examinations.exam_cell_assessment_schemas import (
    ExamAssessmentComponentInput,
    ExamAssessmentConfigCreate,
    ExamAssessmentConfigUpdate,
)
from app.modules.examinations.exam_cell_assessment_service import create_assessment_config, update_assessment_config
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

_ASSESSMENT_TYPE_OPTIONS = [
    (ExamAssessmentComponentKind.CIA.value, "Continuous internal (CIA)"),
    (ExamAssessmentComponentKind.INTERNAL.value, "Internal assessment"),
    (ExamAssessmentComponentKind.MODEL_EXAM.value, "Model examination"),
    (ExamAssessmentComponentKind.END_SEMESTER.value, "End semester examination"),
    (ExamAssessmentComponentKind.THEORY.value, "Theory"),
    (ExamAssessmentComponentKind.PRACTICAL.value, "Practical"),
    (ExamAssessmentComponentKind.LABORATORY.value, "Laboratory"),
]

_SOURCE_OPTIONS = [
    ("faculty", "Faculty"),
    ("exam_cell", "Exam cell"),
    ("lms", "LMS"),
]

_SOURCE_LABELS = {key: label for key, label in _SOURCE_OPTIONS}

_DEFAULT_COMPONENTS = [
    ExamAssessmentComponentInput(
        code="CIA",
        name="Continuous Internal Assessment",
        assessment_type=ExamAssessmentComponentKind.CIA,
        max_marks=50,
        weight_percent=20,
        passing_marks=20,
        sort_order=1,
        metadata={"source_label": "Faculty", "source": "faculty"},
    ),
    ExamAssessmentComponentInput(
        code="ESE",
        name="End Semester Examination",
        assessment_type=ExamAssessmentComponentKind.END_SEMESTER,
        max_marks=100,
        weight_percent=80,
        passing_marks=40,
        sort_order=2,
        metadata={"source_label": "Exam Cell", "source": "exam_cell"},
    ),
]


def _default_pattern_components() -> list[ExamAssessmentComponentInput]:
    return [c.model_copy(deep=True) for c in _DEFAULT_COMPONENTS]


def _default_config_code(session: ExamSession) -> str:
    base = (session.session_code or session.session_id or "SESSION").strip().upper().replace(" ", "-")[:20]
    return f"EXAM-{base}-{uuid4().hex[:4].upper()}"


def _page_assessment_options() -> dict[str, list[StudentAdminDashboardFilterOption]]:
    return {
        "assessment_type_options": [
            StudentAdminDashboardFilterOption(value=value, label=label) for value, label in _ASSESSMENT_TYPE_OPTIONS
        ],
        "source_options": [StudentAdminDashboardFilterOption(value=value, label=label) for value, label in _SOURCE_OPTIONS],
    }


def _source_key_from_component(comp: ExamAssessmentComponent) -> str:
    meta = comp.metadata or {}
    raw = str(meta.get("source") or "").strip().lower()
    if raw in _SOURCE_LABELS:
        return raw
    if comp.assessment_type in (
        ExamAssessmentComponentKind.END_SEMESTER,
        ExamAssessmentComponentKind.THEORY,
        ExamAssessmentComponentKind.PRACTICAL,
        ExamAssessmentComponentKind.LABORATORY,
    ):
        return "exam_cell"
    return "faculty"


def _drafts_from_components(components: list[ExamAssessmentComponent]) -> list[InternalExternalAssessmentComponentDraft]:
    drafts: list[InternalExternalAssessmentComponentDraft] = []
    for comp in components:
        drafts.append(
            InternalExternalAssessmentComponentDraft(
                component_id=comp.component_id,
                code=comp.code,
                name=comp.name,
                assessment_type=comp.assessment_type.value,
                weight_percent=float(comp.weight_percent),
                max_marks=float(comp.max_marks),
                source=_source_key_from_component(comp),
            )
        )
    return drafts


def _components_from_drafts(
    drafts: list[InternalExternalAssessmentComponentDraft],
) -> list[ExamAssessmentComponentInput]:
    if not drafts:
        raise AppError(code="VALIDATION", message="Add at least one assessment component", status_code=422)
    payload: list[ExamAssessmentComponentInput] = []
    for index, draft in enumerate(drafts, start=1):
        name = draft.name.strip()
        if not name:
            raise AppError(code="VALIDATION", message="Each component needs a name", status_code=422)
        code = (draft.code or name).strip().upper().replace(" ", "_")[:32]
        if not code:
            raise AppError(code="VALIDATION", message="Each component needs a code", status_code=422)
        try:
            kind = ExamAssessmentComponentKind(draft.assessment_type)
        except ValueError as exc:
            raise AppError(code="VALIDATION", message="Invalid assessment component type", status_code=422) from exc
        source = draft.source if draft.source in _SOURCE_LABELS else "faculty"
        passing = round(float(draft.max_marks) * 0.4, 2) if draft.max_marks else None
        payload.append(
            ExamAssessmentComponentInput(
                code=code,
                name=name,
                assessment_type=kind,
                max_marks=float(draft.max_marks),
                weight_percent=float(draft.weight_percent),
                passing_marks=passing,
                sort_order=index,
                metadata={"source": source, "source_label": _SOURCE_LABELS[source]},
            )
        )
    return payload


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
    option_fields = _page_assessment_options()
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
        component_drafts=[],
        **option_fields,
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
    page_subtitle = f"{chrome['step_progress_label']} · {session.name}"

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
    component_drafts = _drafts_from_components(components)
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
        component_drafts=component_drafts,
        **_page_assessment_options(),
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


async def create_session_assessment_pattern_page(
    scope: AccessScope,
    *,
    session_id: str,
) -> InternalExternalAssessmentPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    user = await User.get(scope.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, session_id.strip()),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)

    config = await _resolve_config(tenant_id, session)
    components = _default_pattern_components()
    if config is not None:
        existing = await ExamAssessmentComponent.find(
            Eq(ExamAssessmentComponent.tenant_id, tenant_id),
            Eq(ExamAssessmentComponent.config_id, config.config_id),
        ).to_list()
        if existing:
            return await get_internal_external_assessment_page(scope, session_id=session.session_id)
        await update_assessment_config(
            scope,
            user,
            to_object_id(str(config.id), "config_id"),
            ExamAssessmentConfigUpdate(components=components),
        )
    else:
        title = f"{session.name} assessment pattern"
        await create_assessment_config(
            scope,
            user,
            ExamAssessmentConfigCreate(
                config_code=_default_config_code(session),
                title=title,
                programme_code=None,
                semester_label=session.semester_label,
                academic_year_label=session.academic_year_label,
                course_code=None,
                passing_marks_percent=40.0,
                theory_rules={"moderation_range_marks": 5},
                components=components,
            ),
        )

    return await get_internal_external_assessment_page(scope, session_id=session.session_id)


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

    config: ExamAssessmentConfig | None = None
    if payload.config_id.strip():
        config = await ExamAssessmentConfig.find_one(
            Eq(ExamAssessmentConfig.tenant_id, tenant_id),
            Eq(ExamAssessmentConfig.config_id, payload.config_id),
        )
        if config is None:
            raise AppError(code="NOT_FOUND", message="Assessment configuration not found", status_code=404)

    if config is None and payload.components:
        await create_session_assessment_pattern_page(scope, session_id=payload.session_id)
        config = await _resolve_config(tenant_id, session)
        if config is None:
            raise AppError(code="SERVER", message="Failed to prepare assessment configuration", status_code=500)

    if config is not None:
        theory_rules = dict(config.theory_rules or {})
        theory_rules["moderation_range_marks"] = int(payload.moderation_range)
        passing = float(payload.pass_mark_percent)
        update_kwargs: dict[str, object] = {
            "passing_marks_percent": passing,
            "theory_rules": theory_rules,
        }
        if payload.components is not None:
            update_kwargs["components"] = _components_from_drafts(payload.components)
        await update_assessment_config(
            scope,
            user,
            to_object_id(str(config.id), "config_id"),
            ExamAssessmentConfigUpdate(**update_kwargs),  # type: ignore[arg-type]
        )

    page = await get_internal_external_assessment_page(scope, session_id=payload.session_id)
    if payload.advance_workflow:
        await regenerate_exam_timetable_page(
            scope,
            ExamTimetableManagementActionPayload(session_id=payload.session_id, page=1),
        )
        next_href = workflow_href_after("configure_subjects", payload.session_id)
        if next_href:
            return page.model_copy(update={"continue_href": next_href})
    return page