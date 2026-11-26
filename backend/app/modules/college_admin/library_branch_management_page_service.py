"""Library branch management (CA 12.02)."""

from __future__ import annotations

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.library_admin_models import LibraryBookCopyRecord, LibraryBranch
from app.modules.college_admin.models import InstitutionCampus
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryBranchManagementPageRead,
    LibraryBranchManagementTableRow,
)
from app.modules.library.facility_enums import LibraryOperatingStatus
from app.modules.library.facility_models import LibraryOperatingHours, LibrarySection
from app.modules.library.library_enums import LibraryCopyStatus
from app.modules.library.library_models import LibraryCatalogItem, LibraryCopy

_TABLE_HEADERS = ["Branch", "Location", "Titles", "Seats", "Hours", "Status"]


def _hours_label(doc: LibraryOperatingHours | None) -> str:
    if doc is None or not doc.days:
        return "—"
    opens: list[str] = []
    closes: list[str] = []
    for day in doc.days:
        if day.is_closed:
            continue
        for session in day.sessions:
            opens.append(session.opens_at)
            closes.append(session.closes_at)
    if not opens:
        return "Closed"
    return f"{min(opens)}–{max(closes)}"


def _status(operating_status: str, *, is_active: bool) -> tuple[str, str]:
    if not is_active:
        return "Inactive", "muted"
    key = (operating_status or "active").lower()
    if key in {LibraryOperatingStatus.ACTIVE.value, "open", "active"}:
        return "Open", "success"
    if key in {LibraryOperatingStatus.MAINTENANCE.value, LibraryOperatingStatus.TEMPORARILY_CLOSED.value}:
        return "Closed", "warning"
    if key == LibraryOperatingStatus.INACTIVE.value:
        return "Inactive", "muted"
    return key.replace("_", " ").title(), "muted"


async def _titles_at_branch(tenant_id: PydanticObjectId, branch_code: str) -> int:
    rows = await LibraryBookCopyRecord.find(
        Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
        Eq(LibraryBookCopyRecord.branch_code, branch_code),
    ).to_list()
    return len({r.book_id for r in rows})


async def _seats_at_branch(tenant_id: PydanticObjectId, branch_code: str) -> int:
    sections = await LibrarySection.find(
        Eq(LibrarySection.tenant_id, tenant_id),
        Eq(LibrarySection.branch_code, branch_code),
        Eq(LibrarySection.is_active, True),
    ).count()
    if sections:
        return sections
    copies = await LibraryCopy.find(
        Eq(LibraryCopy.tenant_id, tenant_id),
        Eq(LibraryCopy.status, LibraryCopyStatus.AVAILABLE),
    ).count()
    copy_rows = await LibraryBookCopyRecord.find(
        Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
        Eq(LibraryBookCopyRecord.branch_code, branch_code),
    ).to_list()
    if not copy_rows:
        return 0
    copy_ids = {c.copy_id for c in copy_rows}
    available = await LibraryCopy.find(
        {"tenant_id": tenant_id, "copy_id": {"$in": list(copy_ids)}, "status": LibraryCopyStatus.AVAILABLE.value},
    ).count()
    return available


async def get_library_branch_management_page(scope: AccessScope) -> LibraryBranchManagementPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    branches = await LibraryBranch.find(Eq(LibraryBranch.tenant_id, tenant_id)).sort("name").to_list()
    campuses = await InstitutionCampus.find(Eq(InstitutionCampus.tenant_id, tenant_id)).to_list()
    campus_by_id = {c.id: c for c in campuses}

    hours_docs = await LibraryOperatingHours.find(Eq(LibraryOperatingHours.tenant_id, tenant_id)).to_list()
    hours_by_branch: dict[str | None, LibraryOperatingHours] = {}
    for doc in hours_docs:
        hours_by_branch[doc.branch_code] = doc

    table_rows: list[LibraryBranchManagementTableRow] = []
    for branch in branches:
        campus = campus_by_id.get(branch.campus_id) if branch.campus_id else None
        location = (branch.address or (campus.name if campus else None) or branch.description or "—").strip()
        if len(location) > 120:
            location = f"{location[:118]}…"
        titles = await _titles_at_branch(tenant_id, branch.branch_code)
        seats = await _seats_at_branch(tenant_id, branch.branch_code)
        hours = _hours_label(hours_by_branch.get(branch.branch_code))
        status_label, status_tone = _status(branch.operating_status, is_active=branch.is_active)
        table_rows.append(
            LibraryBranchManagementTableRow(
                branch_code=branch.branch_code,
                branch_name=branch.name,
                location_label=location,
                titles_label=f"{titles:,}",
                seats_label=f"{seats:,}",
                hours_label=hours,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/library/library-branch-management?branch={branch.branch_code}",
            )
        )

    count = len(table_rows)
    branches_count_label = f"{count:,} branch" if count == 1 else f"{count:,} branches"

    return LibraryBranchManagementPageRead(
        page_title="Library Branch Management",
        page_subtitle="Branches, sections and working hours",
        add_branch_label="Add branch",
        add_branch_href="/college-admin/library/library-branch-management?action=create",
        branches_section_title="Branches",
        branches_count_label=branches_count_label,
        table_headers=_TABLE_HEADERS,
        branch_rows=table_rows,
        empty_table_message="No library branches yet. Add a branch to get started.",
        generated_at=now,
    )