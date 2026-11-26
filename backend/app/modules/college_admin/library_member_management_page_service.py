"""Library member management (CA 12.08)."""

from __future__ import annotations

import math

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.library_admin_models import LibraryMembershipReference
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryMemberManagementPageRead,
    LibraryMemberManagementTableRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.library.library_enums import LibraryCirculationStatus
from app.modules.library.library_models import LibraryCirculation
from app.modules.library.member_enums import LibraryMemberCategory, LibraryMemberStatus

_PAGE_SIZE = 3
_TABLE_HEADERS = ["Member", "ID", "Type", "Borrowing limit", "On loan", "Status"]
_ACTIVE_LOAN = frozenset({LibraryCirculationStatus.ACTIVE, LibraryCirculationStatus.OVERDUE})
_STUDENT_CATS = frozenset({LibraryMemberCategory.STUDENT.value, "student"})
_FACULTY_STAFF_CATS = frozenset(
    {LibraryMemberCategory.FACULTY.value, LibraryMemberCategory.EMPLOYEE.value, "faculty", "employee", "staff"},
)


def _type_label(member: LibraryMembershipReference) -> str:
    cat = (member.member_category or member.member_type or "member").lower()
    mapping = {
        "student": "Student",
        "faculty": "Faculty",
        "employee": "Faculty",
        "staff": "Faculty",
        "external": "External",
    }
    return mapping.get(cat, cat.replace("_", " ").title())


def _is_blocked(member: LibraryMembershipReference) -> bool:
    status = (member.status or "").lower()
    return status in {LibraryMemberStatus.SUSPENDED.value, LibraryMemberStatus.INACTIVE.value, "blocked"} or not member.eligible


def _status(member: LibraryMembershipReference) -> tuple[str, str]:
    if _is_blocked(member):
        return "Blocked", "error"
    return "Active", "success"


async def get_library_member_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryMemberManagementPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    members = await LibraryMembershipReference.find(Eq(LibraryMembershipReference.tenant_id, tenant_id)).sort("-updated_at").to_list()
    total = len(members)
    students = sum(1 for m in members if (m.member_category or m.member_type or "").lower() in _STUDENT_CATS)
    faculty_staff = sum(
        1 for m in members if (m.member_category or m.member_type or "").lower() in _FACULTY_STAFF_CATS
    )
    blocked = sum(1 for m in members if _is_blocked(m))

    kpis = [
        UserDashboardKpi(
            key="members",
            label="Members",
            value=f"{total:,}",
            hint_line="All library members",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="students",
            label="Students",
            value=f"{students:,}",
            hint_line="Student members",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="faculty_staff",
            label="Faculty and staff",
            value=f"{faculty_staff:,}",
            hint_line="Employees and faculty",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="blocked",
            label="Blocked",
            value=f"{blocked:,}",
            hint_line="Fines or lost books",
            hint_tone="error" if blocked else "success",
        ),
    ]

    loans = await LibraryCirculation.find(
        Eq(LibraryCirculation.tenant_id, tenant_id),
        In(LibraryCirculation.status, list(_ACTIVE_LOAN)),
    ).to_list()
    on_loan_by_user: dict = {}
    for loan in loans:
        on_loan_by_user[loan.student_user_id] = on_loan_by_user.get(loan.student_user_id, 0) + 1

    user_ids = {m.member_user_id for m in members}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[LibraryMemberManagementTableRow] = []
    for member in members:
        user = user_by_id.get(member.member_user_id)
        member_name = user.full_name if user else "—"
        status_label, status_tone = _status(member)
        on_loan = on_loan_by_user.get(member.member_user_id, 0)
        table_rows.append(
            LibraryMemberManagementTableRow(
                member_user_id=str(member.member_user_id),
                member_name=member_name,
                member_id_label=member.membership_number,
                type_label=_type_label(member),
                borrowing_limit_label=str(member.borrowing_limit),
                on_loan_label=str(on_loan),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/library/library-member-management?id={member.membership_number}",
            )
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total, start + len(paged_rows))
    showing_label = f"{showing_end:,} of {total:,}"

    return LibraryMemberManagementPageRead(
        page_title="Library Member Management",
        page_subtitle="Students, faculty and external members",
        add_member_label="Add member",
        add_member_href="/college-admin/library/library-member-management?action=add",
        kpis=kpis,
        members_section_title="Members",
        table_headers=_TABLE_HEADERS,
        member_rows=paged_rows,
        empty_table_message="No library members yet.",
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )