"""College admin dashboard — recent institutional activities overview."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.college_admin.enums import DashboardDateRange, InstitutionActivityKind
from app.modules.college_admin.import_admin_models import InstitutionImportJob
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader, _date_window
from app.modules.college_admin.models import InstitutionActivityLog
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    RecentActivitiesOverviewFilters,
    RecentActivitiesOverviewKpiRead,
    RecentActivitiesOverviewRead,
    RecentActivityByModuleItem,
    RecentActivityFeedRow,
    RecentActivityFollowUpItem,
    RecentActivityModuleFilterOption,
    RecentActivityTopPerformerItem,
    RecentActivityUserFilterOption,
)

_reader = OperationalDataReader()

_FEED_LIMIT_DEFAULT = 9

_RESOURCE_MODULE: dict[str, str] = {
    "fee": "Finance",
    "finance": "Finance",
    "payment": "Finance",
    "refund": "Finance",
    "scholarship": "Finance",
    "exam": "Examinations",
    "examination": "Examinations",
    "timetable": "Examinations",
    "assessment": "Examinations",
    "student": "Students",
    "enrollment": "Students",
    "admission": "Students",
    "attendance": "Attendance",
    "faculty": "Data management",
    "employee": "Data management",
    "import": "Data management",
    "library": "Library",
    "hostel": "Hostel",
    "leave": "HR & leave",
    "workflow": "Approvals",
    "approval": "Approvals",
    "institution": "Institution",
    "campus": "Institution",
    "settings": "Institution",
}

_CATEGORY_MODULE: dict[str, str] = {
    "student": "Students",
    "faculty": "Data management",
    "admission": "Students",
    "institution": "Institution",
    "audit": "Institution",
}

_PERIOD_LABELS: dict[DashboardDateRange | None, str] = {
    DashboardDateRange.TODAY: "today",
    DashboardDateRange.WEEK: "this week",
    DashboardDateRange.MONTH: "this month",
    DashboardDateRange.SEMESTER: "this period",
    None: "this period",
}

_KPI_TITLES: dict[DashboardDateRange | None, str] = {
    DashboardDateRange.TODAY: "Actions today",
    DashboardDateRange.WEEK: "Actions this week",
    DashboardDateRange.MONTH: "Actions this month",
    DashboardDateRange.SEMESTER: "Actions",
    None: "Actions",
}


def _module_for(resource_type: str, category: str) -> tuple[str, str]:
    rt = (resource_type or "").lower()
    for key, label in _RESOURCE_MODULE.items():
        if key in rt:
            return key, label
    cat_label = _CATEGORY_MODULE.get(category, "Operations")
    return category or "other", cat_label


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fmt_time(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%H:%M")


def _result_from_audit(outcome: str, metadata: dict) -> tuple[str, str]:
    normalized = (outcome or "success").lower()
    if normalized in ("failure", "failed", "error"):
        err = metadata.get("error_count") or metadata.get("failed_rows") or metadata.get("invalid_rows") or 1
        try:
            n = int(err)
        except (TypeError, ValueError):
            n = 1
        suffix = "s" if n != 1 else ""
        return "errors", f"{n} error{suffix}"
    if normalized in ("pending", "pending_approval", "awaiting"):
        return "pending", "Pending"
    if normalized in ("in_review", "review"):
        return "in_review", "In review"
    return "completed", "Completed"


def _result_from_import_status(status: str, failed_rows: int) -> tuple[str, str]:
    st = (status or "").lower()
    if failed_rows > 0:
        return "errors", f"{failed_rows} error{'s' if failed_rows != 1 else ''}"
    if st in ("pending_approval", "validated", "preview_ready"):
        return "pending", "Pending"
    if st in ("running",):
        return "in_review", "In review"
    return "completed", "Completed"


class _FeedEvent:
    __slots__ = (
        "activity_id",
        "title",
        "module_key",
        "module_label",
        "performed_by_label",
        "actor_user_id",
        "occurred_at",
        "result_key",
        "result_label",
    )

    def __init__(
        self,
        *,
        activity_id: str,
        title: str,
        module_key: str,
        module_label: str,
        performed_by_label: str,
        actor_user_id: str | None,
        occurred_at: datetime,
        result_key: str,
        result_label: str,
    ) -> None:
        self.activity_id = activity_id
        self.title = title
        self.module_key = module_key
        self.module_label = module_label
        self.performed_by_label = performed_by_label
        self.actor_user_id = actor_user_id
        self.occurred_at = occurred_at
        self.result_key = result_key
        self.result_label = result_label


async def _load_user_names(tenant_id: PydanticObjectId, user_ids: set[PydanticObjectId]) -> dict[PydanticObjectId, str]:
    names: dict[PydanticObjectId, str] = {}
    for uid in user_ids:
        user = await User.get(uid)
        if user and user.tenant_id == tenant_id:
            names[uid] = user.full_name or user.email or str(uid)
    return names


async def _collect_feed_events(
    tenant_id: PydanticObjectId,
    window_start: datetime,
    window_end: datetime,
    user_names: dict[PydanticObjectId, str],
) -> list[_FeedEvent]:
    events: list[_FeedEvent] = []

    admin_rows = await (
        InstitutionActivityLog.find(
            Eq(InstitutionActivityLog.tenant_id, tenant_id),
            {"created_at": {"$gte": window_start, "$lt": window_end}},
        )
        .sort("-created_at")
        .limit(200)
        .to_list()
    )
    for row in admin_rows:
        if row.activity_kind == InstitutionActivityKind.DASHBOARD_VIEW:
            continue
        mod_key, mod_label = _module_for(row.resource_type, "institution")
        actor_label = user_names.get(row.actor_id, "Institution") if row.actor_id else "System"
        events.append(
            _FeedEvent(
                activity_id=str(row.id),
                title=row.summary,
                module_key=mod_key,
                module_label=mod_label,
                performed_by_label=row.metadata.get("actor_label") or actor_label,
                actor_user_id=str(row.actor_id) if row.actor_id else None,
                occurred_at=row.created_at,
                result_key="completed",
                result_label="Completed",
            )
        )

    audit_rows = await (
        AuditLog.find({"tenant_id": tenant_id, "created_at": {"$gte": window_start, "$lt": window_end}})
        .sort("-created_at")
        .limit(300)
        .to_list()
    )
    for row in audit_rows:
        mod_key, mod_label = _module_for(row.resource_type, "audit")
        actor_label = user_names.get(row.actor_id, "System") if row.actor_id else "System"
        if row.metadata.get("office_label"):
            actor_label = str(row.metadata["office_label"])
        result_key, result_label = _result_from_audit(row.outcome, row.metadata or {})
        events.append(
            _FeedEvent(
                activity_id=str(row.id),
                title=row.action,
                module_key=mod_key,
                module_label=mod_label,
                performed_by_label=actor_label,
                actor_user_id=str(row.actor_id) if row.actor_id else None,
                occurred_at=row.created_at,
                result_key=result_key,
                result_label=result_label,
            )
        )

    for item in await _reader.recent_student_activities(tenant_id, from_time=window_start, limit=80):
        if _ensure_aware(item.occurred_at) >= window_end:
            continue
        mod_key, mod_label = _module_for("student", item.category)
        events.append(
            _FeedEvent(
                activity_id=item.activity_id,
                title=item.title,
                module_key=mod_key,
                module_label=mod_label,
                performed_by_label=item.actor_label or "Student portal",
                actor_user_id=item.reference_id,
                occurred_at=item.occurred_at,
                result_key="completed",
                result_label="Completed",
            )
        )

    for item in await _reader.recent_faculty_activities(tenant_id, from_time=window_start, limit=80):
        if _ensure_aware(item.occurred_at) >= window_end:
            continue
        mod_key, mod_label = _module_for("faculty", item.category)
        events.append(
            _FeedEvent(
                activity_id=item.activity_id,
                title=item.title,
                module_key=mod_key,
                module_label=mod_label,
                performed_by_label=item.actor_label or "Faculty",
                actor_user_id=item.reference_id,
                occurred_at=item.occurred_at,
                result_key="completed",
                result_label="Completed",
            )
        )

    for item in await _reader.recent_admissions(tenant_id, from_time=window_start, limit=40):
        if _ensure_aware(item.occurred_at) >= window_end:
            continue
        events.append(
            _FeedEvent(
                activity_id=item.activity_id,
                title=item.title,
                module_key="admission",
                module_label="Students",
                performed_by_label=item.actor_label or "Admissions",
                actor_user_id=item.reference_id,
                occurred_at=item.occurred_at,
                result_key="completed",
                result_label="Completed",
            )
        )

    import_jobs = await (
        InstitutionImportJob.find(
            Eq(InstitutionImportJob.tenant_id, tenant_id),
            {
                "$or": [
                    {"created_at": {"$gte": window_start, "$lt": window_end}},
                    {"completed_at": {"$gte": window_start, "$lt": window_end}},
                ]
            },
        )
        .sort("-created_at")
        .limit(30)
        .to_list()
    )
    for job in import_jobs:
        status_val = job.status.value if hasattr(job.status, "value") else str(job.status)
        result_key, result_label = _result_from_import_status(status_val, job.failed_rows)
        title = f"Bulk import — {job.file_name}"
        if job.entity_type:
            et = job.entity_type.value if hasattr(job.entity_type, "value") else str(job.entity_type)
            title = f"Bulk import — {job.executed_rows or job.total_rows} {et} records"
        events.append(
            _FeedEvent(
                activity_id=job.job_id,
                title=title,
                module_key="import",
                module_label="Data management",
                performed_by_label=user_names.get(job.actor_id, "HR Office") if job.actor_id else "HR Office",
                actor_user_id=str(job.actor_id) if job.actor_id else None,
                occurred_at=job.completed_at or job.created_at,
                result_key=result_key,
                result_label=result_label,
            )
        )

    events.sort(key=lambda e: e.occurred_at, reverse=True)
    return events


async def get_recent_activities_overview(
    scope: AccessScope,
    *,
    anchor_date: date | None = None,
    date_range: DashboardDateRange | None = DashboardDateRange.TODAY,
    module_key: str | None = None,
    user_id: str | None = None,
    feed_offset: int = 0,
    feed_limit: int = _FEED_LIMIT_DEFAULT,
) -> RecentActivitiesOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    anchor = anchor_date or date.today()
    range_key = date_range or DashboardDateRange.TODAY
    window_start, window_end = _date_window(anchor, range_key)

    actor_ids: set[PydanticObjectId] = set()
    audit_for_ids = await (
        AuditLog.find({"tenant_id": tenant_id, "created_at": {"$gte": window_start, "$lt": window_end}})
        .limit(400)
        .to_list()
    )
    for row in audit_for_ids:
        if row.actor_id:
            actor_ids.add(row.actor_id)
    inst_for_ids = await (
        InstitutionActivityLog.find(
            Eq(InstitutionActivityLog.tenant_id, tenant_id),
            {"created_at": {"$gte": window_start, "$lt": window_end}},
        )
        .limit(200)
        .to_list()
    )
    for row in inst_for_ids:
        if row.actor_id:
            actor_ids.add(row.actor_id)
    user_names = await _load_user_names(tenant_id, actor_ids)

    all_events = await _collect_feed_events(tenant_id, window_start, window_end, user_names)

    if module_key:
        all_events = [e for e in all_events if e.module_key == module_key or e.module_label.lower().replace(" ", "_") == module_key]
    if user_id:
        all_events = [e for e in all_events if e.actor_user_id == user_id]

    feed_total = len(all_events)
    page_events = all_events[feed_offset : feed_offset + feed_limit]
    feed_rows = [
        RecentActivityFeedRow(
            activity_id=e.activity_id,
            title=e.title,
            module_key=e.module_key,
            module_label=e.module_label,
            performed_by_label=e.performed_by_label,
            actor_user_id=e.actor_user_id,
            occurred_at=e.occurred_at,
            time_label=_fmt_time(e.occurred_at),
            result_key=e.result_key,
            result_label=e.result_label,
        )
        for e in page_events
    ]

    module_counts: dict[str, tuple[str, int]] = {}
    for e in all_events:
        prev = module_counts.get(e.module_key)
        module_counts[e.module_key] = (e.module_label, (prev[1] if prev else 0) + 1)
    by_module = [
        RecentActivityByModuleItem(module_key=key, module_label=label, count=count)
        for key, (label, count) in sorted(module_counts.items(), key=lambda x: -x[1][1])
    ]
    module_max = max((m.count for m in by_module), default=1)

    performer_stats: dict[str, dict] = defaultdict(lambda: {"label": "", "module": "", "count": 0})
    role_keys: set[str] = set()
    records_changed = 0
    failed_actions = 0
    distinct_actors: set[str] = set()
    resource_tags: set[str] = set()

    for e in all_events:
        if e.actor_user_id:
            distinct_actors.add(e.actor_user_id)
        role_keys.add(e.module_label)
        if e.result_key == "completed":
            records_changed += 1
        if e.result_key == "errors":
            failed_actions += 1
        key = e.performed_by_label
        stats = performer_stats[key]
        stats["label"] = key
        stats["module"] = e.module_label
        stats["count"] += 1

        rt = e.module_key
        if rt in ("student", "admission", "finance", "fee"):
            resource_tags.add("students")
        elif rt in ("faculty", "import", "employee"):
            resource_tags.add("faculty")
        elif rt in ("finance", "payment", "refund"):
            resource_tags.add("fees")
        elif rt in ("exam", "examination", "assessment"):
            resource_tags.add("marks")

    top_performers = [
        RecentActivityTopPerformerItem(
            performer_key=label,
            performer_label=label,
            module_label=data["module"],
            action_count=data["count"],
        )
        for label, data in sorted(performer_stats.items(), key=lambda x: -x[1]["count"])[:6]
    ]

    # Daily average comparison (UTC days, trailing 7 days before current window)
    compare_end = window_start
    compare_start = compare_end - timedelta(days=7)
    prior_audit = await AuditLog.find(
        {"tenant_id": tenant_id, "created_at": {"$gte": compare_start, "$lt": compare_end}},
    ).count()
    prior_inst = await InstitutionActivityLog.find(
        Eq(InstitutionActivityLog.tenant_id, tenant_id),
        {"created_at": {"$gte": compare_start, "$lt": compare_end}},
    ).count()
    prior_daily_avg = (prior_audit + prior_inst) / 7 if (prior_audit + prior_inst) else None
    actions_vs_avg: float | None = None
    if prior_daily_avg and prior_daily_avg > 0:
        baseline = prior_daily_avg if range_key == DashboardDateRange.TODAY else prior_daily_avg * 7
        actions_vs_avg = round(((feed_total - baseline) / baseline) * 100, 0)

    records_hint = "No record changes in range"
    if resource_tags:
        parts = []
        if "students" in resource_tags:
            parts.append("Students")
        if "fees" in resource_tags:
            parts.append("fees")
        if "marks" in resource_tags:
            parts.append("marks")
        if "faculty" in resource_tags:
            parts.append("faculty")
        records_hint = ", ".join(parts) if parts else "Administrative records"

    follow_ups: list[RecentActivityFollowUpItem] = []
    for e in all_events:
        if e.result_key == "errors":
            follow_ups.append(
                RecentActivityFollowUpItem(
                    item_key=e.activity_id,
                    title=e.title,
                    detail=e.result_label,
                    action_key="fix",
                    action_label="Fix",
                    resource_type=e.module_key,
                    resource_id=e.activity_id,
                )
            )
        elif e.result_key in ("pending", "in_review"):
            follow_ups.append(
                RecentActivityFollowUpItem(
                    item_key=e.activity_id,
                    title=e.title,
                    detail=f"Awaiting action on {e.module_label.lower()}",
                    action_key="waiting",
                    action_label="Waiting",
                    resource_type=e.module_key,
                    resource_id=e.activity_id,
                )
            )
        if len(follow_ups) >= 5:
            break

    partial_imports = await InstitutionImportJob.find(
        Eq(InstitutionImportJob.tenant_id, tenant_id),
        {"failed_rows": {"$gt": 0}},
    ).sort("-created_at").limit(3).to_list()
    for job in partial_imports:
        if any(f.item_key == job.job_id for f in follow_ups):
            continue
        follow_ups.append(
            RecentActivityFollowUpItem(
                item_key=job.job_id,
                title=f"Bulk import had {job.failed_rows} error{'s' if job.failed_rows != 1 else ''}",
                detail=job.error_message or "Review validation errors",
                action_key="fix",
                action_label="Fix",
                resource_type="import",
                resource_id=job.job_id,
            )
        )
        if len(follow_ups) >= 5:
            break

    user_options: list[RecentActivityUserFilterOption] = []
    seen_users: set[str] = set()
    for e in all_events:
        if not e.actor_user_id or e.actor_user_id in seen_users:
            continue
        seen_users.add(e.actor_user_id)
        user_options.append(
            RecentActivityUserFilterOption(user_id=e.actor_user_id, label=e.performed_by_label),
        )

    module_options = [
        RecentActivityModuleFilterOption(module_key=key, module_label=label)
        for key, (label, _count) in sorted(module_counts.items(), key=lambda x: x[1][0])
    ]

    period = _PERIOD_LABELS.get(range_key)
    kpi_title = _KPI_TITLES.get(range_key, "Actions")

    return RecentActivitiesOverviewRead(
        filters=RecentActivitiesOverviewFilters(
            anchor_date=anchor,
            date_range=range_key,
            module_key=module_key,
            user_id=user_id,
            feed_offset=feed_offset,
            feed_limit=feed_limit,
        ),
        scope_label="College scope",
        kpis=RecentActivitiesOverviewKpiRead(
            actions_count=feed_total,
            actions_kpi_label=kpi_title,
            actions_period_label=period or "this period",
            actions_vs_daily_avg_pct=actions_vs_avg,
            active_administrators=len(distinct_actors),
            active_role_count=len(role_keys),
            records_changed=records_changed,
            records_changed_hint=records_hint,
            failed_actions=failed_actions,
            failed_actions_hint="Validation errors" if failed_actions else "No failures",
        ),
        feed_rows=feed_rows,
        feed_total=feed_total,
        feed_limit=feed_limit,
        feed_offset=feed_offset,
        activity_by_module=by_module,
        activity_by_module_max=module_max,
        top_performers=top_performers,
        follow_ups=follow_ups[:5],
        module_filter_options=module_options,
        user_filter_options=user_options,
        generated_at=now,
    )