"""College admin dashboard — alerts & notifications overview."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.college_admin.attendance_overview_service import get_attendance_overview
from app.modules.college_admin.communication_admin_models import CommunicationProviderSettings, InstitutionAnnouncement
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.finance_admin_models import PaymentReconciliationRecord
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import CollegeDashboardPreferences, InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AlertsDeliveryChannelItem,
    AlertsFeaturedBanner,
    AlertsOverviewKpiRead,
    AlertsOverviewRead,
    AlertsRuleItem,
    DashboardAlertByModuleItem,
    DashboardAlertItem,
)
from app.modules.examinations.exam_cell_timetable_enums import ExamScheduleApprovalDecision
from app.modules.examinations.exam_cell_timetable_models import ExamScheduleApproval
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction
from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus, HostelOutpassRequest

_reader = OperationalDataReader()

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


@dataclass
class _AlertDraft:
    alert_id: str
    severity_key: str
    severity_label: str
    title: str
    summary: str | None
    module_key: str
    module_label: str
    raised_at: datetime
    action_key: str
    action_label: str
    action_href: str


def _fmt_time(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%H:%M")


def _fmt_inr(amount: float) -> str:
    if amount >= 100_000:
        return f"₹{amount / 100_000:.1f} L"
    return f"₹{amount:,.0f}"


def _severity_label(key: str) -> str:
    return {"critical": "Critical", "warning": "Warning", "info": "Info"}.get(key, key.title())


async def _user_prefs(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> CollegeDashboardPreferences:
    prefs = await CollegeDashboardPreferences.find_one(
        Eq(CollegeDashboardPreferences.tenant_id, tenant_id),
        Eq(CollegeDashboardPreferences.user_id, user_id),
    )
    if prefs is None:
        prefs = CollegeDashboardPreferences(tenant_id=tenant_id, user_id=user_id)
        await prefs.insert()
    return prefs


async def mark_dashboard_alerts_read(scope: AccessScope, user: User) -> dict[str, int]:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    overview = await get_alerts_overview(scope, user)
    prefs = await _user_prefs(tenant_id, user.id)
    keys = {*prefs.dismissed_alert_keys}
    for alert in overview.all_alerts:
        keys.add(alert.alert_id)
    prefs.dismissed_alert_keys = sorted(keys)
    prefs.updated_at = utcnow()
    await prefs.save()
    return {"marked": len(overview.all_alerts)}


async def get_alerts_overview(scope: AccessScope, user: User) -> AlertsOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if today_start.tzinfo is None:
        today_start = today_start.replace(tzinfo=timezone.utc)

    inst_settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    settings = (inst_settings.settings or {}) if inst_settings else {}

    prefs = await _user_prefs(tenant_id, user.id)
    dismissed = set(prefs.dismissed_alert_keys)

    drafts: list[_AlertDraft] = []

    unreconciled = await PaymentReconciliationRecord.find(
        Eq(PaymentReconciliationRecord.tenant_id, tenant_id),
        Eq(PaymentReconciliationRecord.reconciled, False),
    ).to_list()
    if unreconciled:
        tx_ids = [row.transaction_id for row in unreconciled]
        txs = await PaymentTransaction.find(
            Eq(PaymentTransaction.tenant_id, tenant_id),
            {"transaction_id": {"$in": tx_ids}},
        ).to_list()
        total_mismatch = sum(float(tx.amount or 0) for tx in txs)
        latest = max((row.created_at for row in unreconciled), default=now)
        drafts.append(
            _AlertDraft(
                alert_id="finance:reconciliation_mismatch",
                severity_key="critical",
                severity_label="Critical",
                title=f"Payment gateway settlement mismatch of {_fmt_inr(total_mismatch)}",
                summary=(
                    f"{len(unreconciled)} transactions are not reconciled. "
                    "Receipts for affected students may be on hold until the mismatch is resolved."
                ),
                module_key="finance",
                module_label="Finance",
                raised_at=latest,
                action_key="resolve",
                action_label="Resolve",
                action_href="/college-admin/finance/payment-reconciliation",
            )
        )

    hostel_pending = await HostelOutpassRequest.find(
        Eq(HostelOutpassRequest.tenant_id, tenant_id),
        Eq(HostelOutpassRequest.status, HostelLeaveOutpassStatus.PENDING_APPROVAL),
    ).to_list()
    if hostel_pending:
        oldest = min(hostel_pending, key=lambda r: r.created_at)
        age_days = max(0, (now.date() - oldest.created_at.date()).days)
        drafts.append(
            _AlertDraft(
                alert_id="hostel:bulk_outpass_pending",
                severity_key="critical" if age_days >= 3 else "warning",
                severity_label=_severity_label("critical" if age_days >= 3 else "warning"),
                title="Hostel bulk outpass approval overdue" if age_days >= 3 else "Hostel outpass approvals pending",
                summary=f"{len(hostel_pending)} students waiting · {age_days} day{'s' if age_days != 1 else ''}",
                module_key="hostel",
                module_label="Hostel",
                raised_at=oldest.created_at,
                action_key="review",
                action_label="Review",
                action_href="/college-admin/hostel/leave-outpass-approval",
            )
        )

    attendance = await get_attendance_overview(scope, date_range=DashboardDateRange.MONTH)
    below = attendance.kpis.students_below_minimum
    if below > 0:
        drafts.append(
            _AlertDraft(
                alert_id="attendance:below_minimum",
                severity_key="warning",
                severity_label="Warning",
                title=f"{below} students below minimum attendance",
                summary="Review condonation and shortage workflows before regulatory deadlines.",
                module_key="attendance",
                module_label="Attendance",
                raised_at=attendance.generated_at,
                action_key="view",
                action_label="View list",
                action_href="/college-admin/attendance-administration/shortages",
            )
        )

    exam_pending = await ExamScheduleApproval.find(
        Eq(ExamScheduleApproval.tenant_id, tenant_id),
        Eq(ExamScheduleApproval.decision, ExamScheduleApprovalDecision.PENDING),
    ).count()
    if exam_pending:
        drafts.append(
            _AlertDraft(
                alert_id="examination:timetable_approval",
                severity_key="warning",
                severity_label="Warning",
                title="Exam timetable approval pending",
                summary=f"{exam_pending} timetable submission{'s' if exam_pending != 1 else ''} awaiting decision",
                module_key="examination",
                module_label="Examinations",
                raised_at=now,
                action_key="review",
                action_label="Review",
                action_href="/college-admin/approvals/pending-approval-requests",
            )
        )

    for item in attendance.shortage_alerts:
        if item.count <= 0:
            continue
        drafts.append(
            _AlertDraft(
                alert_id=f"attendance:{item.alert_key}",
                severity_key="warning",
                severity_label="Warning",
                title=item.label,
                summary=f"{item.count} student{'s' if item.count != 1 else ''} in this band",
                module_key="attendance",
                module_label="Attendance",
                raised_at=attendance.generated_at,
                action_key="view",
                action_label="View list",
                action_href="/college-admin/attendance-administration/shortages",
            )
        )

    integration = await _reader.integration_health(tenant_id)
    for item in integration:
        status = (item.status or "").lower()
        if status in {"ok", "healthy", "up", "active", "connected"}:
            continue
        sev = "critical" if status in {"down", "failed", "error"} else "warning"
        drafts.append(
            _AlertDraft(
                alert_id=f"integration:{item.provider_code}",
                severity_key=sev,
                severity_label=_severity_label(sev),
                title=f"Integration issue · {item.provider_code}",
                summary=item.detail or f"Status: {item.status}",
                module_key="compliance",
                module_label="Compliance & others",
                raised_at=item.last_check_at or now,
                action_key="open",
                action_label="Open",
                action_href="/college-admin/integration-administration",
            )
        )

    sms_provider = await CommunicationProviderSettings.find_one(
        Eq(CommunicationProviderSettings.tenant_id, tenant_id),
        Eq(CommunicationProviderSettings.channel, "sms"),
    )
    if sms_provider:
        cfg = sms_provider.config or {}
        remaining = cfg.get("credits_remaining")
        quota = cfg.get("credits_quota") or cfg.get("quota")
        if remaining is not None and quota:
            try:
                ratio = float(remaining) / float(quota)
            except (TypeError, ValueError):
                ratio = 1.0
            if ratio < 0.1:
                drafts.append(
                    _AlertDraft(
                        alert_id="communication:sms_credits_low",
                        severity_key="warning",
                        severity_label="Warning",
                        title="SMS credits below 10%",
                        summary=f"{int(remaining):,} credits remaining",
                        module_key="communication",
                        module_label="Communication",
                        raised_at=sms_provider.updated_at,
                        action_key="top_up",
                        action_label="Top up",
                        action_href="/college-admin/communication-administration",
                    )
                )

    announcements = await (
        InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id))
        .sort("-published_at")
        .limit(15)
        .to_list()
    )
    for ann in announcements:
        if ann.status != "published":
            continue
        body_lower = (ann.body or "").lower()
        title_lower = ann.title.lower()
        if "maintenance" in title_lower or "maintenance" in body_lower:
            drafts.append(
                _AlertDraft(
                    alert_id=f"announcement:{ann.announcement_id}",
                    severity_key="info",
                    severity_label="Info",
                    title=ann.title,
                    summary=ann.body[:240] if ann.body else None,
                    module_key="platform",
                    module_label="Platform notice",
                    raised_at=ann.published_at or ann.created_at,
                    action_key="info",
                    action_label="Info",
                    action_href="/college-admin/communication-administration",
                )
            )
        elif "calendar" in title_lower or "semester" in title_lower:
            drafts.append(
                _AlertDraft(
                    alert_id=f"announcement:{ann.announcement_id}",
                    severity_key="info",
                    severity_label="Info",
                    title=ann.title,
                    summary="Published for institution stakeholders",
                    module_key="academics",
                    module_label="Academics",
                    raised_at=ann.published_at or ann.created_at,
                    action_key="info",
                    action_label="Info",
                    action_href="/college-admin/academic-configuration",
                )
            )

    failed_tx = await PaymentTransaction.find(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.status, PaymentTransactionStatus.FAILED),
    ).count()
    if failed_tx:
        drafts.append(
            _AlertDraft(
                alert_id="finance:failed_payments",
                severity_key="warning",
                severity_label="Warning",
                title=f"{failed_tx} failed online payment{'s' if failed_tx != 1 else ''}",
                summary="Review gateway responses and student receipt status",
                module_key="finance",
                module_label="Finance",
                raised_at=now,
                action_key="open",
                action_label="Open",
                action_href="/college-admin/finance-administration",
            )
        )

    compliance_due = settings.get("compliance_return_due_label")
    if compliance_due:
        drafts.append(
            _AlertDraft(
                alert_id="compliance:annual_return",
                severity_key="warning",
                severity_label="Warning",
                title=str(settings.get("compliance_return_title", "Regulatory return due")),
                summary=str(compliance_due),
                module_key="compliance",
                module_label="Institution",
                raised_at=now,
                action_key="open",
                action_label="Open",
                action_href="/college-admin/institution-profile",
            )
        )

    drafts.sort(key=lambda d: (_SEVERITY_ORDER.get(d.severity_key, 9), -d.raised_at.timestamp()))

    def to_item(d: _AlertDraft, *, read: bool) -> DashboardAlertItem:
        return DashboardAlertItem(
            alert_id=d.alert_id,
            severity_key=d.severity_key,
            severity_label=d.severity_label,
            title=d.title,
            summary=d.summary,
            module_key=d.module_key,
            module_label=d.module_label,
            raised_at=d.raised_at,
            time_label=_fmt_time(d.raised_at),
            action_key=d.action_key,
            action_label=d.action_label,
            action_href=d.action_href,
            is_read=read,
        )

    all_items = [to_item(d, read=d.alert_id in dismissed) for d in drafts]
    visible_items = [item for item in all_items if not item.is_read]

    critical = sum(1 for i in visible_items if i.severity_key == "critical")
    warning = sum(1 for i in visible_items if i.severity_key == "warning")
    info = sum(1 for i in visible_items if i.severity_key == "info")

    resolved_today = await AuditLog.find(
        {
            "tenant_id": tenant_id,
            "created_at": {"$gte": today_start},
            "outcome": {"$in": ["success", "resolved"]},
            "action": {"$regex": "reconcil|resolve|alert", "$options": "i"},
        }
    ).count()

    resolution_logs = await (
        AuditLog.find(
            {
                "tenant_id": tenant_id,
                "created_at": {"$gte": now - timedelta(days=7)},
                "metadata.resolution_hours": {"$exists": True},
            }
        )
        .limit(50)
        .to_list()
    )
    hours = [float(row.metadata["resolution_hours"]) for row in resolution_logs if row.metadata.get("resolution_hours") is not None]
    avg_resolution = round(sum(hours) / len(hours), 1) if hours else None

    featured: AlertsFeaturedBanner | None = None
    for d in drafts:
        if d.severity_key == "critical" and d.alert_id not in dismissed:
            featured = AlertsFeaturedBanner(
                alert_id=d.alert_id,
                title=d.title,
                summary=d.summary,
                action_label="Open reconciliation →" if d.module_key == "finance" else f"{d.action_label} →",
                action_href=d.action_href,
            )
            break

    module_counts: dict[str, tuple[str, int]] = {}
    for item in visible_items:
        prev = module_counts.get(item.module_key)
        module_counts[item.module_key] = (item.module_label, (prev[1] if prev else 0) + 1)
    by_module = [
        DashboardAlertByModuleItem(module_key=k, module_label=v[0], count=v[1])
        for k, v in sorted(module_counts.items(), key=lambda x: -x[1][1])
    ]
    module_max = max((m.count for m in by_module), default=1)

    providers = await CommunicationProviderSettings.find(Eq(CommunicationProviderSettings.tenant_id, tenant_id)).to_list()
    provider_by_channel = {p.channel: p for p in providers}
    digest_on = bool(settings.get("notification_digest_enabled", True))
    digest_time = str(settings.get("notification_digest_time", "Daily at 08:00 IST"))
    sms = provider_by_channel.get("sms")
    sms_phone = (sms.config or {}).get("sender_id") or (sms.config or {}).get("mask") if sms else None

    delivery_channels = [
        AlertsDeliveryChannelItem(
            channel_key="in_app",
            label="In-app notifications",
            detail="All alert levels",
            enabled=True,
        ),
        AlertsDeliveryChannelItem(
            channel_key="email_digest",
            label="Email digest",
            detail=digest_time if digest_on else "Disabled",
            enabled=digest_on,
        ),
        AlertsDeliveryChannelItem(
            channel_key="sms_critical",
            label="SMS for critical alerts",
            detail=str(sms_phone) if sms_phone else "Not configured",
            enabled=bool(sms and sms.push_enabled),
        ),
    ]

    rules = [
        AlertsRuleItem(
            rule_key="escalate_unread",
            label="Escalate if unread",
            value_label=f"{int(settings.get('alert_escalate_unread_hours', 4))} hours",
        ),
        AlertsRuleItem(
            rule_key="auto_resolve_info",
            label="Auto-resolve info",
            value_label=f"After {int(settings.get('alert_auto_resolve_info_days', 7))} days",
        ),
        AlertsRuleItem(
            rule_key="quiet_hours",
            label="Quiet hours",
            value_label=str(settings.get("alert_quiet_hours", "22:00 – 07:00")),
        ),
        AlertsRuleItem(
            rule_key="recipients",
            label="Recipients",
            value_label=str(settings.get("alert_recipients", "College Admin, Principal")),
        ),
    ]

    return AlertsOverviewRead(
        kpis=AlertsOverviewKpiRead(
            critical_count=critical,
            critical_hint="Action needed today" if critical else "No critical alerts",
            warning_count=warning,
            warning_hint="Review within 48 hours" if warning else "No warnings",
            info_count=info,
            info_hint="No action required",
            resolved_today=resolved_today,
            resolved_hint=f"Avg. {avg_resolution} hours to resolve" if avg_resolution is not None else "No recent resolutions",
            avg_resolution_hours=avg_resolution,
        ),
        featured=featured,
        all_alerts=visible_items,
        alerts_total=len(visible_items),
        alerts_by_module=by_module,
        alerts_by_module_max=module_max,
        delivery_channels=delivery_channels,
        alert_rules=rules,
        generated_at=now,
    )