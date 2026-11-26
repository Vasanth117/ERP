"""HR employee onboarding list (CA 11.04)."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_admin_models import EmployeeOnboardingRecord
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.hr_recruitment_management_page_service import _SUB_NAV, _fmt_snapshot
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HrEmployeeOnboardingPageRead,
    HrOnboardingStatusCell,
    HrOnboardingTableRow,
    PoliciesPagination,
)
from app.modules.hr.enums import HrOnboardingProcessStatus, HrOnboardingTaskStatus
from app.modules.hr.onboarding_models import HrOnboardingProcess, HrOnboardingTask
from app.modules.hr.recruitment_models import HrCandidate

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Employee", "Joining", "Documents", "IT account", "ID card", "Progress"]

_DOC_KEYS = ("document", "documents", "verification", "paperwork")
_IT_KEYS = ("it_account", "it account", "ldap", "email", "system access", "login")
_ID_KEYS = ("id_card", "id card", "badge", "identity card")


def _matches_keys(text: str, keys: tuple[str, ...]) -> bool:
    blob = text.lower()
    return any(k in blob for k in keys)


def _cell_from_tasks(tasks: list[HrOnboardingTask], keys: tuple[str, ...]) -> HrOnboardingStatusCell:
    matching = [t for t in tasks if _matches_keys(f"{t.task_key} {t.title}", keys)]
    if not matching:
        return HrOnboardingStatusCell(label="Not started", tone="muted")
    if all(t.status == HrOnboardingTaskStatus.COMPLETED for t in matching):
        return HrOnboardingStatusCell(label="Done", tone="success")
    if all(t.status == HrOnboardingTaskStatus.NOT_STARTED for t in matching):
        return HrOnboardingStatusCell(label="Not started", tone="muted")
    return HrOnboardingStatusCell(label="Pending", tone="warning")


def _progress_cell(process: HrOnboardingProcess, tasks: list[HrOnboardingTask]) -> HrOnboardingStatusCell:
    if process.status == HrOnboardingProcessStatus.COMPLETED or process.completed_at:
        return HrOnboardingStatusCell(label="Complete", tone="success")
    mandatory = [t for t in tasks if t.mandatory]
    if not mandatory:
        done_optional = sum(1 for t in tasks if t.status == HrOnboardingTaskStatus.COMPLETED)
        total = len(tasks)
        if total == 0:
            return HrOnboardingStatusCell(label="—", tone="muted")
        pct = int(round(100 * done_optional / total))
        return HrOnboardingStatusCell(label=f"{pct}%", tone="info")
    done = sum(1 for t in mandatory if t.status == HrOnboardingTaskStatus.COMPLETED)
    pct = int(round(100 * done / len(mandatory)))
    return HrOnboardingStatusCell(label=f"{pct}%", tone="info")


def _legacy_cells(checklist: list[dict]) -> tuple[HrOnboardingStatusCell, HrOnboardingStatusCell, HrOnboardingStatusCell, HrOnboardingStatusCell]:
    def pick(keys: tuple[str, ...]) -> HrOnboardingStatusCell:
        for item in checklist:
            title = str(item.get("title") or item.get("task_key") or "")
            if not _matches_keys(title, keys):
                continue
            if item.get("completed"):
                return HrOnboardingStatusCell(label="Done", tone="success")
            return HrOnboardingStatusCell(label="Pending", tone="warning")
        return HrOnboardingStatusCell(label="Not started", tone="muted")

    docs = pick(_DOC_KEYS)
    it_acc = pick(_IT_KEYS)
    id_card = pick(_ID_KEYS)
    total = len(checklist) or 1
    done = sum(1 for item in checklist if item.get("completed"))
    progress = (
        HrOnboardingStatusCell(label="Complete", tone="success")
        if done == total and checklist
        else HrOnboardingStatusCell(label=f"{int(round(100 * done / total))}%", tone="info")
    )
    return docs, it_acc, id_card, progress


async def get_hr_employee_onboarding_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HrEmployeeOnboardingPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    processes = await HrOnboardingProcess.find(
        Eq(HrOnboardingProcess.tenant_id, tenant_id),
        In(
            HrOnboardingProcess.status,
            [
                HrOnboardingProcessStatus.IN_PROGRESS,
                HrOnboardingProcessStatus.PENDING_COMPLETION,
                HrOnboardingProcessStatus.NOT_STARTED,
                HrOnboardingProcessStatus.COMPLETED,
            ],
        ),
    ).sort("-updated_at").to_list()

    legacy_rows = await EmployeeOnboardingRecord.find(
        Eq(EmployeeOnboardingRecord.tenant_id, tenant_id),
        Eq(EmployeeOnboardingRecord.completed, False),
    ).to_list()

    user_ids: set[PydanticObjectId] = {p.employee_user_id for p in processes if p.employee_user_id}
    user_ids.update(r.user_id for r in legacy_rows)
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    candidate_ids = {p.candidate_id for p in processes}
    candidates = await HrCandidate.find(In(HrCandidate.id, list(candidate_ids))).to_list() if candidate_ids else []
    candidate_by_id = {c.id: c for c in candidates}

    process_ids = [p.id for p in processes]
    all_tasks: list[HrOnboardingTask] = []
    if process_ids:
        all_tasks = await HrOnboardingTask.find(
            Eq(HrOnboardingTask.tenant_id, tenant_id),
            In(HrOnboardingTask.process_id, process_ids),
        ).to_list()
    tasks_by_process: dict[PydanticObjectId, list[HrOnboardingTask]] = {}
    for task in all_tasks:
        tasks_by_process.setdefault(task.process_id, []).append(task)

    built: list[HrOnboardingTableRow] = []
    seen_users: set[PydanticObjectId] = set()

    for process in processes:
        if process.employee_user_id:
            seen_users.add(process.employee_user_id)
        user = user_by_id.get(process.employee_user_id) if process.employee_user_id else None
        candidate = candidate_by_id.get(process.candidate_id)
        name = user.full_name if user else (candidate.full_name if candidate else "—")
        joining = process.joining_date.strftime("%d %b %Y") if process.joining_date else "—"
        tasks = tasks_by_process.get(process.id, [])
        built.append(
            HrOnboardingTableRow(
                process_id=str(process.id),
                employee_name=name,
                joining_label=joining,
                documents=_cell_from_tasks(tasks, _DOC_KEYS),
                it_account=_cell_from_tasks(tasks, _IT_KEYS),
                id_card=_cell_from_tasks(tasks, _ID_KEYS),
                progress=_progress_cell(process, tasks),
                detail_href=f"/college-admin/hr/employee-onboarding?process_id={process.id}",
            )
        )

    for legacy in legacy_rows:
        if legacy.user_id in seen_users:
            continue
        user = user_by_id.get(legacy.user_id)
        docs, it_acc, id_card, progress = _legacy_cells(legacy.checklist or [])
        built.append(
            HrOnboardingTableRow(
                process_id=str(legacy.id),
                employee_name=user.full_name if user else "—",
                joining_label="—",
                documents=docs,
                it_account=it_acc,
                id_card=id_card,
                progress=progress,
                detail_href=f"/college-admin/hr/employee-onboarding?user_id={legacy.user_id}",
            )
        )

    built.sort(key=lambda r: (r.joining_label == "—", r.employee_name.lower()))
    total = len(built)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged = built[start : start + page_size]
    showing_end = min(total, start + len(paged)) if total else 0

    return HrEmployeeOnboardingPageRead(
        page_title="Employee Onboarding",
        page_subtitle="Joining checklists for new employees",
        new_onboarding_label="New onboarding",
        new_onboarding_href="/college-admin/hr/employee-onboarding?create=1",
        sub_nav=_SUB_NAV,
        onboarding_section_title="Onboarding",
        table_headers=_TABLE_HEADERS,
        onboarding_rows=paged,
        showing_label=f"{showing_end} of {total:,}" if total else "0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · HR onboarding records · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )