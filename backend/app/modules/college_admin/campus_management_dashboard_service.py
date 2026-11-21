"""Campus management dashboard (CA 02.04)."""

from __future__ import annotations

from collections import defaultdict

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBuilding, HostelRoom
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.institution_service import list_campuses
from app.modules.college_admin.library_admin_models import LibraryBranch
from app.modules.college_admin.models import InstitutionCampus
from app.modules.college_admin.operations_ext_models import InstitutionFacility, InstitutionMaintenanceRequest, MaintenanceStatus
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CampusDashboardKpi,
    CampusDashboardRow,
    CampusFacilitySummary,
    CampusManagementDashboardRead,
    CampusOpenIssue,
    ClassroomUtilizationBar,
)
from app.modules.students.models import StudentProfile


def _address_label(address) -> str:
    parts = [getattr(address, "city", None), getattr(address, "state", None)]
    return ", ".join(p for p in parts if p) or "—"


def _format_area(acres: float) -> str:
    if acres == int(acres):
        return f"{int(acres)} acres"
    return f"{acres:.1f} acres"


def _format_sq_m(value: float) -> str:
    if value >= 100_000:
        lakh = value / 100_000
        return f"{lakh:.1f} lakh sq. m built-up"
    return f"{int(value):,} sq. m built-up"


async def _campus_student_counts(tenant_id: PydanticObjectId, campuses: list) -> dict[str, int]:
    main_campus_id = next((c.campus_id for c in campuses if c.is_main), campuses[0].campus_id if campuses else None)
    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_to_campuses: dict[PydanticObjectId, list[PydanticObjectId]] = {}
    for dept in departments:
        targets = list(dept.campus_ids)
        if not targets and main_campus_id:
            targets = [PydanticObjectId(main_campus_id)]
        dept_to_campuses[dept.id] = targets

    counts: dict[str, int] = defaultdict(int)
    students = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    for student in students:
        if student.department_id is None:
            if main_campus_id:
                counts[main_campus_id] += 1
            continue
        campus_targets = dept_to_campuses.get(student.department_id)
        if not campus_targets:
            if main_campus_id:
                counts[main_campus_id] += 1
            continue
        for cid in campus_targets:
            counts[str(cid)] += 1
    return counts


async def get_campus_management_dashboard(scope: AccessScope) -> CampusManagementDashboardRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)

    campuses = await list_campuses(scope, active_only=False)
    campus_docs = await InstitutionCampus.find(Eq(InstitutionCampus.tenant_id, tenant_id)).to_list()
    doc_by_id = {str(doc.id): doc for doc in campus_docs}
    student_counts = await _campus_student_counts(tenant_id, campuses)

    facilities = await InstitutionFacility.find(
        Eq(InstitutionFacility.tenant_id, tenant_id),
        Eq(InstitutionFacility.active, True),
    ).to_list()

    classrooms = [f for f in facilities if f.facility_type == "classroom"]
    laboratories = [f for f in facilities if f.facility_type == "laboratory"]
    buildings = [f for f in facilities if f.facility_type in {"building", "block"}]

    open_maintenance = await InstitutionMaintenanceRequest.find(
        Eq(InstitutionMaintenanceRequest.tenant_id, tenant_id),
        In(
            InstitutionMaintenanceRequest.status,
            [
                MaintenanceStatus.OPEN,
                MaintenanceStatus.ASSIGNED,
                MaintenanceStatus.IN_PROGRESS,
            ],
        ),
    ).to_list()
    lab_maintenance = sum(
        1
        for m in open_maintenance
        if "lab" in m.title.lower() or (m.facility_id and "lab" in m.facility_id.lower())
    )
    if not lab_maintenance:
        lab_maintenance = sum(1 for f in laboratories if not f.active or f.utilization_percent == 0)

    avg_util = 0
    if classrooms:
        avg_util = round(sum(f.utilization_percent for f in classrooms) / len(classrooms))

    total_acres = sum((doc.area_acres or 0) for doc in campus_docs)
    total_sq_m = sum((doc.built_up_sq_m or 0) for doc in campus_docs)

    campus_names = " · ".join(c.name for c in campuses[:2] if c.is_active)
    if len(campuses) > 2:
        campus_names += f" · +{len(campuses) - 2} more"

    kpis = [
        CampusDashboardKpi(
            key="campuses",
            label="Campuses",
            value=str(len([c for c in campuses if c.is_active])),
            hint=campus_names or "No active campuses",
        ),
        CampusDashboardKpi(
            key="total_area",
            label="Total area",
            value=_format_area(total_acres) if total_acres else "—",
            hint=_format_sq_m(total_sq_m) if total_sq_m else "Area not recorded",
        ),
        CampusDashboardKpi(
            key="classrooms",
            label="Classrooms",
            value=str(len(classrooms)),
            hint=f"{avg_util}% utilisation this week" if classrooms else "No classroom facilities registered",
            hint_tone="success" if avg_util >= 80 else "warning" if classrooms else "muted",
        ),
        CampusDashboardKpi(
            key="laboratories",
            label="Laboratories",
            value=str(len(laboratories)),
            hint=(
                f"{lab_maintenance} under maintenance"
                if lab_maintenance
                else "All laboratories operational"
            ),
            hint_tone="warning" if lab_maintenance else "muted",
        ),
    ]

    def buildings_for(campus_id: str) -> int:
        doc = doc_by_id.get(campus_id)
        if doc and doc.buildings_count is not None:
            return doc.buildings_count
        return sum(
            1
            for f in buildings
            if f.campus_id and str(f.campus_id) == campus_id
        )

    rows = [
        CampusDashboardRow(
            campus_id=c.campus_id,
            name=c.name,
            location_label=_address_label(c.address),
            student_count=student_counts.get(c.campus_id, 0),
            buildings_count=buildings_for(c.campus_id),
            status_code="active" if c.is_active else "inactive",
            status_label="Active" if c.is_active else "Inactive",
            detail_href=f"/college-admin/institution/campuses/{c.campus_id}",
        )
        for c in campuses
    ]

    chart_sources = buildings if buildings else classrooms
    utilization_bars = sorted(
        [
            ClassroomUtilizationBar(
                building_label=f.name,
                utilization_percent=int(round(f.utilization_percent)),
                tone="warning" if f.utilization_percent < 80 else "primary",
            )
            for f in chart_sources
        ],
        key=lambda bar: bar.utilization_percent,
        reverse=True,
    )[:8]

    hostel_buildings = await HostelBuilding.find(Eq(HostelBuilding.tenant_id, tenant_id)).to_list()
    hostel_rooms = await HostelRoom.find(Eq(HostelRoom.tenant_id, tenant_id)).to_list()
    hostel_blocks = len(hostel_buildings) or len({r.building_code for r in hostel_rooms if r.building_code})
    beds = await HostelBed.find(Eq(HostelBed.tenant_id, tenant_id)).count()
    if not beds:
        beds = sum(r.bed_capacity for r in hostel_rooms)

    library_branches = await LibraryBranch.find(
        Eq(LibraryBranch.tenant_id, tenant_id),
        Eq(LibraryBranch.is_active, True),
    ).to_list()
    library_desc = (
        f"{'Central' if len(library_branches) == 1 else 'Central'} + {max(0, len(library_branches) - 1)} department libraries"
        if len(library_branches) > 1
        else (library_branches[0].name if library_branches else "No library branches registered")
    )

    auditoriums = [f for f in facilities if f.facility_type == "auditorium"]
    auditorium_desc = (
        " · ".join(f"{f.capacity or '—'} seats" for f in auditoriums[:2])
        if auditoriums
        else "No auditoriums registered"
    )
    if len(auditoriums) >= 2:
        auditorium_desc = f"{len(auditoriums)} · {auditorium_desc}"

    transport = [f for f in facilities if f.facility_type in {"transport", "fleet"}]
    transport_desc = (
        f"{len(transport)} fleet entries registered"
        if transport
        else "No transport fleet registered"
    )
    if transport:
        routes = sum(int(f.capacity or 0) for f in transport)
        if routes:
            transport_desc = f"{len(transport)} buses · {routes} routes"

    facility_summaries = [
        CampusFacilitySummary(
            key="hostels",
            title="Hostels",
            description=f"{hostel_blocks or len(hostel_buildings)} blocks · {beds} beds",
            icon_slug="hotel",
        ),
        CampusFacilitySummary(
            key="library",
            title="Library",
            description=library_desc,
            icon_slug="library-big",
        ),
        CampusFacilitySummary(
            key="auditoriums",
            title="Auditoriums",
            description=auditorium_desc,
            icon_slug="landmark",
        ),
        CampusFacilitySummary(
            key="transport",
            title="Transport",
            description=transport_desc,
            icon_slug="map-pin",
        ),
    ]

    issues: list[CampusOpenIssue] = []
    for item in sorted(open_maintenance, key=lambda row: row.created_at, reverse=True)[:5]:
        status = item.status.value if hasattr(item.status, "value") else str(item.status)
        tone = "info" if status in {"open", "assigned"} and "planned" in item.title.lower() else "warning"
        status_label = (
            "Scheduled"
            if "planned" in item.title.lower() or status == "open"
            else "In progress"
        )
        if status == MaintenanceStatus.IN_PROGRESS.value:
            status_label = "In progress"
            tone = "warning"
        issues.append(
            CampusOpenIssue(
                issue_id=item.request_id,
                title=item.title,
                raised_label=f"Raised {item.created_at.strftime('%d %b')}",
                status_code=status,
                status_label=status_label,
                tone=tone,
            )
        )

    first_campus = campuses[0].campus_id if campuses else ""

    return CampusManagementDashboardRead(
        page_title="Campus Management Dashboard",
        page_subtitle="Overview of all campuses, capacity and facilities",
        export_label="Export",
        add_campus_label="Add campus",
        kpis=kpis,
        campuses=rows,
        campus_count_label=f"{len(campuses)} campus{'es' if len(campuses) != 1 else ''}",
        campuses_view_all_href="/college-admin/institution/campuses",
        campus_details_href=(
            f"/college-admin/institution/campuses/{first_campus}" if first_campus else "/college-admin/institution/campuses"
        ),
        classroom_utilization=utilization_bars,
        classroom_utilization_hint=(
            f"{avg_util}% average classroom utilisation"
            if classrooms
            else None
        ),
        facilities=facility_summaries,
        open_issues=issues,
        operations_href="/college-admin/operations",
        add_campus_href="/college-admin/institution/campuses#add-campus",
        footer_disclaimer=(
            "Live institutional data · Campuses, facilities and maintenance records · All times IST"
        ),
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )