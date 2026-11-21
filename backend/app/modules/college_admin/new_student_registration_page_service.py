"""New student registration wizard (CA 06.05)."""

from __future__ import annotations

import re
import secrets
from typing import Any
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionFieldMeta,
    InstitutionFieldOption,
    NewStudentRegistrationDraftUpdate,
    NewStudentRegistrationFormSection,
    NewStudentRegistrationFormValues,
    NewStudentRegistrationNextStep,
    NewStudentRegistrationPageRead,
    NewStudentRegistrationSummaryItem,
    NewStudentRegistrationWizardStep,
)
from app.modules.college_admin.student_admin_models import (
    AdmissionStatus,
    StudentAdmission,
    StudentNewRegistrationDraft,
)
from app.modules.college_admin.student_administration_dashboard_page_service import _quota_label
from app.modules.college_admin.student_statistics_overview_service import _CATEGORY_LABELS, _normalize_meta_key

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()

_WIZARD_STEPS: list[tuple[str, str]] = [
    ("admission", "Admission"),
    ("student_information", "Student information"),
    ("documents", "Documents"),
    ("programme_allocation", "Programme allocation"),
    ("approval", "Approval"),
    ("account_creation", "Account creation"),
]

_PERSONAL_FIELDS = [
    InstitutionFieldMeta(key="full_name", label="Full name", required=True),
    InstitutionFieldMeta(key="date_of_birth", label="Date of birth", required=True, field_type="date"),
    InstitutionFieldMeta(key="gender", label="Gender", required=True, field_type="select"),
    InstitutionFieldMeta(key="blood_group", label="Blood group", field_type="select"),
    InstitutionFieldMeta(key="mobile", label="Mobile", required=True),
    InstitutionFieldMeta(key="email", label="Email", field_type="email"),
    InstitutionFieldMeta(key="nationality", label="Nationality", field_type="select"),
    InstitutionFieldMeta(key="community", label="Community", field_type="select"),
]

_GUARDIAN_FIELDS = [
    InstitutionFieldMeta(key="guardian_name", label="Guardian name", required=True),
    InstitutionFieldMeta(key="relationship", label="Relationship", required=True, field_type="select"),
    InstitutionFieldMeta(key="guardian_mobile", label="Guardian mobile", required=True),
    InstitutionFieldMeta(key="occupation", label="Occupation"),
]

_GENDER_OPTIONS = [
    InstitutionFieldOption(value="", label="Select gender"),
    InstitutionFieldOption(value="female", label="Female"),
    InstitutionFieldOption(value="male", label="Male"),
    InstitutionFieldOption(value="other", label="Other"),
]

_BLOOD_GROUP_OPTIONS = [
    InstitutionFieldOption(value="", label="Select blood group"),
    *[InstitutionFieldOption(value=g, label=g) for g in ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")],
]

_NATIONALITY_OPTIONS = [
    InstitutionFieldOption(value="", label="Select nationality"),
    InstitutionFieldOption(value="indian", label="Indian"),
    InstitutionFieldOption(value="other", label="Other"),
]

_COMMUNITY_OPTIONS = [InstitutionFieldOption(value="", label="Select community")]
for key, label in sorted(_CATEGORY_LABELS.items(), key=lambda item: item[1]):
    _COMMUNITY_OPTIONS.append(InstitutionFieldOption(value=key, label=label))

_RELATIONSHIP_OPTIONS = [
    InstitutionFieldOption(value="", label="Select relationship"),
    InstitutionFieldOption(value="father", label="Father"),
    InstitutionFieldOption(value="mother", label="Mother"),
    InstitutionFieldOption(value="guardian", label="Guardian"),
    InstitutionFieldOption(value="sibling", label="Sibling"),
    InstitutionFieldOption(value="other", label="Other"),
]


def _ay_display(code: str) -> str:
    return code.replace("-", "–") if code else "—"


def _programme_label(code: str | None, programmes: dict[str, AcademicProgramme]) -> str:
    if not code:
        return "—"
    prog = programmes.get(code.upper())
    return prog.name if prog and prog.name else code


async def _generate_admission_number(tenant_id: PydanticObjectId, ay_code: str) -> str:
    year_part = ay_code.split("-")[0] if ay_code and "-" in ay_code else "0000"
    for _ in range(8):
        suffix = secrets.token_hex(2).upper()[:4]
        candidate = f"ADM-{year_part}-{suffix}"
        exists = await StudentAdmission.find_one(
            Eq(StudentAdmission.tenant_id, tenant_id),
            Eq(StudentAdmission.admission_number, candidate),
        )
        if not exists:
            return candidate
    return f"ADM-{year_part}-{secrets.token_hex(3).upper()[:6]}"


async def _resolve_admission(
    tenant_id: PydanticObjectId,
    actor_id: PydanticObjectId,
    admission_id: str | None,
) -> StudentAdmission:
    ay_label, _ = await _reader.current_academic_term(tenant_id)
    if admission_id:
        oid = to_object_id(admission_id, "admission id")
        admission = await StudentAdmission.get(oid)
        if admission is None or admission.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Admission not found", status_code=404)
        return admission

    number = await _generate_admission_number(tenant_id, ay_label or "2026-27")
    admission = StudentAdmission(
        tenant_id=tenant_id,
        admission_number=number,
        applicant_name="",
        applicant_email=f"draft+{secrets.token_hex(4)}@pending.local",
        programme_code="",
        academic_year_code=ay_label or "2026-27",
        status=AdmissionStatus.PENDING,
        metadata={"registration_origin": "new_student_wizard"},
        updated_by=actor_id,
    )
    await admission.insert()
    return admission


async def _get_or_create_draft(
    tenant_id: PydanticObjectId,
    actor_id: PydanticObjectId,
    admission_id: PydanticObjectId,
) -> StudentNewRegistrationDraft:
    existing = await StudentNewRegistrationDraft.find_one(
        Eq(StudentNewRegistrationDraft.tenant_id, tenant_id),
        Eq(StudentNewRegistrationDraft.admission_id, admission_id),
    )
    if existing is not None:
        return existing
    draft = StudentNewRegistrationDraft(
        tenant_id=tenant_id,
        admission_id=admission_id,
        actor_id=actor_id,
        step_key="student_information",
    )
    await draft.insert()
    return draft


def _coerce_form_values(raw: dict[str, Any], admission: StudentAdmission) -> NewStudentRegistrationFormValues:
    meta = admission.metadata or {}
    return NewStudentRegistrationFormValues(
        full_name=str(raw.get("full_name") or admission.applicant_name or "").strip(),
        date_of_birth=raw.get("date_of_birth") or meta.get("date_of_birth"),
        gender=raw.get("gender") or meta.get("gender"),
        blood_group=raw.get("blood_group") or meta.get("blood_group"),
        mobile=str(raw.get("mobile") or meta.get("mobile") or "").strip(),
        email=(
            ""
            if str(raw.get("email") or "").strip().endswith("@pending.local")
            else str(raw.get("email") or "").strip()
        )
        or (
            ""
            if str(admission.applicant_email or "").endswith("@pending.local")
            else str(admission.applicant_email or "").strip()
        ),
        nationality=raw.get("nationality") or meta.get("nationality"),
        community=raw.get("community") or meta.get("community") or _normalize_meta_key(
            str(meta.get("category", ""))
        )
        or None,
        guardian_name=str(raw.get("guardian_name") or meta.get("guardian_name") or "").strip(),
        relationship=raw.get("relationship") or meta.get("guardian_relationship"),
        guardian_mobile=str(raw.get("guardian_mobile") or meta.get("guardian_mobile") or "").strip(),
        occupation=str(raw.get("occupation") or meta.get("guardian_occupation") or "").strip(),
    )


def _step_index(step_key: str) -> int:
    for index, (key, _) in enumerate(_WIZARD_STEPS):
        if key == step_key:
            return index
    return 1


def _build_steps(current_key: str) -> list[NewStudentRegistrationWizardStep]:
    current_index = _step_index(current_key)
    steps: list[NewStudentRegistrationWizardStep] = []
    for index, (key, label) in enumerate(_WIZARD_STEPS):
        if index < current_index:
            status = "done"
        elif key == current_key:
            status = "active"
        else:
            status = "pending"
        steps.append(
            NewStudentRegistrationWizardStep(key=key, label=label, step_number=index + 1, status=status),
        )
    return steps


def _build_next_steps(current_key: str) -> list[NewStudentRegistrationNextStep]:
    current_index = _step_index(current_key)
    items: list[NewStudentRegistrationNextStep] = []
    for index, (key, label) in enumerate(_WIZARD_STEPS):
        if index <= current_index:
            continue
        if index == current_index + 1:
            items.append(NewStudentRegistrationNextStep(key=key, label=label, status_label="Next", tone="info"))
        elif len(items) < 2:
            items.append(NewStudentRegistrationNextStep(key=key, label=label, status_label="Then", tone="muted"))
        else:
            break
    if current_key == "student_information":
        items.insert(
            0,
            NewStudentRegistrationNextStep(
                key="student_information",
                label="Student information",
                status_label="In progress",
                tone="info",
            ),
        )
    return items[:3]


def _validate_student_information(form: NewStudentRegistrationFormValues) -> None:
    missing: list[str] = []
    if not form.full_name:
        missing.append("Full name")
    if not form.date_of_birth:
        missing.append("Date of birth")
    if not form.gender:
        missing.append("Gender")
    if not form.mobile:
        missing.append("Mobile")
    if not form.guardian_name:
        missing.append("Guardian name")
    if not form.relationship:
        missing.append("Relationship")
    if not form.guardian_mobile:
        missing.append("Guardian mobile")
    if not form.email or form.email.endswith("@pending.local"):
        missing.append("Email")
    elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", form.email):
        missing.append("Email")
    if missing:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Complete required fields: {', '.join(missing)}",
            status_code=422,
        )


async def _apply_form_to_admission(admission: StudentAdmission, form: NewStudentRegistrationFormValues) -> None:
    admission.applicant_name = form.full_name or admission.applicant_name
    if form.email and not form.email.endswith("@pending.local"):
        admission.applicant_email = form.email.lower()
    meta = dict(admission.metadata or {})
    mapping = {
        "date_of_birth": form.date_of_birth,
        "gender": form.gender,
        "blood_group": form.blood_group,
        "mobile": form.mobile,
        "nationality": form.nationality,
        "community": form.community,
        "category": form.community,
        "guardian_name": form.guardian_name,
        "guardian_mobile": form.guardian_mobile,
        "guardian_occupation": form.occupation,
        "guardian_relationship": form.relationship,
    }
    for k, v in mapping.items():
        if v is not None and v != "":
            meta[k] = v
    admission.metadata = meta
    admission.updated_at = utcnow()


def _page_read(
    *,
    admission: StudentAdmission,
    draft: StudentNewRegistrationDraft,
    programmes: dict[str, AcademicProgramme],
    now,
) -> NewStudentRegistrationPageRead:
    form = _coerce_form_values(draft.values, admission)
    step_key = draft.step_key or "student_information"
    step_index = _step_index(step_key)
    step_label = _WIZARD_STEPS[step_index][1]

    summary = [
        NewStudentRegistrationSummaryItem(
            key="application",
            label="Application",
            value=admission.admission_number,
        ),
        NewStudentRegistrationSummaryItem(
            key="programme",
            label="Programme",
            value=_programme_label(admission.programme_code, programmes),
        ),
        NewStudentRegistrationSummaryItem(
            key="quota",
            label="Quota",
            value=_quota_label(admission) if admission.programme_code else "—",
        ),
        NewStudentRegistrationSummaryItem(
            key="intake",
            label="Intake",
            value=_ay_display(admission.academic_year_code),
        ),
    ]

    return NewStudentRegistrationPageRead(
        admission_id=str(admission.id),
        page_title="New Student Registration",
        page_subtitle=f"Step {step_index + 1} of {len(_WIZARD_STEPS)} · {step_label}",
        back_href="/college-admin/students/student-admission",
        back_label="Back",
        save_draft_label="Save draft",
        continue_label="Continue",
        current_step_key=step_key,
        step_position_label=f"Step {step_index + 1} of {len(_WIZARD_STEPS)} · {step_label}",
        steps=_build_steps(step_key),
        sections=[
            NewStudentRegistrationFormSection(key="personal_details", title="Personal details"),
            NewStudentRegistrationFormSection(key="guardian_details", title="Guardian details"),
        ],
        field_meta=[*_PERSONAL_FIELDS, *_GUARDIAN_FIELDS],
        gender_options=_GENDER_OPTIONS,
        blood_group_options=_BLOOD_GROUP_OPTIONS,
        nationality_options=_NATIONALITY_OPTIONS,
        community_options=_COMMUNITY_OPTIONS,
        relationship_options=_RELATIONSHIP_OPTIONS,
        form=form,
        admission_summary_title="Admission summary",
        admission_summary=summary,
        next_steps_title="Next steps",
        next_steps=_build_next_steps(step_key),
        has_draft=bool(draft.values),
        footer_disclaimer="Live institutional data · Student admissions and records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_new_student_registration_page(
    scope: AccessScope,
    admission_id: str | None = None,
) -> NewStudentRegistrationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None
    now = utcnow()

    admission = await _resolve_admission(tenant_id, actor_id, admission_id)
    draft = await _get_or_create_draft(tenant_id, actor_id, admission.id)
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    programme_by_code = {p.programme_code.upper(): p for p in programmes}

    if not draft.values:
        draft.values = _coerce_form_values({}, admission).model_dump()
        if not (admission.programme_code or "").strip() and programmes:
            admission.programme_code = programmes[0].programme_code
            await admission.save()

    return _page_read(
        admission=admission,
        draft=draft,
        programmes=programme_by_code,
        now=now,
    )


async def save_new_student_registration_draft(
    scope: AccessScope,
    payload: NewStudentRegistrationDraftUpdate,
) -> NewStudentRegistrationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None
    now = utcnow()

    admission_oid = to_object_id(payload.admission_id, "admission id")
    admission = await StudentAdmission.get(admission_oid)
    if admission is None or admission.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Admission not found", status_code=404)

    draft = await _get_or_create_draft(tenant_id, actor_id, admission_oid)
    merged = {**draft.values, **(payload.values or {})}
    draft.values = merged
    form = _coerce_form_values(merged, admission)

    if payload.advance:
        if draft.step_key == "student_information" or payload.step_key == "student_information":
            _validate_student_information(form)
            draft.step_key = "documents"
    elif payload.step_key:
        draft.step_key = payload.step_key

    await _apply_form_to_admission(admission, form)
    await admission.save()
    draft.updated_at = now
    await draft.save()

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    programme_by_code = {p.programme_code.upper(): p for p in programmes}
    return _page_read(admission=admission, draft=draft, programmes=programme_by_code, now=now)