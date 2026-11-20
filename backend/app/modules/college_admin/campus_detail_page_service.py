"""Campus details page (buildings, summary, facilities) — CA 02.04 detail."""

from __future__ import annotations

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.campus_ext_models import (
    InstitutionCampusBuilding,
    InstitutionCampusFacilityShowcase,
)
from app.modules.college_admin.campus_shared import campus_staff_counts, campus_student_counts
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBuilding, HostelRoom
from app.modules.college_admin.institution_service import list_campuses
from app.modules.college_admin.models import InstitutionCampus
from app.modules.college_admin.operations_ext_models import InstitutionFacility
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CampusBuildingRow,
    CampusDetailPageRead,
    CampusFacilityStatusRow,
    CampusSummaryStat,
)


async def _resolve_campus(scope: AccessScope, campus_id: PydanticObjectId) -> InstitutionCampus:
    tenant_id = require_college_tenant_scope(scope)
    campus = await InstitutionCampus.find_one(
        Eq(InstitutionCampus.tenant_id, tenant_id),
        Eq(InstitutionCampus.id, campus_id),
    )
    if campus is None:
        raise AppError(code="NOT_FOUND", message="Campus not found", status_code=404)
    return campus


def _format_count(value: int | None) -> str:
    if value is None:
        return "—"
    return f"{value:,}"


async def get_campus_detail_page(scope: AccessScope, campus_id: PydanticObjectId) -> CampusDetailPageRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)
    campus = await _resolve_campus(scope, campus_id)
    campus_key = str(campus.id)

    building_rows = await InstitutionCampusBuilding.find(
        Eq(InstitutionCampusBuilding.tenant_id, tenant_id),
        Eq(InstitutionCampusBuilding.campus_id, campus.id),
    ).sort("+sort_order").to_list()
    buildings_total = len(building_rows)
    shown_limit = 6
    building_slice = building_rows[:shown_limit]

    buildings = [
        CampusBuildingRow(
            building_id=row.building_id,
            name=row.name,
            floors=row.floors,
            classroom_count=row.classroom_count,
            laboratory_count=row.laboratory_count,
            departments_label=row.departments_label or "—",
        )
        for row in building_slice
    ]

    facilities = await InstitutionFacility.find(
        Eq(InstitutionFacility.tenant_id, tenant_id),
        Eq(InstitutionFacility.campus_id, campus.id),
        Eq(InstitutionFacility.active, True),
    ).to_list()
    classrooms = sum(1 for f in facilities if f.facility_type == "classroom")
    laboratories = sum(1 for f in facilities if f.facility_type == "laboratory")

    campuses = await list_campuses(scope, active_only=False)
    main_id = next((c.campus_id for c in campuses if c.is_main), campus_key)
    student_counts = await campus_student_counts(tenant_id, [c.campus_id for c in campuses] or [main_id])
    students = student_counts.get(campus_key, 0)
    staff = await campus_staff_counts(tenant_id, campus.id)

    hostel_rooms = await HostelRoom.find(Eq(HostelRoom.tenant_id, tenant_id)).to_list()
    hostel_buildings = await HostelBuilding.find(
        Eq(HostelBuilding.tenant_id, tenant_id),
        Eq(HostelBuilding.campus_id, campus.id),
    ).to_list()
    building_codes = {b.building_code for b in hostel_buildings}
    campus_rooms = [r for r in hostel_rooms if r.building_code in building_codes]
    beds = await HostelBed.find(Eq(HostelBed.tenant_id, tenant_id)).count()
    if campus_rooms:
        beds = sum(r.bed_capacity for r in campus_rooms)
    elif beds and not hostel_buildings:
        pass
    elif not beds:
        beds = sum(r.bed_capacity for r in hostel_rooms)

    parking = campus.parking_slots

    summary_stats = [
        CampusSummaryStat(key="students", label="Students", value=_format_count(students)),
        CampusSummaryStat(key="staff", label="Faculty & staff", value=_format_count(staff)),
        CampusSummaryStat(key="classrooms", label="Classrooms", value=_format_count(classrooms)),
        CampusSummaryStat(key="laboratories", label="Laboratories", value=_format_count(laboratories)),
        CampusSummaryStat(key="hostel_beds", label="Hostel beds", value=_format_count(beds)),
        CampusSummaryStat(key="parking", label="Parking slots", value=_format_count(parking)),
    ]

    showcase_docs = await InstitutionCampusFacilityShowcase.find(
        Eq(InstitutionCampusFacilityShowcase.tenant_id, tenant_id),
        Eq(InstitutionCampusFacilityShowcase.campus_id, campus.id),
    ).sort("+sort_order").to_list()

    facility_statuses: list[CampusFacilityStatusRow] = [
        CampusFacilityStatusRow(
            showcase_id=doc.showcase_id,
            title=doc.title,
            subtitle=doc.subtitle,
            status_code=doc.status_code,
            status_label=doc.status_label,
            icon_slug=doc.icon_slug,
        )
        for doc in showcase_docs
    ]

    if not facility_statuses:
        icon_by_type = {
            "library": "library-big",
            "health": "heart-pulse",
            "health_centre": "heart-pulse",
            "sports": "dumbbell",
            "sports_complex": "dumbbell",
        }
        for fac in facilities:
            slug = icon_by_type.get(fac.facility_type)
            if slug is None and fac.facility_type not in {
                "library",
                "health",
                "health_centre",
                "sports",
                "sports_complex",
                "auditorium",
            }:
                continue
            slug = slug or "landmark"
            capacity = f"{fac.capacity:,} capacity" if fac.capacity else ""
            facility_statuses.append(
                CampusFacilityStatusRow(
                    showcase_id=fac.facility_id,
                    title=fac.name,
                    subtitle=capacity or fac.facility_type.replace("_", " ").title(),
                    status_code="open" if fac.active else "closed",
                    status_label="Open" if fac.active else "Closed",
                    icon_slug=slug,
                )
            )

    footer = f"{buildings_total} building{'s' if buildings_total != 1 else ''}"
    if buildings_total > shown_limit:
        footer += f" · {len(buildings)} shown"

    return CampusDetailPageRead(
        page_title=campus.name,
        campus_id=campus_key,
        campus_name=campus.name,
        back_href="/college-admin/institution/campuses",
        contact_href=f"/college-admin/institution/campuses/{campus_key}/contact",
        buildings=buildings,
        buildings_total=buildings_total,
        buildings_shown=len(buildings),
        buildings_footer_label=footer,
        manage_buildings_href="/college-admin/operations/building-infrastructure-management",
        view_all_buildings_href=(
            f"/college-admin/operations/building-infrastructure-management?campus_id={campus_key}"
        ),
        summary_stats=summary_stats,
        facility_statuses=facility_statuses,
        generated_at=utcnow(),
    )