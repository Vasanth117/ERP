"""Aggregate institution overview for college admin dashboard (CA Institutional Overview)."""

from __future__ import annotations

from collections import defaultdict
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.institution_service import get_institution_profile, list_campuses
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicTermSummary,
    CampusOverviewRow,
    ComplianceStatusItem,
    InstitutionalOverviewRead,
    KeyContactItem,
    ProgrammeLevelMixItem,
)
from app.modules.college_admin.identity_models import DepartmentStatus
from app.modules.faculty.models import FacultyProfile
from app.modules.students.models import StudentProfile

_reader = OperationalDataReader()

_LEVEL_LABELS = {
    "undergraduate": "Undergraduate (UG)",
    "postgraduate": "Postgraduate (PG)",
    "doctoral": "Doctoral (Ph.D.)",
    "unassigned": "Not mapped to an active programme",
}


def _programme_level(prog: AcademicProgramme) -> str:
    if prog.duration_semesters <= 4 and prog.credits_required <= 80:
        return "doctoral"
    if prog.duration_semesters <= 6:
        return "postgraduate"
    return "undergraduate"


def _address_label(address) -> str:
    parts = [getattr(address, "city", None), getattr(address, "state", None)]
    return ", ".join(p for p in parts if p) or "—"


async def get_institutional_overview(scope: AccessScope) -> InstitutionalOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)

    profile = await get_institution_profile(scope)
    year, semester = await _reader.current_academic_term(tenant_id)
    statistics = await _reader.headcount_statistics(tenant_id)
    campuses = await list_campuses(scope, active_only=False)
    integration_health = await _reader.integration_health(tenant_id)

    main_campus_id = next((c.campus_id for c in campuses if c.is_main), campuses[0].campus_id if campuses else None)

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()

    dept_to_campuses: dict[PydanticObjectId, list[PydanticObjectId]] = {}
    campus_dept_count: dict[str, int] = defaultdict(int)
    for dept in departments:
        targets = list(dept.campus_ids)
        if not targets and main_campus_id:
            targets = [PydanticObjectId(main_campus_id)]
        dept_to_campuses[dept.id] = targets
        for cid in targets:
            campus_dept_count[str(cid)] += 1

    campus_student_count: dict[str, int] = defaultdict(int)
    students = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    for student in students:
        if student.department_id is None:
            if main_campus_id:
                campus_student_count[main_campus_id] += 1
            continue
        campus_targets = dept_to_campuses.get(student.department_id)
        if not campus_targets:
            if main_campus_id:
                campus_student_count[main_campus_id] += 1
            continue
        for cid in campus_targets:
            campus_student_count[str(cid)] += 1

    campus_rows = [
        CampusOverviewRow(
            campus_id=c.campus_id,
            campus_code=c.campus_code,
            name=c.name,
            is_main=c.is_main,
            is_active=c.is_active,
            location_label=_address_label(c.address),
            student_count=campus_student_count.get(c.campus_id, 0),
            department_count=campus_dept_count.get(c.campus_id, 0),
        )
        for c in campuses
    ]

    programmes = await AcademicProgramme.find(
        Eq(AcademicProgramme.tenant_id, tenant_id),
        Eq(AcademicProgramme.is_active, True),
    ).to_list()
    code_to_level = {p.programme_code.upper(): _programme_level(p) for p in programmes}

    level_agg: dict[str, dict[str, int | set[str]]] = defaultdict(
        lambda: {"students": 0, "programmes": set()},
    )
    for prog in programmes:
        level = code_to_level[prog.programme_code.upper()]
        level_agg[level]["programmes"].add(prog.programme_code.upper())

    for student in students:
        code = (student.programme_code or "").upper()
        level = code_to_level.get(code, "unassigned")
        level_agg[level]["students"] += 1
        if code and level != "unassigned":
            level_agg[level]["programmes"].add(code)

    programme_mix = [
        ProgrammeLevelMixItem(
            level=level,
            label=_LEVEL_LABELS.get(level, level),
            student_count=int(level_agg[level]["students"]),
            programme_count=len(level_agg[level]["programmes"]),
        )
        for level in ("undergraduate", "postgraduate", "doctoral", "unassigned")
        if level_agg[level]["students"] > 0 or level_agg[level]["programmes"]
    ]

    accreditation_summary = profile.affiliation_type or profile.affiliation_name
    accreditation_detail = profile.affiliation_name

    compliance_items: list[ComplianceStatusItem] = []
    compliance_items.append(
        ComplianceStatusItem(
            title="Affiliation registry",
            status_code="valid" if profile.affiliation_id else "pending",
            detail=profile.affiliation_id or "No affiliation identifier on file",
        )
    )
    compliance_items.append(
        ComplianceStatusItem(
            title="Institution profile",
            status_code="valid" if profile.legal_name and profile.institution_code else "pending",
            detail="Registry profile complete" if profile.institution_code else "Institution code not set",
        )
    )
    if year:
        compliance_items.append(
            ComplianceStatusItem(
                title="Academic year context",
                status_code="valid",
                detail=f"{year}" + (f" · {semester}" if semester else ""),
            )
        )
    for item in integration_health:
        code = (
            "valid"
            if item.status.lower() in {"ok", "healthy", "up", "active", "connected"}
            else "pending"
            if item.status.lower() in {"unknown", "degraded"}
            else "due_soon"
        )
        compliance_items.append(
            ComplianceStatusItem(
                title=f"Integration · {item.provider_code}",
                status_code=code,
                detail=item.detail or item.status,
            )
        )

    key_contacts: list[KeyContactItem] = []
    seen_user_ids: set[PydanticObjectId] = set()

    for dept in departments:
        if dept.head_user_id is None or dept.head_user_id in seen_user_ids:
            continue
        user = await User.get(dept.head_user_id)
        if user is None or user.tenant_id != tenant_id:
            continue
        seen_user_ids.add(user.id)
        key_contacts.append(
            KeyContactItem(
                name=user.full_name or user.email,
                role_label=f"Head · {dept.name}",
                email=user.email,
                phone=None,
            )
        )
        if len(key_contacts) >= 6:
            break

    if len(key_contacts) < 6:
        faculty_rows = (
            await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id))
            .sort("+designation")
            .limit(20)
            .to_list()
        )
        for fac in faculty_rows:
            if fac.user_id in seen_user_ids:
                continue
            designation = (fac.designation or "").strip()
            if not designation:
                continue
            user = await User.get(fac.user_id)
            if user is None:
                continue
            seen_user_ids.add(user.id)
            key_contacts.append(
                KeyContactItem(
                    name=user.full_name or user.email,
                    role_label=designation,
                    email=user.email,
                    phone=fac.contact_phone,
                )
            )
            if len(key_contacts) >= 8:
                break

    if not key_contacts and profile.institution_email:
        key_contacts.append(
            KeyContactItem(
                name=profile.display_name,
                role_label="Institution contact",
                email=profile.institution_email,
                phone=profile.contact_phone,
            )
        )

    if not key_contacts:
        admins = await User.find(
            Eq(User.tenant_id, tenant_id),
            Eq(User.role, Role.COLLEGE_ADMIN),
            Eq(User.is_active, True),
        ).limit(3).to_list()
        for admin in admins:
            key_contacts.append(
                KeyContactItem(
                    name=admin.full_name or admin.email,
                    role_label="College administrator",
                    email=admin.email,
                    phone=None,
                )
            )

    return InstitutionalOverviewRead(
        profile=profile,
        academic_term=AcademicTermSummary(
            academic_year_label=year,
            semester_label=semester,
        ),
        statistics=statistics,
        accreditation_summary=accreditation_summary,
        accreditation_detail=accreditation_detail,
        campuses=campus_rows,
        programme_mix=programme_mix,
        compliance_items=compliance_items,
        key_contacts=key_contacts,
        generated_at=utcnow(),
    )