"""Credit and grading configuration pages (CA 05 — college admin academics)."""

from __future__ import annotations

import re
from collections import defaultdict
from copy import deepcopy
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.academic_config_models import AcademicRegulation, ConfigPublicationStatus
from app.modules.college_admin.credit_grading_nav import credit_grading_sub_nav
from app.modules.college_admin.department_performance_overview_service import _programme_level
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicYearCreateFormOption,
    AcademicYearRuleToggle,
    CreditCalculationField,
    CreditConfigurationPageRead,
    CreditConfigurationSave,
    CreditLevelRequirementRow,
    CreditLimitStatItem,
    GradingCalculationField,
    GradingClassificationRow,
    GradingScaleRow,
    GradingSystemConfigurationPageRead,
    GradingSystemConfigurationSave,
)
from app.modules.examinations.models import GradingPolicy
from app.modules.students.curriculum_models import CurriculumReference, RegistrationPolicyReference
from app.modules.students.curriculum_models import StudentCourseRegistration
from app.modules.students.registration_enums import CourseRegistrationStatus

_SCOPE_PROGRESSION = "progression"
_SCOPE_GRADING = "grading"

_DEFAULT_PROGRESSION_RULES: dict[str, Any] = {
    "calculation": {
        "lecture_week": "1 credit",
        "tutorial_week": "1 credit",
        "practical_hours_per_week": "2",
        "practical_week_credits": "1 credit",
        "internship_4_weeks": "2 credits",
        "mooc_max": "up_to_6",
        "honours_additional": "additional_18",
    },
    "toggles": {
        "allow_mooc_transfer": True,
        "allow_overload": True,
        "audit_in_cgpa": False,
        "carry_forward_excess": False,
    },
    "level_overrides": {},
    "requirements_footnote_regulation": "",
}

_DEFAULT_GRADING_RULES: dict[str, Any] = {
    "grade_rows": [],
    "classification_rows": [],
    "calculation": {
        "grading_method": "relative_30",
        "cgpa_rounding": "2_decimals",
        "percentage_conversion": "cgpa_x_10",
    },
    "toggles": {
        "arrear_in_cgpa": True,
        "show_grade_points_transcript": True,
        "allow_moderation": True,
    },
    "applies_to_regulations": "",
}

_MOOC_OPTIONS = [
    AcademicYearCreateFormOption(value="up_to_6", label="Up to 6 credits"),
    AcademicYearCreateFormOption(value="up_to_12", label="Up to 12 credits"),
    AcademicYearCreateFormOption(value="none", label="Not permitted"),
]

_HONOURS_OPTIONS = [
    AcademicYearCreateFormOption(value="additional_18", label="Additional 18 credits"),
    AcademicYearCreateFormOption(value="additional_24", label="Additional 24 credits"),
    AcademicYearCreateFormOption(value="none", label="Not offered"),
]

_GRADING_METHOD_OPTIONS = [
    AcademicYearCreateFormOption(value="relative_30", label="Relative (curve) for >30 students"),
    AcademicYearCreateFormOption(value="absolute", label="Absolute grading"),
]

_ROUNDING_OPTIONS = [
    AcademicYearCreateFormOption(value="2_decimals", label="2 decimals"),
    AcademicYearCreateFormOption(value="1_decimal", label="1 decimal"),
]

_PCT_OPTIONS = [
    AcademicYearCreateFormOption(value="cgpa_x_10", label="CGPA × 10"),
    AcademicYearCreateFormOption(value="cgpa_x_9_5", label="CGPA × 9.5"),
]


def _level_label(level: str, sample_name: str) -> str:
    if level == "undergraduate":
        if "b.sc" in sample_name.lower() or "bsc" in sample_name.lower():
            return "UG – B.Sc"
        return "UG – B.E. / B.Tech"
    if level == "postgraduate":
        return "PG – M.E. / M.Tech"
    if level == "doctoral":
        return "Doctoral"
    return level.title()


async def _progression_regulation(tenant_id: PydanticObjectId) -> AcademicRegulation:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_PROGRESSION),
        Eq(AcademicRegulation.status, ConfigPublicationStatus.DRAFT),
    )
    if doc is None:
        doc = await AcademicRegulation.find_one(
            Eq(AcademicRegulation.tenant_id, tenant_id),
            Eq(AcademicRegulation.scope_key, _SCOPE_PROGRESSION),
        )
    if doc is None:
        rules = deepcopy(_DEFAULT_PROGRESSION_RULES)
        doc = AcademicRegulation(
            tenant_id=tenant_id,
            scope_key=_SCOPE_PROGRESSION,
            rules=rules,
            status=ConfigPublicationStatus.DRAFT,
        )
        await doc.insert()
    return doc


async def _grading_regulation(tenant_id: PydanticObjectId) -> AcademicRegulation:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_GRADING),
        Eq(AcademicRegulation.status, ConfigPublicationStatus.DRAFT),
    )
    if doc is None:
        doc = await AcademicRegulation.find_one(
            Eq(AcademicRegulation.tenant_id, tenant_id),
            Eq(AcademicRegulation.scope_key, _SCOPE_GRADING),
        )
    if doc is None:
        rules = deepcopy(_DEFAULT_GRADING_RULES)
        doc = AcademicRegulation(
            tenant_id=tenant_id,
            scope_key=_SCOPE_GRADING,
            rules=rules,
            status=ConfigPublicationStatus.DRAFT,
        )
        await doc.insert()
    return doc


def _grade_rows_from_policy(policy: GradingPolicy | None, rules: dict) -> list[GradingScaleRow]:
    stored = rules.get("grade_rows") or []
    if stored:
        return [
            GradingScaleRow(
                grade_id=str(i),
                grade=str(row.get("grade", "")),
                grade_point=float(row.get("grade_point", 0)),
                marks_range_label=str(row.get("marks_range_label", "—")),
                description=str(row.get("description", "")),
            )
            for i, row in enumerate(stored)
        ]
    if policy and policy.grade_bands:
        rows: list[GradingScaleRow] = []
        bands = sorted(policy.grade_bands, key=lambda b: float(b.get("min", 0)), reverse=True)
        for i, band in enumerate(bands):
            mn = int(band.get("min", 0))
            rows.append(
                GradingScaleRow(
                    grade_id=str(i),
                    grade=str(band.get("grade", "")),
                    grade_point=float(band.get("grade_point", band.get("point", 0))),
                    marks_range_label=f"{mn}+",
                    description=str(band.get("description", "")),
                )
            )
        return rows
    return []


async def _build_level_rows(
    tenant_id: PydanticObjectId,
    overrides: dict,
) -> tuple[list[CreditLevelRequirementRow], str]:
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    policies = await RegistrationPolicyReference.find(Eq(RegistrationPolicyReference.tenant_id, tenant_id)).to_list()
    max_by_prog: dict[str, float] = defaultdict(float)
    min_by_prog: dict[str, float] = defaultdict(float)
    for pol in policies:
        code = pol.programme_code.upper()
        max_by_prog[code] = max(max_by_prog[code], pol.max_credits)
        min_by_prog[code] = min(min_by_prog[code] or pol.min_credits, pol.min_credits)

    groups: dict[str, list[AcademicProgramme]] = defaultdict(list)
    for prog in programmes:
        if not prog.is_active:
            continue
        level = _programme_level(prog)
        groups[level].append(prog)

    curriculum = await CurriculumReference.find(Eq(CurriculumReference.tenant_id, tenant_id)).to_list()
    footnote = "—"
    for ref in sorted(curriculum, key=lambda r: r.updated_at, reverse=True):
        if ref.academic_regulations:
            footnote = f"As per {ref.academic_regulations[0]}"
            break

    rows: list[CreditLevelRequirementRow] = []
    for level, progs in sorted(groups.items(), key=lambda item: item[0]):
        if not progs:
            continue
        level_key = level
        override = overrides.get(level_key) or {}
        sample = progs[0].name
        label = _level_label(level, sample)
        graduate = override.get("min_graduate_credits")
        if graduate is None:
            graduate = max((p.credits_required for p in progs), default=0)
        codes = [p.programme_code.upper() for p in progs]
        max_sem = override.get("max_per_semester")
        if max_sem is None:
            max_vals = [max_by_prog[c] for c in codes if c in max_by_prog]
            max_sem = max(max_vals) if max_vals else 26
        min_sem = override.get("min_per_semester")
        if min_sem is None:
            min_vals = [min_by_prog[c] for c in codes if c in min_by_prog and min_by_prog[c]]
            min_sem = min(min_vals) if min_vals else 16
        rows.append(
            CreditLevelRequirementRow(
                level_key=level_key,
                level_label=label,
                min_graduate_credits=float(graduate),
                max_per_semester=float(max_sem),
                min_per_semester=float(min_sem),
                status_label="Active",
                status_tone="success",
            )
        )
    return rows, footnote


async def _student_limit_counts(tenant_id: PydanticObjectId) -> tuple[int, int]:
    registrations = await StudentCourseRegistration.find(Eq(StudentCourseRegistration.tenant_id, tenant_id)).to_list()
    active_status = {
        CourseRegistrationStatus.APPROVED,
        CourseRegistrationStatus.SUBMITTED,
        CourseRegistrationStatus.PENDING_APPROVAL,
    }
    policies = await RegistrationPolicyReference.find(Eq(RegistrationPolicyReference.tenant_id, tenant_id)).to_list()
    policy_by_prog: dict[str, RegistrationPolicyReference] = {}
    for pol in policies:
        policy_by_prog[pol.programme_code.upper()] = pol

    credits_by_student: dict[tuple, float] = defaultdict(float)
    prog_by_student: dict[PydanticObjectId, str] = {}
    for row in registrations:
        if row.status not in active_status:
            continue
        key = (row.user_id, row.academic_year_label, row.semester_label)
        credits_by_student[key] += row.credit_units
        prog_by_student[row.user_id] = row.programme_code.upper()

    above = 0
    below = 0
    seen: set[PydanticObjectId] = set()
    for (user_id, _year, _sem), total in credits_by_student.items():
        if user_id in seen:
            continue
        seen.add(user_id)
        prog = prog_by_student.get(user_id)
        pol = policy_by_prog.get(prog or "")
        if not pol:
            continue
        if total > pol.max_credits:
            above += 1
        elif total < pol.min_credits:
            below += 1
    return above, below


async def get_credit_configuration_page(scope: AccessScope) -> CreditConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    reg = await _progression_regulation(tenant_id)
    rules = reg.rules or {}
    calc = {**_DEFAULT_PROGRESSION_RULES["calculation"], **(rules.get("calculation") or {})}
    toggles = {**_DEFAULT_PROGRESSION_RULES["toggles"], **(rules.get("toggles") or {})}
    overrides = rules.get("level_overrides") or {}

    level_rows, footnote = await _build_level_rows(tenant_id, overrides)
    above, below = await _student_limit_counts(tenant_id)

    calc_fields = [
        CreditCalculationField(key="lecture_week", label="1 lecture hour per week =", value=str(calc.get("lecture_week", ""))),
        CreditCalculationField(key="tutorial_week", label="1 tutorial hour per week =", value=str(calc.get("tutorial_week", ""))),
        CreditCalculationField(
            key="practical_hours_per_week",
            label="2 practical hours per week =",
            value=str(calc.get("practical_week_credits", calc.get("practical_hours_per_week", ""))),
        ),
        CreditCalculationField(key="internship_4_weeks", label="Internship (4 weeks) =", value=str(calc.get("internship_4_weeks", ""))),
        CreditCalculationField(
            key="mooc_max",
            label="MOOC courses (NPTEL)",
            value=str(calc.get("mooc_max", "")),
            field_type="select",
            options=_MOOC_OPTIONS,
        ),
        CreditCalculationField(
            key="honours_additional",
            label="Honours / minor degree",
            value=str(calc.get("honours_additional", "")),
            field_type="select",
            options=_HONOURS_OPTIONS,
        ),
    ]

    rule_toggles = [
        AcademicYearRuleToggle(
            key="allow_mooc_transfer",
            title="Allow credit transfer from MOOCs",
            description="NPTEL / SWAYAM",
            enabled=bool(toggles.get("allow_mooc_transfer")),
        ),
        AcademicYearRuleToggle(
            key="allow_overload",
            title="Allow overload above maximum",
            description="With HoD approval",
            enabled=bool(toggles.get("allow_overload")),
        ),
        AcademicYearRuleToggle(
            key="audit_in_cgpa",
            title="Count audit courses towards CGPA",
            description="",
            enabled=bool(toggles.get("audit_in_cgpa")),
        ),
        AcademicYearRuleToggle(
            key="carry_forward_excess",
            title="Carry forward excess credits",
            description="To next semester",
            enabled=bool(toggles.get("carry_forward_excess")),
        ),
    ]

    return CreditConfigurationPageRead(
        page_title="Credit Configuration",
        page_subtitle="Credit rules, minimum requirements and limits for each programme level",
        reset_label="Reset",
        save_rules_label="Save rules",
        cancel_label="Cancel",
        requirements_section_title="Credit requirements by level",
        requirements_table_headers=["Level", "Min. credits to graduate", "Max per semester", "Min per semester", "Status"],
        requirements_footer_label=rules.get("requirements_footnote_regulation") or footnote,
        requirements_edit_label="Edit →",
        requirements_edit_href="/college-admin/academics/programme-management",
        level_rows=level_rows,
        calculation_section_title="Credit calculation",
        calculation_fields=calc_fields,
        rules_section_title="Rules",
        rules=rule_toggles,
        limits_section_title="Students outside limits",
        limit_stats=[
            CreditLimitStatItem(
                key="above_max",
                title="Above max credits",
                description="Overload requests",
                count=above,
                count_tone="warning",
            ),
            CreditLimitStatItem(
                key="below_min",
                title="Below min credits",
                description="Detained / part-time",
                count=below,
                count_tone="info",
            ),
        ],
        form_note="Changes are saved to the audit log with your name and time.",
        sub_nav=credit_grading_sub_nav(active="credit"),
        footer_disclaimer="Live academic data · Programmes, registration policies and progression rules · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def save_credit_configuration(scope: AccessScope, payload: CreditConfigurationSave) -> CreditConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    reg = await _progression_regulation(tenant_id)
    overrides = {
        row.level_key: {
            "min_graduate_credits": row.min_graduate_credits,
            "max_per_semester": row.max_per_semester,
            "min_per_semester": row.min_per_semester,
        }
        for row in payload.level_rows
    }
    reg.rules = {
        **(reg.rules or {}),
        "calculation": payload.calculation,
        "toggles": payload.rules,
        "level_overrides": overrides,
    }
    reg.updated_by = scope.user_id
    reg.updated_at = utcnow()
    await reg.save()
    await record_audit(
        actor_id=scope.user_id,
        action="academic.credit_rules.saved",
        resource_type="academic_regulation",
        resource_id=str(reg.id),
        tenant_id=tenant_id,
    )
    return await get_credit_configuration_page(scope)


async def reset_credit_configuration(scope: AccessScope) -> CreditConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    reg = await _progression_regulation(tenant_id)
    reg.rules = deepcopy(_DEFAULT_PROGRESSION_RULES)
    reg.rules["level_overrides"] = {}
    reg.updated_by = scope.user_id
    reg.updated_at = utcnow()
    await reg.save()
    return await get_credit_configuration_page(scope)


async def get_grading_system_configuration_page(scope: AccessScope) -> GradingSystemConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_READ)
    tenant_id = require_college_tenant_scope(scope)
    reg = await _grading_regulation(tenant_id)
    rules = reg.rules or {}
    policy = await GradingPolicy.find_one(Eq(GradingPolicy.tenant_id, tenant_id))

    grade_rows = _grade_rows_from_policy(policy, rules)
    classification_stored = rules.get("classification_rows") or []
    classification_rows = [
        GradingClassificationRow(
            class_id=str(i),
            class_label=str(row.get("class_label", "")),
            cgpa_label=str(row.get("cgpa_label", "")),
            condition_label=str(row.get("condition_label", "")),
        )
        for i, row in enumerate(classification_stored)
    ]

    calc = {**_DEFAULT_GRADING_RULES["calculation"], **(rules.get("calculation") or {})}
    toggles = {**_DEFAULT_GRADING_RULES["toggles"], **(rules.get("toggles") or {})}

    curriculum = await CurriculumReference.find(Eq(CurriculumReference.tenant_id, tenant_id)).to_list()
    regs = set()
    for ref in curriculum:
        regs.update(ref.academic_regulations)
    footer = rules.get("applies_to_regulations") or (" and ".join(sorted(regs)) if regs else "Current regulations")

    calc_fields = [
        GradingCalculationField(
            key="grading_method",
            label="Grading method",
            value=str(calc.get("grading_method", "")),
            required=True,
            options=_GRADING_METHOD_OPTIONS,
        ),
        GradingCalculationField(
            key="cgpa_rounding",
            label="CGPA rounding",
            value=str(calc.get("cgpa_rounding", "")),
            required=True,
            options=_ROUNDING_OPTIONS,
        ),
        GradingCalculationField(
            key="percentage_conversion",
            label="Percentage conversion",
            value=str(calc.get("percentage_conversion", "")),
            options=_PCT_OPTIONS,
        ),
    ]

    rule_toggles = [
        AcademicYearRuleToggle(
            key="arrear_in_cgpa",
            title="Include arrear grades in CGPA",
            description="After clearing",
            enabled=bool(toggles.get("arrear_in_cgpa")),
        ),
        AcademicYearRuleToggle(
            key="show_grade_points_transcript",
            title="Show grade points on transcript",
            description="",
            enabled=bool(toggles.get("show_grade_points_transcript")),
        ),
        AcademicYearRuleToggle(
            key="allow_moderation",
            title="Allow moderation by exam cell",
            description="Max +3 marks",
            enabled=bool(toggles.get("allow_moderation")),
        ),
    ]

    return GradingSystemConfigurationPageRead(
        page_title="Grading System Configuration",
        page_subtitle="Grades, grade points and classification rules used in results",
        preview_transcript_label="Preview transcript",
        preview_transcript_href="/college-admin/examinations",
        save_grading_label="Save grading",
        cancel_label="Cancel",
        grade_scale_title="Grade scale – 10-point",
        grade_table_headers=["Grade", "Grade point", "Marks range", "Description"],
        grade_rows=grade_rows,
        grade_scale_footer=footer,
        add_grade_label="Add grade →",
        classification_section_title="Classification",
        classification_table_headers=["Class", "CGPA", "Condition"],
        classification_rows=classification_rows,
        classification_footer=f"{len(classification_rows)} classes",
        classification_edit_label="Edit →",
        calculation_section_title="Calculation",
        calculation_fields=calc_fields,
        rules_section_title="Rules",
        rules=rule_toggles,
        form_note="Changes are saved to the audit log with your name and time.",
        sub_nav=credit_grading_sub_nav(active="grading"),
        footer_disclaimer="Live academic data · Grading policy and examination regulations · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def save_grading_system_configuration(
    scope: AccessScope,
    payload: GradingSystemConfigurationSave,
) -> GradingSystemConfigurationPageRead:
    authorize(scope, Permission.ACADEMIC_CONFIG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    reg = await _grading_regulation(tenant_id)

    grade_store = [
        {
            "grade": row.grade,
            "grade_point": row.grade_point,
            "marks_range_label": row.marks_range_label,
            "description": row.description,
        }
        for row in payload.grade_rows
    ]
    class_store = [
        {
            "class_label": row.class_label,
            "cgpa_label": row.cgpa_label,
            "condition_label": row.condition_label,
        }
        for row in payload.classification_rows
    ]

    reg.rules = {
        **(reg.rules or {}),
        "grade_rows": grade_store,
        "classification_rows": class_store,
        "calculation": payload.calculation,
        "toggles": payload.rules,
    }
    reg.updated_by = scope.user_id
    reg.updated_at = utcnow()
    await reg.save()

    policy = await GradingPolicy.find_one(Eq(GradingPolicy.tenant_id, tenant_id))
    if policy is None:
        policy = GradingPolicy(tenant_id=tenant_id)
    bands = []
    for row in payload.grade_rows:
        parts = row.marks_range_label.replace("–", "-").split("-")
        mn = 0
        if parts:
            try:
                mn = int(re.search(r"\d+", parts[0]).group()) if re.search(r"\d+", parts[0]) else 0
            except (AttributeError, ValueError):
                mn = 0
        bands.append({"min": mn, "grade": row.grade, "grade_point": row.grade_point, "description": row.description})
    policy.grade_bands = bands
    policy.updated_at = utcnow()
    await policy.save()

    await record_audit(
        actor_id=scope.user_id,
        action="academic.grading_rules.saved",
        resource_type="academic_regulation",
        resource_id=str(reg.id),
        tenant_id=tenant_id,
    )
    return await get_grading_system_configuration_page(scope)