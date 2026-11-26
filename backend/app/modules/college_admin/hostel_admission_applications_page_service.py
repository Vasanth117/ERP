"""Hostel admission applications (CA 13.05)."""

from __future__ import annotations

import math

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admissions_page_shared import (
    application_bucket,
    application_display_status,
    distance_label,
    pick_academic_year_label,
    study_year_ordinal,
    submitted_short,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelAdmissionApplicationsPageRead,
    HostelAdmissionApplicationsTableRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.hostel.hostel_models import HostelApplication

_PAGE_SIZE = 3
_TABLE_HEADERS = ["Application", "Student", "Year", "Distance", "Submitted", "Status"]


async def _load_students(
    tenant_id: PydanticObjectId, user_ids: set[PydanticObjectId]
) -> tuple[dict[PydanticObjectId, User], dict[PydanticObjectId, StudentRecord]]:
    if not user_ids:
        return {}, {}
    users = await User.find(In(User.id, list(user_ids))).to_list()
    records = await StudentRecord.find(
        Eq(StudentRecord.tenant_id, tenant_id),
        In(StudentRecord.user_id, list(user_ids)),
    ).to_list()
    return {u.id: u for u in users}, {r.user_id: r for r in records}


async def get_hostel_admission_applications_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    academic_year_label: str | None = None,
) -> HostelAdmissionApplicationsPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    all_apps = await HostelApplication.find(Eq(HostelApplication.tenant_id, tenant_id)).sort("-submitted_at").to_list()
    year_label = academic_year_label or pick_academic_year_label(all_apps)
    apps = [a for a in all_apps if not year_label or a.academic_year_label == year_label]

    total = len(apps)
    pending = sum(1 for a in apps if application_bucket(a.status) == "pending")
    approved = sum(1 for a in apps if application_bucket(a.status) == "approved")
    waitlisted = sum(1 for a in apps if application_bucket(a.status) == "waitlisted")

    user_ids = {a.student_user_id for a in apps if a.student_user_id}
    users_by_id, records_by_user = await _load_students(tenant_id, user_ids)

    table_rows: list[HostelAdmissionApplicationsTableRow] = []
    for app in apps:
        student = users_by_id.get(app.student_user_id)
        record = records_by_user.get(app.student_user_id)
        status_label, status_tone = application_display_status(app.status)
        table_rows.append(
            HostelAdmissionApplicationsTableRow(
                application_id=app.application_id,
                application_label=app.application_id,
                student_label=student.full_name if student else "—",
                year_label=study_year_ordinal(
                    record.batch_label if record else None,
                    app.academic_year_label,
                ),
                distance_label=distance_label(app.eligibility_payload),
                submitted_label=submitted_short(app.submitted_at),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hostel/hostel-admission-applications?id={app.application_id}",
            )
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total, start + len(paged_rows))
    count_label = f"{showing_end} of {total}"
    subtitle = f"Applications for {year_label}" if year_label else "Hostel admission applications"

    kpis = [
        UserDashboardKpi(
            key="applications",
            label="Applications",
            value=f"{total:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="pending_review",
            label="Pending review",
            value=f"{pending:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="approved",
            label="Approved",
            value=f"{approved:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="waitlisted",
            label="Waitlisted",
            value=f"{waitlisted:,}",
            hint_line="",
            hint_tone="muted",
        ),
    ]

    return HostelAdmissionApplicationsPageRead(
        page_title="Hostel Admission Applications",
        page_subtitle=subtitle,
        export_label="Export",
        export_href="/college-admin/hostel/hostel-admission-applications?export=1",
        kpis=kpis,
        applications_section_title="Applications",
        table_headers=_TABLE_HEADERS,
        application_rows=paged_rows,
        empty_table_message="No hostel admission applications yet.",
        count_label=count_label,
        showing_label=f"Showing {showing_end if total else 0} of {total:,}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        academic_year_label=year_label,
        generated_at=now,
    )