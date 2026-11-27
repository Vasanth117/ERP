"""LMS settings management page (CA 15.12)."""

from __future__ import annotations

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicRegulation
from app.modules.college_admin.lms_admin_models import InstitutionLmsSettings, LmsPublishingPolicy
from app.modules.college_admin.lms_admin_service import _append_history, _get_settings_doc
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionFieldMeta,
    InstitutionFieldOption,
    LmsSettingsFormValues,
    LmsSettingsPageRead,
    LmsSettingsSave,
    LmsSettingsToggleRule,
)
from app.modules.lms.models import AssignmentRule

_SCOPE_KEY = "lms_administration_settings"
_POLICY_CODE = "default"

_DEFAULTS: dict[str, object] = {
    "max_upload_size_mb": "200",
    "allowed_formats": "pdf_docx_pptx_mp4",
    "late_submission": "allowed_penalty",
    "quiz_attempts": "2",
    "video_retention_years": "3",
    "completion_threshold_percent": "80",
    "require_content_review": True,
    "allow_video_download": False,
    "plagiarism_check_assignments": True,
}

_FIELD_META = [
    InstitutionFieldMeta(key="max_upload_size_mb", label="Max upload size", field_type="text", required=True),
    InstitutionFieldMeta(key="allowed_formats", label="Allowed formats", field_type="select", required=True),
    InstitutionFieldMeta(key="late_submission", label="Late submission", field_type="select", required=True),
    InstitutionFieldMeta(key="quiz_attempts", label="Quiz attempts", field_type="select", required=True),
    InstitutionFieldMeta(key="video_retention_years", label="Video retention", field_type="select", required=True),
    InstitutionFieldMeta(
        key="completion_threshold_percent",
        label="Completion threshold",
        field_type="text",
        required=True,
    ),
]

_FIELD_OPTIONS: dict[str, list[InstitutionFieldOption]] = {
    "allowed_formats": [
        InstitutionFieldOption(value="pdf_docx_pptx_mp4", label="PDF, DOCX, PPTX, MP4"),
        InstitutionFieldOption(value="pdf_docx", label="PDF, DOCX"),
        InstitutionFieldOption(value="pdf_docx_pptx", label="PDF, DOCX, PPTX"),
        InstitutionFieldOption(value="pdf_mp4", label="PDF, MP4"),
    ],
    "late_submission": [
        InstitutionFieldOption(value="allowed_penalty", label="Allowed with penalty"),
        InstitutionFieldOption(value="allowed_no_penalty", label="Allowed without penalty"),
        InstitutionFieldOption(value="not_allowed", label="Not allowed"),
    ],
    "quiz_attempts": [
        InstitutionFieldOption(value="1", label="1"),
        InstitutionFieldOption(value="2", label="2"),
        InstitutionFieldOption(value="3", label="3"),
        InstitutionFieldOption(value="unlimited", label="Unlimited"),
    ],
    "video_retention_years": [
        InstitutionFieldOption(value="1", label="1 year"),
        InstitutionFieldOption(value="2", label="2 years"),
        InstitutionFieldOption(value="3", label="3 years"),
        InstitutionFieldOption(value="5", label="5 years"),
    ],
}

_FORMAT_EXTENSIONS: dict[str, list[str]] = {
    "pdf_docx_pptx_mp4": [".pdf", ".docx", ".pptx", ".mp4"],
    "pdf_docx": [".pdf", ".docx"],
    "pdf_docx_pptx": [".pdf", ".docx", ".pptx"],
    "pdf_mp4": [".pdf", ".mp4"],
}


def _parse_mb(value: str) -> int:
    digits = "".join(c for c in (value or "") if c.isdigit())
    mb = int(digits) if digits else int(str(_DEFAULTS["max_upload_size_mb"]))
    return max(1, min(mb, 2048))


def _parse_percent(value: str) -> float:
    digits = "".join(c for c in (value or "") if c.isdigit() or c == ".")
    if not digits:
        return float(_DEFAULTS["completion_threshold_percent"])
    try:
        pct = float(digits)
    except ValueError:
        pct = float(_DEFAULTS["completion_threshold_percent"])
    return max(0, min(pct, 100))


def _display_percent(value: float) -> str:
    return f"{int(value) if value == int(value) else value}%"


async def _load_rules(tenant_id: PydanticObjectId) -> dict[str, object]:
    merged = dict(_DEFAULTS)
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc and doc.rules:
        merged.update(doc.rules)

    settings = await _get_settings_doc(tenant_id)
    merged["require_content_review"] = settings.moderation_required

    policy = await LmsPublishingPolicy.find_one(
        Eq(LmsPublishingPolicy.tenant_id, tenant_id),
        Eq(LmsPublishingPolicy.policy_code, _POLICY_CODE),
    )
    if policy:
        merged["require_content_review"] = policy.material_requires_approval
        rules_blob = policy.rules or {}
        if "allow_video_download" in rules_blob:
            merged["allow_video_download"] = bool(rules_blob["allow_video_download"])
        if "plagiarism_check_assignments" in rules_blob:
            merged["plagiarism_check_assignments"] = bool(rules_blob["plagiarism_check_assignments"])
        if rules_blob.get("quiz_attempts"):
            merged["quiz_attempts"] = str(rules_blob["quiz_attempts"])
        if rules_blob.get("video_retention_years"):
            merged["video_retention_years"] = str(rules_blob["video_retention_years"])
        if rules_blob.get("completion_threshold_percent") is not None:
            merged["completion_threshold_percent"] = float(rules_blob["completion_threshold_percent"])

    rule = await AssignmentRule.find_one(Eq(AssignmentRule.tenant_id, tenant_id))
    if rule:
        merged["max_upload_size_mb"] = str(max(1, round(rule.max_file_size_bytes / (1024 * 1024))))
        if rule.late_submission_allowed:
            if rule.late_penalty_percent > 0:
                merged["late_submission"] = "allowed_penalty"
            else:
                merged["late_submission"] = "allowed_no_penalty"
        else:
            merged["late_submission"] = "not_allowed"
        for key, exts in _FORMAT_EXTENSIONS.items():
            if exts == rule.allowed_extensions:
                merged["allowed_formats"] = key
                break

    if isinstance(merged.get("completion_threshold_percent"), (int, float)):
        merged["completion_threshold_percent"] = _display_percent(float(merged["completion_threshold_percent"]))
    elif isinstance(merged.get("completion_threshold_percent"), str) and not merged["completion_threshold_percent"].endswith("%"):
        merged["completion_threshold_percent"] = f"{merged['completion_threshold_percent']}%"

    if isinstance(merged.get("max_upload_size_mb"), (int, float)):
        merged["max_upload_size_mb"] = f"{int(merged['max_upload_size_mb'])} MB"
    elif isinstance(merged.get("max_upload_size_mb"), str) and "MB" not in merged["max_upload_size_mb"].upper():
        merged["max_upload_size_mb"] = f"{merged['max_upload_size_mb']} MB"

    return merged


def _form_values(rules: dict[str, object]) -> LmsSettingsFormValues:
    max_upload = rules.get("max_upload_size_mb", _DEFAULTS["max_upload_size_mb"])
    if isinstance(max_upload, (int, float)):
        max_upload = f"{int(max_upload)} MB"
    elif isinstance(max_upload, str) and "MB" not in max_upload.upper():
        max_upload = f"{max_upload} MB"

    threshold = rules.get("completion_threshold_percent", _DEFAULTS["completion_threshold_percent"])
    if isinstance(threshold, (int, float)):
        threshold = _display_percent(float(threshold))
    elif isinstance(threshold, str) and not threshold.endswith("%"):
        threshold = f"{threshold}%"

    return LmsSettingsFormValues(
        max_upload_size_mb=str(max_upload),
        allowed_formats=str(rules.get("allowed_formats", _DEFAULTS["allowed_formats"])),
        late_submission=str(rules.get("late_submission", _DEFAULTS["late_submission"])),
        quiz_attempts=str(rules.get("quiz_attempts", _DEFAULTS["quiz_attempts"])),
        video_retention_years=str(rules.get("video_retention_years", _DEFAULTS["video_retention_years"])),
        completion_threshold_percent=str(threshold),
        require_content_review=bool(rules.get("require_content_review", _DEFAULTS["require_content_review"])),
        allow_video_download=bool(rules.get("allow_video_download", _DEFAULTS["allow_video_download"])),
        plagiarism_check_assignments=bool(rules.get("plagiarism_check_assignments", _DEFAULTS["plagiarism_check_assignments"])),
    )


def _toggle_rules(form: LmsSettingsFormValues) -> list[LmsSettingsToggleRule]:
    return [
        LmsSettingsToggleRule(
            key="require_content_review",
            label="Require content review before publishing",
            enabled=form.require_content_review,
        ),
        LmsSettingsToggleRule(
            key="allow_video_download",
            label="Allow video download",
            enabled=form.allow_video_download,
        ),
        LmsSettingsToggleRule(
            key="plagiarism_check_assignments",
            label="Plagiarism check on assignments",
            enabled=form.plagiarism_check_assignments,
        ),
    ]


async def get_lms_settings_management_page(scope: AccessScope) -> LmsSettingsPageRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    rules = await _load_rules(tenant_id)
    form = _form_values(rules)
    return LmsSettingsPageRead(
        page_title="LMS Settings",
        page_subtitle="Policies and limits",
        cancel_label="Cancel",
        save_label="Save",
        limits_section_title="Limits",
        controls_section_title="Controls",
        field_meta=_FIELD_META,
        field_options=_FIELD_OPTIONS,
        form=form,
        toggle_rules=_toggle_rules(form),
        generated_at=now,
    )


async def save_lms_settings_management_page(
    scope: AccessScope,
    user: User,
    payload: LmsSettingsSave,
) -> LmsSettingsPageRead:
    authorize(scope, Permission.LMS_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    form = payload.form

    max_bytes = _parse_mb(form.max_upload_size_mb) * 1024 * 1024
    threshold = _parse_percent(form.completion_threshold_percent)
    extensions = _FORMAT_EXTENSIONS.get(form.allowed_formats, _FORMAT_EXTENSIONS["pdf_docx_pptx_mp4"])

    late_allowed = form.late_submission != "not_allowed"
    late_penalty = 0.0
    if form.late_submission == "allowed_penalty":
        late_penalty = 10.0

    rules = {
        **_DEFAULTS,
        **form.model_dump(),
        "max_upload_size_mb": str(_parse_mb(form.max_upload_size_mb)),
        "completion_threshold_percent": threshold,
    }

    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    if doc is None:
        doc = AcademicRegulation(tenant_id=tenant_id, scope_key=_SCOPE_KEY, rules=rules, updated_by=user.id)
        await doc.insert()
    else:
        doc.rules = rules
        doc.updated_by = user.id
        doc.updated_at = utcnow()
        await doc.save()

    settings = await _get_settings_doc(tenant_id)
    prev_settings = settings.model_dump(mode="json")
    settings.moderation_required = form.require_content_review
    settings.version += 1
    settings.updated_by = user.id
    settings.updated_at = utcnow()
    await settings.save()
    await _append_history(
        tenant_id,
        scope="lms_settings",
        resource_id="default",
        version_number=settings.version,
        snapshot=prev_settings,
        actor_id=user.id,
    )

    policy = await LmsPublishingPolicy.find_one(
        Eq(LmsPublishingPolicy.tenant_id, tenant_id),
        Eq(LmsPublishingPolicy.policy_code, _POLICY_CODE),
    )
    if policy is None:
        policy = LmsPublishingPolicy(
            tenant_id=tenant_id,
            policy_code=_POLICY_CODE,
            material_requires_approval=form.require_content_review,
            updated_by=user.id,
        )
        await policy.insert()
    else:
        policy.material_requires_approval = form.require_content_review
        policy.rules = {
            **(policy.rules or {}),
            "allow_video_download": form.allow_video_download,
            "plagiarism_check_assignments": form.plagiarism_check_assignments,
            "quiz_attempts": form.quiz_attempts,
            "video_retention_years": form.video_retention_years,
            "completion_threshold_percent": threshold,
            "max_upload_size_mb": _parse_mb(form.max_upload_size_mb),
        }
        policy.version += 1
        policy.updated_by = user.id
        policy.updated_at = utcnow()
        await policy.save()

    rule = await AssignmentRule.find_one(Eq(AssignmentRule.tenant_id, tenant_id))
    if rule is None:
        rule = AssignmentRule(tenant_id=tenant_id)
    rule.allowed_extensions = extensions
    rule.max_file_size_bytes = max_bytes
    rule.late_submission_allowed = late_allowed
    rule.late_penalty_percent = min(late_penalty, settings.assignment_late_penalty_cap)
    if rule.id:
        await rule.save()
    else:
        await rule.insert()

    return await get_lms_settings_management_page(scope)