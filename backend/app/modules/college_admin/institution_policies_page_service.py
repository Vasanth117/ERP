"""Institutional policies dashboard (CA policies screen)."""

from __future__ import annotations

import math
import re
from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.core.form_values import blank_to_none
from app.modules.college_admin.institution_policy_models import (
    InstitutionPolicy,
    InstitutionPolicyAcknowledgement,
    InstitutionPolicyReview,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionPoliciesPageRead,
    InstitutionPolicyCreate,
    InstitutionPolicyCreateResult,
    InstitutionPolicyFilterOption,
    InstitutionPolicyReviewItem,
    InstitutionPolicyRow,
    InstitutionPolicySelectedDetail,
    PoliciesPagination,
)
from app.modules.students.models import StudentProfile

_CREATE_CATEGORIES = [
    InstitutionPolicyFilterOption(value="Academic", label="Academic"),
    InstitutionPolicyFilterOption(value="Conduct", label="Conduct"),
    InstitutionPolicyFilterOption(value="HR", label="HR"),
    InstitutionPolicyFilterOption(value="IT", label="IT"),
    InstitutionPolicyFilterOption(value="Safety", label="Safety"),
    InstitutionPolicyFilterOption(value="Governance", label="Governance"),
]

_CREATE_AUDIENCES = [
    InstitutionPolicyFilterOption(value="all", label="All"),
    InstitutionPolicyFilterOption(value="students", label="Students"),
    InstitutionPolicyFilterOption(value="faculty", label="Faculty"),
    InstitutionPolicyFilterOption(value="staff", label="Staff"),
]

_CREATE_STATUSES = [
    InstitutionPolicyFilterOption(value="draft", label="Draft"),
    InstitutionPolicyFilterOption(value="in_review", label="In review"),
    InstitutionPolicyFilterOption(value="published", label="Published"),
]


def _status_tone(status: str) -> str:
    if status == "published":
        return "success"
    if status == "draft":
        return "warning"
    if status == "in_review":
        return "info"
    return "muted"


def _review_tone(code: str) -> str:
    if code == "in_review":
        return "info"
    if code == "upcoming":
        return "muted"
    return "muted"


def _format_effective(value: date | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y")


async def _distinct_filter_options(
    tenant_id: PydanticObjectId,
    field: str,
) -> list[InstitutionPolicyFilterOption]:
    rows = await InstitutionPolicy.find(Eq(InstitutionPolicy.tenant_id, tenant_id)).to_list()
    seen: set[str] = set()
    options: list[InstitutionPolicyFilterOption] = []
    for row in rows:
        raw = getattr(row, field, "") or ""
        key = str(raw).strip()
        if not key or key.lower() in seen:
            continue
        seen.add(key.lower())
        label = key.replace("_", " ").title() if field == "status" else key
        if field == "audience":
            label = key.title() if key != "all" else "All"
        options.append(InstitutionPolicyFilterOption(value=key, label=label))
    options.sort(key=lambda item: item.label)
    return options


def _slug_policy_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return (slug[:48] or "policy").strip("-")


async def _unique_policy_id(tenant_id: PydanticObjectId, title: str) -> str:
    base = _slug_policy_id(title)
    candidate = base
    suffix = 0
    while await InstitutionPolicy.find_one(
        Eq(InstitutionPolicy.tenant_id, tenant_id),
        Eq(InstitutionPolicy.policy_id, candidate),
    ):
        suffix += 1
        candidate = f"{base}-{suffix}"
    return candidate


async def create_institution_policy(
    scope: AccessScope,
    payload: InstitutionPolicyCreate,
) -> InstitutionPolicyCreateResult:
    authorize(scope, Permission.INSTITUTION_PROFILE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    from app.modules.college_admin.form_validation_details import raise_validation_error, scroll_field

    title = payload.title.strip()
    if len(title) < 2:
        raise_validation_error(
            "Complete the required policy fields before saving.",
            [
                scroll_field(
                    "title",
                    label="Policy title",
                    message="Enter a title for this policy (at least 2 characters).",
                )
            ],
        )

    policy_id = await _unique_policy_id(tenant_id, title)
    search_bits = [title, payload.category, payload.audience, policy_id]
    search_text = " ".join(str(part) for part in search_bits if part).lower()

    doc = InstitutionPolicy(
        tenant_id=tenant_id,
        policy_id=policy_id,
        title=title,
        category=payload.category.strip(),
        audience=payload.audience.strip().lower(),
        version_label=payload.version_label.strip() or "1.0",
        effective_from=payload.effective_from,
        status=payload.status.strip().lower() or "draft",
        owner_label=blank_to_none(payload.owner_label),
        approved_by_label=blank_to_none(payload.approved_by_label),
        acknowledgement_requirement=blank_to_none(payload.acknowledgement_requirement),
        detail_href=f"/college-admin/institution/policies/{policy_id}",
        search_text=search_text,
        sort_order=await InstitutionPolicy.find(Eq(InstitutionPolicy.tenant_id, tenant_id)).count(),
    )
    await doc.insert()
    return InstitutionPolicyCreateResult(policy_id=policy_id, title=title)


async def _acknowledgement_line(policy: InstitutionPolicy, tenant_id: PydanticObjectId) -> str | None:
    if not policy.acknowledgement_requirement:
        return None
    completed = policy.acknowledgement_completed
    required = policy.acknowledgement_required
    if required is None and policy.audience in {"all", "students"}:
        required = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).count()
    if completed is None:
        completed = await InstitutionPolicyAcknowledgement.find(
            Eq(InstitutionPolicyAcknowledgement.tenant_id, tenant_id),
            Eq(InstitutionPolicyAcknowledgement.policy_id, policy.policy_id),
        ).count()
    if required is None:
        return policy.acknowledgement_requirement
    if required == 0:
        return policy.acknowledgement_requirement
    percent = int(round((completed or 0) / required * 100))
    return f"{completed or 0:,} of {required:,} ({percent}%)"


async def get_institution_policies_page(
    scope: AccessScope,
    *,
    search: str | None = None,
    category: str | None = None,
    audience: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 6,
    selected_policy_id: str | None = None,
) -> InstitutionPoliciesPageRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)
    page = max(1, page)
    page_size = min(max(1, page_size), 50)

    all_rows = await InstitutionPolicy.find(Eq(InstitutionPolicy.tenant_id, tenant_id)).sort("+sort_order").to_list()
    all_rows.sort(key=lambda row: (row.sort_order, row.title.lower()))

    filtered: list[InstitutionPolicy] = []
    needle = (search or "").strip().lower()
    for row in all_rows:
        if category and row.category != category:
            continue
        if audience and row.audience != audience:
            continue
        if status and row.status != status:
            continue
        if needle:
            blob = (row.search_text or row.title).lower()
            if needle not in blob and needle not in row.title.lower():
                continue
        filtered.append(row)

    total = len(filtered)
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    if page > total_pages:
        page = total_pages
    start = (page - 1) * page_size
    page_rows = filtered[start : start + page_size]

    table_rows = [
        InstitutionPolicyRow(
            policy_id=row.policy_id,
            title=row.title,
            audience_label=row.audience.replace("_", " ").title() if row.audience != "all" else "All",
            version_label=row.version_label,
            effective_label=_format_effective(row.effective_from),
            status_code=row.status,
            status_label=row.status.replace("_", " ").title(),
            status_tone=_status_tone(row.status),
        )
        for row in page_rows
    ]

    selected_doc: InstitutionPolicy | None = None
    if selected_policy_id:
        selected_doc = next((row for row in filtered if row.policy_id == selected_policy_id), None)
        if selected_doc is None:
            selected_doc = await InstitutionPolicy.find_one(
                Eq(InstitutionPolicy.tenant_id, tenant_id),
                Eq(InstitutionPolicy.policy_id, selected_policy_id),
            )
    if selected_doc is None and filtered:
        selected_doc = filtered[0]

    selected: InstitutionPolicySelectedDetail | None = None
    if selected_doc:
        ack_line = await _acknowledgement_line(selected_doc, tenant_id)
        selected = InstitutionPolicySelectedDetail(
            policy_id=selected_doc.policy_id,
            title=selected_doc.title,
            open_href=selected_doc.detail_href
            or f"/college-admin/institution/policies/{selected_doc.policy_id}",
            open_label="Open",
            owner_label=selected_doc.owner_label,
            approved_by_label=selected_doc.approved_by_label,
            acknowledgement_requirement=selected_doc.acknowledgement_requirement,
            acknowledgement_progress_label=ack_line,
        )

    reviews = await InstitutionPolicyReview.find(Eq(InstitutionPolicyReview.tenant_id, tenant_id)).sort(
        "+sort_order",
    ).to_list()
    review_items = [
        InstitutionPolicyReviewItem(
            review_id=row.review_id,
            title=row.title,
            subtitle=row.subtitle,
            status_code=row.status_code,
            status_label=row.status_label,
            status_tone=_review_tone(row.status_code),
        )
        for row in reviews
    ]

    categories = await _distinct_filter_options(tenant_id, "category")
    audiences = await _distinct_filter_options(tenant_id, "audience")
    statuses = await _distinct_filter_options(tenant_id, "status")

    page_numbers = list(range(1, min(total_pages, 12) + 1))
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    return InstitutionPoliciesPageRead(
        page_title="Institutional Policies",
        page_subtitle="Policies published to students, faculty and staff",
        export_label="Export list",
        add_policy_label="Add policy",
        add_policy_href="/college-admin/institution/policies#add-policy",
        create_dialog_title="Add policy",
        create_dialog_subtitle="Define title, audience, version and publish status",
        create_save_label="Create policy",
        create_cancel_label="Cancel",
        create_category_options=_CREATE_CATEGORIES,
        create_audience_options=_CREATE_AUDIENCES,
        create_status_options=_CREATE_STATUSES,
        search_placeholder="Search policies...",
        category_filter_label="Category",
        audience_filter_label="Audience",
        status_filter_label="Status",
        category_options=[InstitutionPolicyFilterOption(value="", label="Category")] + categories,
        audience_options=[InstitutionPolicyFilterOption(value="", label="Audience")] + audiences,
        status_options=[InstitutionPolicyFilterOption(value="", label="Status")] + statuses,
        policies=table_rows,
        policy_count_label=f"{total} polic{'ies' if total != 1 else 'y'}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        selected_policy=selected,
        review_schedule=review_items,
        review_schedule_title="Review schedule",
        selected_panel_prefix="Selected:",
        footer_disclaimer=(
            "Live institutional policy records · Acknowledgement counts from stored data · All times IST"
        ),
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )