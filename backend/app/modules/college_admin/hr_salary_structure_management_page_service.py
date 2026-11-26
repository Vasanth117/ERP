"""HR salary structure management (CA 11 — Salary Structure Management)."""

from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.hr_payroll_shared import HR_PAYROLL_SUB_NAV
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrSalaryStructureManagementPageRead,
    HrSalaryStructureTableRow,
    PoliciesPagination,
)
from app.modules.hr.enums import HrSalaryAssignmentStatus, HrSalaryTemplateStatus
from app.modules.hr.salary_structure_models import HrEmployeeSalaryAssignment, HrSalaryTemplate

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _applies_to_label(template_kind: str) -> str:
    kind = (template_kind or "staff").replace("_", " ").strip()
    return kind.title()


def _status_presentation(status: HrSalaryTemplateStatus) -> tuple[str, str]:
    if status == HrSalaryTemplateStatus.ACTIVE:
        return "Active", "success"
    if status == HrSalaryTemplateStatus.INACTIVE:
        return "Inactive", "muted"
    return status.value.replace("_", " ").title(), "muted"


async def get_hr_salary_structure_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HrSalaryStructureManagementPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    templates = await HrSalaryTemplate.find(Eq(HrSalaryTemplate.tenant_id, tenant_id)).sort("-updated_at").to_list()
    latest_by_code: dict[str, HrSalaryTemplate] = {}
    for tpl in templates:
        existing = latest_by_code.get(tpl.template_code)
        if existing is None or tpl.version > existing.version:
            latest_by_code[tpl.template_code] = tpl

    active_templates = [t for t in latest_by_code.values() if t.status == HrSalaryTemplateStatus.ACTIVE]
    template_ids = [t.id for t in active_templates]

    assignments = (
        await HrEmployeeSalaryAssignment.find(
            Eq(HrEmployeeSalaryAssignment.tenant_id, tenant_id),
            In(HrEmployeeSalaryAssignment.template_id, template_ids),
            Eq(HrEmployeeSalaryAssignment.status, HrSalaryAssignmentStatus.ACTIVE),
        ).to_list()
        if template_ids
        else []
    )
    employees_by_template: dict[str, int] = {}
    effective_by_template: dict[str, datetime] = {}
    for asn in assignments:
        key = str(asn.template_id)
        employees_by_template[key] = employees_by_template.get(key, 0) + 1
        eff_dt = datetime.combine(asn.effective_from, datetime.min.time())
        prev = effective_by_template.get(key)
        if prev is None or eff_dt < prev:
            effective_by_template[key] = eff_dt

    table_rows: list[HrSalaryStructureTableRow] = []
    for tpl in sorted(active_templates, key=lambda t: t.title.lower()):
        emp_count = employees_by_template.get(str(tpl.id), 0)
        eff = effective_by_template.get(str(tpl.id)) or tpl.created_at
        eff_label = eff.astimezone(_IST).strftime("%d %b %Y")
        status_label, status_tone = _status_presentation(tpl.status)
        table_rows.append(
            HrSalaryStructureTableRow(
                structure_id=str(tpl.id),
                structure_label=tpl.title,
                applies_to_label=_applies_to_label(tpl.template_kind),
                components_count=len(tpl.component_lines),
                employees_count=emp_count,
                effective_label=eff_label,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hr/salary-structure-management?structure_id={tpl.id}",
            ),
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total = len(table_rows)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    visible = table_rows[start : start + page_size]
    showing_end = min(total, start + len(visible)) if total else 0

    return HrSalaryStructureManagementPageRead(
        page_title="Salary Structure Management",
        page_subtitle="Pay scales and components",
        new_structure_label="New structure",
        new_structure_href="/college-admin/hr/salary-structure-management?create=1",
        sub_nav=HR_PAYROLL_SUB_NAV,
        structures_section_title="Structures",
        table_headers=["Structure", "Applies to", "Components", "Employees", "Effective", "Status"],
        structure_rows=visible,
        showing_label=f"{showing_end} of {total}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages) if total_pages else [],
            has_previous=page > 1,
            has_next=page < total_pages if total_pages else False,
        ),
        footer_disclaimer="Live institutional data · Salary structures · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )