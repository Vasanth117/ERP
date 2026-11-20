"""Department resource management page (CA 04.10 — organization / faculty & resources)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.finance_ext_models import (
    BudgetStatus,
    DepartmentBudgetAllocation,
    ExpenseStatus,
    InstitutionBudget,
    InstitutionExpenseRecord,
    InstitutionPurchaseRequest,
    PurchaseRequestStatus,
)
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.institution_service import _ensure_settings
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.operations_ext_models import (
    AssetStatus,
    InstitutionAssetAllocation,
    InstitutionAssetRecord,
    InstitutionFacility,
    InstitutionMaintenanceRequest,
    MaintenanceStatus,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    DepartmentResourceBudgetBar,
    DepartmentResourceKpiCard,
    DepartmentResourceLabRow,
    DepartmentResourceManagementPageRead,
    DepartmentResourceOpenRequestItem,
    DepartmentResourceTab,
    InstitutionFieldOption,
)
from app.modules.department_admin.models import DepartmentRequestStatus, DepartmentResourceRequest

_IST = ZoneInfo("Asia/Kolkata")
_MAX_TABS = 5
_LAB_PREVIEW = 6
_OPEN_MAINTENANCE = frozenset(
    {
        MaintenanceStatus.OPEN,
        MaintenanceStatus.ASSIGNED,
        MaintenanceStatus.IN_PROGRESS,
    }
)
_SPENT_STATUSES = frozenset({ExpenseStatus.APPROVED, ExpenseStatus.PAID, ExpenseStatus.PENDING_APPROVAL})
_reader = OperationalDataReader()


def _format_inr(amount: float) -> str:
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.1f} Cr"
    if amount >= 100_000:
        whole = amount / 100_000
        if whole >= 10:
            return f"₹{whole:.0f} L"
        return f"₹{whole:.1f} lakh"
    return f"₹{amount:,.0f}"


def _facility_ids_for_department(
    dept: InstitutionDepartment,
    facilities: list[InstitutionFacility],
    allocations: list[InstitutionAssetAllocation],
    settings_map: dict[str, list[str]],
) -> set[str]:
    did = str(dept.id)
    linked = {a.facility_id for a in allocations if a.department_id == dept.id and a.facility_id and a.active}
    for fid in settings_map.get(did, []):
        linked.add(fid)
    code = (dept.department_code or "").upper()
    if not linked and code:
        for fac in facilities:
            key = fac.facility_id.upper()
            if key.startswith(code) or code in fac.name.upper():
                linked.add(fac.facility_id)
    return linked


def _expense_bucket(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ("gpu", "server", "equipment", "instrument", "purchase")):
        return "equipment"
    if any(k in t for k in ("consumable", "chemical", "reagent")):
        return "consumables"
    if any(k in t for k in ("software", "licence", "license", "subscription")):
        return "software"
    if any(k in t for k in ("event", "workshop", "seminar")):
        return "events"
    return "equipment"


async def get_department_resource_management_page(
    scope: AccessScope,
    *,
    department_id: str | None = None,
    view: str | None = None,
) -> DepartmentResourceManagementPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    settings_doc = await _ensure_settings(tenant_id)
    org_settings = settings_doc.settings.get("organization")
    org_settings = org_settings if isinstance(org_settings, dict) else {}
    facility_map_raw = org_settings.get("resource_facilities_by_department")
    facility_map: dict[str, list[str]] = {}
    if isinstance(facility_map_raw, dict):
        facility_map = {str(k): [str(x) for x in v if x is not None] for k, v in facility_map_raw.items() if isinstance(v, list)}

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).sort("+department_code").to_list()
    if not departments:
        raise AppError(code="NOT_FOUND", message="No active departments", status_code=404)

    selected: InstitutionDepartment | None = None
    if department_id:
        oid = to_object_id(department_id, "department_id")
        selected = next((d for d in departments if d.id == oid), None)
        if selected is None:
            raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)
    else:
        selected = departments[0]

    facilities = await InstitutionFacility.find(
        Eq(InstitutionFacility.tenant_id, tenant_id),
        Eq(InstitutionFacility.active, True),
    ).to_list()
    allocations = await InstitutionAssetAllocation.find(
        Eq(InstitutionAssetAllocation.tenant_id, tenant_id),
        Eq(InstitutionAssetAllocation.active, True),
    ).to_list()
    maintenance = await InstitutionMaintenanceRequest.find(Eq(InstitutionMaintenanceRequest.tenant_id, tenant_id)).to_list()
    assets = await InstitutionAssetRecord.find(Eq(InstitutionAssetRecord.tenant_id, tenant_id)).to_list()

    linked_ids = _facility_ids_for_department(selected, facilities, allocations, facility_map)
    fac_by_id = {f.facility_id: f for f in facilities}
    maint_by_facility = defaultdict(int)
    for req in maintenance:
        if req.facility_id and req.status in _OPEN_MAINTENANCE:
            maint_by_facility[req.facility_id] += 1

    classrooms = [f for f in facilities if f.facility_type == "classroom" and f.facility_id in linked_ids]
    labs = [f for f in facilities if f.facility_type == "laboratory" and f.facility_id in linked_ids]
    labs_maint = sum(1 for lab in labs if maint_by_facility.get(lab.facility_id))
    smart_count = sum(1 for c in classrooms if "smart" in c.name.lower())

    dept_assets = [a for a in assets if a.owner_department_id == selected.id and a.status != AssetStatus.RETIRED]
    asset_ids_at_fac = defaultdict(int)
    gpu_extra = 0
    for alloc in allocations:
        if alloc.department_id != selected.id or not alloc.active:
            continue
        if alloc.facility_id:
            asset_ids_at_fac[alloc.facility_id] += 1
    for asset in dept_assets:
        if "gpu" in asset.name.lower() or "gpu" in asset.category.lower():
            gpu_extra += 1
    book_value = sum(a.financial_value for a in dept_assets)

    active_budget = await InstitutionBudget.find_one(
        Eq(InstitutionBudget.tenant_id, tenant_id),
        Eq(InstitutionBudget.status, BudgetStatus.ACTIVE),
        Eq(InstitutionBudget.enabled, True),
    )
    budget_label = active_budget.label if active_budget else "Annual budget"
    year_label, _ = await _reader.current_academic_term(tenant_id)
    if active_budget:
        budget_section_title = f"Budget {active_budget.fiscal_year}"
    elif year_label:
        budget_section_title = f"Budget {year_label}"
    else:
        budget_section_title = budget_label

    allocated = utilized = 0.0
    if active_budget:
        alloc_doc = await DepartmentBudgetAllocation.find_one(
            Eq(DepartmentBudgetAllocation.tenant_id, tenant_id),
            Eq(DepartmentBudgetAllocation.budget_id, active_budget.budget_id),
            Eq(DepartmentBudgetAllocation.department_id, selected.id),
        )
        if alloc_doc:
            allocated = alloc_doc.allocated_amount
            utilized = alloc_doc.utilized_amount

    if allocated <= 0 and active_budget:
        allocated = sum(
            a.allocated_amount
            for a in await DepartmentBudgetAllocation.find(
                Eq(DepartmentBudgetAllocation.tenant_id, tenant_id),
                Eq(DepartmentBudgetAllocation.department_id, selected.id),
            ).to_list()
        )

    expenses = await InstitutionExpenseRecord.find(
        Eq(InstitutionExpenseRecord.tenant_id, tenant_id),
        Eq(InstitutionExpenseRecord.department_id, selected.id),
    ).to_list()
    spent_by_bucket: dict[str, float] = defaultdict(float)
    for exp in expenses:
        if exp.status not in _SPENT_STATUSES:
            continue
        spent_by_bucket[_expense_bucket(exp.title)] += exp.amount
    if utilized <= 0 and spent_by_bucket:
        utilized = sum(spent_by_bucket.values())

    pct_used = round((utilized / allocated) * 100) if allocated > 0 else 0
    default_splits = org_settings.get("department_budget_category_splits")
    splits: dict[str, float] = {}
    if isinstance(default_splits, dict):
        splits = {str(k): float(v) for k, v in default_splits.items() if v is not None}

    def category_cap(key: str) -> float:
        if splits and key in splits and allocated > 0:
            return allocated * splits[key]
        return allocated * 0.25 if allocated > 0 else 0.0

    budget_bars = [
        DepartmentResourceBudgetBar(
            key="equipment",
            label="Equipment",
            spent_label=_format_inr(spent_by_bucket["equipment"]),
            cap_label=_format_inr(category_cap("equipment")),
            spent_amount=spent_by_bucket["equipment"],
            cap_amount=category_cap("equipment"),
        ),
        DepartmentResourceBudgetBar(
            key="consumables",
            label="Consumables",
            spent_label=_format_inr(spent_by_bucket["consumables"]),
            cap_label=_format_inr(category_cap("consumables")),
            spent_amount=spent_by_bucket["consumables"],
            cap_amount=category_cap("consumables"),
        ),
        DepartmentResourceBudgetBar(
            key="software",
            label="Software licences",
            spent_label=_format_inr(spent_by_bucket["software"]),
            cap_label=_format_inr(category_cap("software")),
            spent_amount=spent_by_bucket["software"],
            cap_amount=category_cap("software"),
        ),
        DepartmentResourceBudgetBar(
            key="events",
            label="Events & workshops",
            spent_label=_format_inr(spent_by_bucket["events"]),
            cap_label=_format_inr(category_cap("events")),
            spent_amount=spent_by_bucket["events"],
            cap_amount=category_cap("events"),
        ),
    ]

    lab_rows: list[DepartmentResourceLabRow] = []
    for lab in sorted(labs, key=lambda f: f.name):
        room = lab.facility_id
        capacity = lab.capacity or 0
        systems = asset_ids_at_fac.get(lab.facility_id) or capacity
        systems_label = str(systems)
        if lab.facility_id and gpu_extra > 0 and "ai" in lab.name.lower():
            systems_label = f"{systems} + {min(gpu_extra, 4)} GPU"
        in_maint = maint_by_facility.get(lab.facility_id, 0) > 0
        lab_rows.append(
            DepartmentResourceLabRow(
                lab_id=lab.facility_id,
                lab_name=lab.name,
                room_label=room,
                capacity=capacity,
                systems_label=systems_label,
                status_code="maintenance" if in_maint else "available",
                status_label="Maintenance" if in_maint else "Available",
                status_tone="warning" if in_maint else "success",
            )
        )

    classroom_subtitle = org_settings.get("classroom_quality_note")
    if not classroom_subtitle:
        classroom_subtitle = "All smart classrooms" if smart_count and smart_count >= len(classrooms) else "Teaching spaces"
    lab_subtitle = f"{labs_maint} under maintenance" if labs_maint else "All operational"
    lab_subtitle_tone = "warning" if labs_maint else "success"

    open_items: list[DepartmentResourceOpenRequestItem] = []
    purchase_rows = await InstitutionPurchaseRequest.find(
        Eq(InstitutionPurchaseRequest.tenant_id, tenant_id),
        Eq(InstitutionPurchaseRequest.department_id, selected.id),
    ).to_list()
    for pr in purchase_rows:
        if pr.status in {PurchaseRequestStatus.REJECTED, PurchaseRequestStatus.ORDERED, PurchaseRequestStatus.DRAFT}:
            continue
        tag = "With finance" if pr.status == PurchaseRequestStatus.SUBMITTED else "Pending"
        tone = "info" if pr.status == PurchaseRequestStatus.SUBMITTED else "warning"
        kind = "purchase" if pr.estimated_amount >= 100_000 else "maintenance"
        if "projector" in pr.description.lower() or "maintenance" in (pr.reason or "").lower():
            kind = "maintenance"
        open_items.append(
            DepartmentResourceOpenRequestItem(
                request_id=pr.request_id,
                title=pr.description[:120],
                detail_line=f"{_format_inr(pr.estimated_amount)} • {kind}",
                status_tag=tag,
                status_tone=tone,
            )
        )

    central_id = selected.central_department_id
    if central_id:
        dept_resource_reqs = await DepartmentResourceRequest.find(
            Eq(DepartmentResourceRequest.tenant_id, tenant_id),
            Eq(DepartmentResourceRequest.central_department_id, central_id),
        ).to_list()
        for req in dept_resource_reqs:
            if req.status not in {DepartmentRequestStatus.PENDING, DepartmentRequestStatus.APPROVED}:
                continue
            open_items.append(
                DepartmentResourceOpenRequestItem(
                    request_id=str(req.id),
                    title=req.resource_name or req.resource_ref,
                    detail_line=req.reason[:80] if req.reason else req.urgency,
                    status_tag="Pending" if req.status == DepartmentRequestStatus.PENDING else "Approved",
                    status_tone="warning" if req.status == DepartmentRequestStatus.PENDING else "info",
                )
            )

    open_items = open_items[:6]

    tab_items: list[DepartmentResourceTab] = []
    for dept in departments[:_MAX_TABS]:
        tab_items.append(
            DepartmentResourceTab(
                department_id=str(dept.id),
                label=dept.department_code if len(dept.name) > 24 else dept.name,
                short_label=dept.department_code,
            )
        )
    more_options: list[InstitutionFieldOption] = []
    if len(departments) > _MAX_TABS:
        for dept in departments[_MAX_TABS:]:
            more_options.append(InstitutionFieldOption(value=str(dept.id), label=dept.name))

    kpis = [
        DepartmentResourceKpiCard(
            key="classrooms",
            title="Classrooms",
            value=str(len(classrooms)),
            subtitle=classroom_subtitle,
            subtitle_tone="success",
        ),
        DepartmentResourceKpiCard(
            key="laboratories",
            title="Laboratories",
            value=str(len(labs)),
            subtitle=lab_subtitle,
            subtitle_tone=lab_subtitle_tone,
        ),
        DepartmentResourceKpiCard(
            key="equipment",
            title="Equipment assets",
            value=f"{len(dept_assets):,}",
            subtitle=f"{_format_inr(book_value)} book value",
            subtitle_tone="muted",
        ),
        DepartmentResourceKpiCard(
            key="budget",
            title="Budget used",
            value=f"{pct_used}%",
            subtitle=f"{_format_inr(utilized)} of {_format_inr(allocated)}" if allocated else "Not allocated",
            subtitle_tone="muted",
        ),
    ]

    generated = utcnow()
    updated_label = generated.astimezone(_IST).strftime("Updated %H:%M IST")
    footer_disclaimer = org_settings.get("resource_footer_disclaimer") or (
        "Illustrative data only · No live student, faculty or finance records · All times IST"
    )
    request_href = f"/college-admin/finance-extensions/purchase-requests?departmentId={selected.id}"
    lab_preview = len(lab_rows) if (view or "").lower() == "labs" else min(len(lab_rows), _LAB_PREVIEW)
    view_all_href = f"/college-admin/organization/department-resource-management?departmentId={selected.id}&view=labs"
    faculty_href = "/college-admin/organization/department-faculty-allocation"

    return DepartmentResourceManagementPageRead(
        page_title="Department Resource Management",
        page_subtitle="Classrooms, labs, equipment and budgets owned by each department",
        request_resource_label="+ Request resource",
        request_resource_href=request_href,
        faculty_nav_label="Faculty",
        faculty_nav_href=faculty_href,
        updated_at_label=updated_label,
        department_tabs=tab_items,
        more_departments_label="More…",
        more_department_options=more_options,
        selected_department_id=str(selected.id),
        kpi_cards=kpis,
        laboratories_section_title="Laboratories",
        laboratories_table_headers=["Lab", "Room", "Capacity", "Systems", "Status"],
        laboratory_rows=lab_rows[:lab_preview],
        laboratories_footer_count_label=f"{len(labs)} labs",
        laboratories_view_all_label="View all",
        laboratories_view_all_href=view_all_href if len(labs) > _LAB_PREVIEW and (view or "").lower() != "labs" else None,
        budget_section_title=budget_section_title,
        budget_bars=budget_bars,
        open_requests_section_title="Open requests",
        open_requests=open_items,
        footer_disclaimer=footer_disclaimer,
        footer_snapshot_label="Sample snapshot",
        generated_at=generated,
    )