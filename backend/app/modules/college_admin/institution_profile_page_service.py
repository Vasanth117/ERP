"""Institution profile screen aggregation (CA 02.01)."""

from __future__ import annotations

from datetime import datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.institution_service import (
    _ensure_branding,
    _ensure_profile,
    _ensure_settings,
    get_institution_profile,
    list_campuses,
)
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import InstitutionBranding, InstitutionConfigurationVersion, InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionAboutField,
    InstitutionLeadershipRow,
    InstitutionProfilePageRead,
    InstitutionStatusBadge,
    ProfileCompletenessRow,
    RelatedSettingLink,
)
from app.modules.faculty.models import FacultyProfile
from app.modules.tenants.enums import TenantLifecycleStatus
from app.modules.tenants.models import Tenant

_reader = OperationalDataReader()

_LEADERSHIP_DESIGNATIONS = (
    "principal",
    "dean",
    "registrar",
    "controller",
    "finance officer",
    "vice principal",
)


def _address_label(address) -> str:
    parts = [getattr(address, "city", None), getattr(address, "state", None)]
    return ", ".join(p for p in parts if p) or None


def _subtitle_line(profile, tenant: Tenant) -> str | None:
    chunks: list[str] = []
    if profile.institution_type:
        chunks.append(profile.institution_type)
    if profile.affiliation_type:
        chunks.append(profile.affiliation_type)
    elif profile.affiliation_name:
        chunks.append(f"Affiliated to {profile.affiliation_name}")
    year = profile.year_established
    if year:
        chunks.append(f"Est. {year}")
    return " · ".join(chunks) if chunks else None


def _institution_type_label(profile) -> str | None:
    parts = [profile.institution_type, profile.affiliation_type]
    label = " – ".join(p for p in parts if p)
    return label or profile.institution_type


def _accreditation_label(profile) -> str | None:
    if profile.accreditation_display:
        return profile.accreditation_display
    parts = [profile.affiliation_type, profile.affiliation_name]
    return " · ".join(p for p in parts if p) or None


def _joining_detail(role_label: str, joining_raw: str | None) -> str | None:
    if not joining_raw:
        return role_label
    try:
        if joining_raw.endswith("Z"):
            joining_raw = joining_raw.replace("Z", "+00:00")
        joined = datetime.fromisoformat(joining_raw)
        since = joined.strftime("%b %Y")
        return f"{role_label} · since {since}"
    except (TypeError, ValueError):
        return role_label


def _designation_rank(designation: str) -> int:
    lowered = designation.lower()
    for index, token in enumerate(_LEADERSHIP_DESIGNATIONS):
        if token in lowered:
            return index
    return len(_LEADERSHIP_DESIGNATIONS)


async def _load_leadership(
    tenant_id: PydanticObjectId,
    profile,
) -> list[InstitutionLeadershipRow]:
    rows: list[InstitutionLeadershipRow] = []
    seen_user_ids: set[PydanticObjectId] = set()

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()

    for dept in departments:
        if dept.head_user_id is None or dept.head_user_id in seen_user_ids:
            continue
        user = await User.get(dept.head_user_id)
        if user is None or user.tenant_id != tenant_id:
            continue
        seen_user_ids.add(user.id)
        role = f"Head · {dept.name}"
        rows.append(
            InstitutionLeadershipRow(
                name=user.full_name or user.email,
                role_label=role,
                detail_line=role,
            )
        )
        if len(rows) >= 6:
            break

    faculty_rows = (
        await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).sort("+designation").limit(40).to_list()
    )
    candidates: list[tuple[int, InstitutionLeadershipRow]] = []
    for fac in faculty_rows:
        if fac.user_id in seen_user_ids:
            continue
        designation = (fac.designation or "").strip()
        if not designation:
            continue
        lowered = designation.lower()
        if not any(token in lowered for token in _LEADERSHIP_DESIGNATIONS) and len(rows) + len(candidates) >= 8:
            continue
        user = await User.get(fac.user_id)
        if user is None:
            continue
        seen_user_ids.add(user.id)
        join_raw = (fac.employment_snapshot or {}).get("joining_date")
        detail = _joining_detail(designation, str(join_raw) if join_raw else None)
        row = InstitutionLeadershipRow(
            name=user.full_name or user.email,
            role_label=designation,
            detail_line=detail,
        )
        rank = _designation_rank(designation)
        candidates.append((rank, row))

    candidates.sort(key=lambda item: item[0])
    for _, row in candidates:
        if len(rows) >= 8:
            break
        if row.name not in {existing.name for existing in rows}:
            rows.append(row)

    if not rows and profile.institution_email:
        rows.append(
            InstitutionLeadershipRow(
                name=profile.display_name,
                role_label="Institution contact",
                detail_line=profile.institution_email,
            )
        )

    if not rows:
        admins = await User.find(
            Eq(User.tenant_id, tenant_id),
            Eq(User.role, Role.COLLEGE_ADMIN),
            Eq(User.is_active, True),
        ).limit(4).to_list()
        for admin in admins:
            rows.append(
                InstitutionLeadershipRow(
                    name=admin.full_name or admin.email,
                    role_label="College administrator",
                    detail_line=admin.email,
                )
            )
    return rows[:8]


def _status_badges(tenant: Tenant, profile) -> list[InstitutionStatusBadge]:
    badges: list[InstitutionStatusBadge] = []
    if tenant.is_active and tenant.lifecycle_status == TenantLifecycleStatus.ACTIVE:
        badges.append(InstitutionStatusBadge(label="Active tenant", tone="success"))
    elif tenant.lifecycle_status:
        badges.append(
            InstitutionStatusBadge(
                label=tenant.lifecycle_status.value.replace("_", " ").title(),
                tone="warning",
            )
        )
    accreditation = profile.accreditation_display or profile.affiliation_type
    if accreditation:
        badges.append(InstitutionStatusBadge(label=accreditation, tone="info"))
    return badges


def _completeness_rows(
  profile,
  branding: InstitutionBranding,
  campuses,
  settings: InstitutionSettings,
  config_versions: int,
) -> list[ProfileCompletenessRow]:
    basic_checks = [
        profile.legal_name,
        profile.display_name,
        profile.institution_code,
        profile.institution_email,
        profile.contact_phone,
        profile.official_website,
        profile.address.city,
        profile.affiliation_name,
    ]
    basic_done = sum(1 for value in basic_checks if value)
    basic_total = len(basic_checks)

    branding_checks = [
        branding.display_name,
        branding.logo_file_id,
        branding.favicon_file_id,
        branding.primary_color,
        branding.secondary_color,
    ]
    branding_done = sum(1 for value in branding_checks if value)
    branding_total = len(branding_checks)

    if not campuses:
        campus_done, campus_total = 0, 1
    else:
        campus_checks = [
            bool(c.address.city or c.address.line1) and bool(c.contact_phone or c.contact_email)
            for c in campuses
            if c.is_active
        ]
        if not campus_checks:
            campus_checks = [bool(c.address.city or c.address.line1) for c in campuses]
        campus_total = len(campus_checks)
        campus_done = sum(1 for flag in campus_checks if flag)

    policy_flags = settings.settings or {}
    policy_checks = [
        profile.affiliation_id,
        profile.aishe_code,
        policy_flags.get("academic_year_display"),
        policy_flags.get("semester_display"),
        policy_flags.get("grade_display_scale"),
        profile.medium_of_instruction,
        policy_flags.get("inter_batch_section_transfer_requires_college_approval") is not None,
        config_versions > 0,
    ]
    policy_done = sum(1 for value in policy_checks if value)
    policy_total = len(policy_checks)

    def row(key: str, label: str, done: int, total: int) -> ProfileCompletenessRow:
        percent = 100 if total == 0 else round((done / total) * 100)
        status = "Complete" if done >= total and total > 0 else f"{done} of {total}"
        return ProfileCompletenessRow(
            key=key,
            label=label,
            completed_count=done,
            total_count=total,
            progress_percent=percent,
            status_label=status,
        )

    return [
        row("basic_information", "Basic information", basic_done, basic_total),
        row("branding_assets", "Branding & assets", branding_done, branding_total),
        row("campus_details", "Campus details", campus_done, campus_total),
        row("policies_uploaded", "Policies uploaded", policy_done, policy_total),
    ]


async def get_institution_profile_page(scope: AccessScope) -> InstitutionProfilePageRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    profile = await get_institution_profile(scope)
    raw_profile = await _ensure_profile(tenant)
    settings_doc = await _ensure_settings(tenant_id)
    branding = await _ensure_branding(tenant)
    campuses = await list_campuses(scope, active_only=False)
    config_count = await InstitutionConfigurationVersion.find(
        Eq(InstitutionConfigurationVersion.tenant_id, tenant_id),
    ).count()

    year, semester = await _reader.current_academic_term(tenant_id)
    active_campuses = [c for c in campuses if c.is_active]

    about_fields = [
        InstitutionAboutField(label="Institution code", value=profile.institution_code),
        InstitutionAboutField(label="AISHE code", value=profile.aishe_code),
        InstitutionAboutField(label="Affiliating university", value=profile.affiliation_name),
        InstitutionAboutField(
            label="Ownership",
            value=profile.ownership_name or profile.legal_name,
        ),
        InstitutionAboutField(label="Institution type", value=_institution_type_label(profile)),
        InstitutionAboutField(label="AICTE permanent ID", value=profile.affiliation_id),
        InstitutionAboutField(label="Accreditation", value=_accreditation_label(profile)),
        InstitutionAboutField(label="Medium of instruction", value=profile.medium_of_instruction),
    ]

    academic_year_display = settings_doc.settings.get("academic_year_display")
    semester_display = settings_doc.settings.get("semester_display")
    academic_summary = " · ".join(
        part
        for part in (
            academic_year_display or year,
            semester_display or semester,
        )
        if part
    )

    related_settings = [
        RelatedSettingLink(
            key="branding",
            title="College logo & branding",
            description="Logo, colours, letterheads.",
            href="/college-admin/institution/branding",
        ),
        RelatedSettingLink(
            key="campuses",
            title="Campus management",
            description=f"{len(active_campuses)} campus{'es' if len(active_campuses) != 1 else ''}",
            href="/college-admin/institution/campuses",
        ),
        RelatedSettingLink(
            key="academic_year",
            title="Academic year",
            description=academic_summary or "Not configured",
            href="/college-admin/institution/academic-year",
        ),
    ]

    leadership = await _load_leadership(tenant_id, raw_profile)
    completeness = _completeness_rows(raw_profile, branding, campuses, settings_doc, config_count)

    return InstitutionProfilePageRead(
        profile=profile,
        display_name=profile.display_name or profile.legal_name,
        subtitle_line=_subtitle_line(raw_profile, tenant),
        location_label=_address_label(profile.address),
        status_badges=_status_badges(tenant, raw_profile),
        about_fields=about_fields,
        leadership=leadership,
        profile_completeness=completeness,
        related_settings=related_settings,
        branding_primary_color=branding.primary_color,
        branding_logo_file_id=branding.logo_file_id,
        footer_disclaimer=(
            "Live institutional data · Profile, campuses and configuration records · All times IST"
        ),
        generated_at=utcnow(),
    )