"""Finance reminder policies and scheduled reminder execution."""

import uuid
from datetime import date, datetime, timedelta, timezone

from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.accounts_finance.finance_notification_dispatch import enqueue_finance_notification
from app.modules.accounts_finance.phase11_models import FinanceNotificationEscalation, FinanceReminderPolicy, FinanceScheduledReminder
from app.modules.accounts_finance.policy import authorize_finance_notify_manage, authorize_finance_notify_read, require_finance_tenant_scope
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def upsert_reminder_policy(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_notify_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    policy_id = payload.get("policy_id") or f"frp_{uuid.uuid4().hex[:8]}"
    doc = await FinanceReminderPolicy.find_one(
        Eq(FinanceReminderPolicy.tenant_id, tenant_id),
        Eq(FinanceReminderPolicy.policy_id, policy_id),
    )
    if doc is None:
        doc = FinanceReminderPolicy(
            tenant_id=tenant_id,
            policy_id=policy_id,
            category=payload["category"],
            days_before_due=int(payload.get("days_before_due") or 0),
            days_after_due=int(payload.get("days_after_due") or 0),
            channel=payload.get("channel") or "in_app",
            max_reminders=int(payload.get("max_reminders") or 3),
            template_subject=payload.get("template_subject") or "Finance reminder",
            template_body=payload.get("template_body") or "Please review your finance account.",
        )
        await doc.insert()
    else:
        doc.active = bool(payload.get("active", doc.active))
        await doc.save()
    return {"policy_id": policy_id}


async def notification_dashboard(scope: AccessScope) -> dict:
    authorize_finance_notify_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    from app.modules.accounts_finance.phase11_models import FinanceNotificationEvent, FinanceNotificationFailure

    events = await FinanceNotificationEvent.find(Eq(FinanceNotificationEvent.tenant_id, tenant_id)).to_list()
    failed = await FinanceNotificationFailure.find(Eq(FinanceNotificationFailure.tenant_id, tenant_id)).count()
    outbox_pending = await DomainOutboxEvent.find(
        Eq(DomainOutboxEvent.tenant_id, tenant_id),
        Eq(DomainOutboxEvent.status, OutboxEventStatus.PENDING),
        In(DomainOutboxEvent.event_type, ["finance.notification.dispatch", "finance.invoice.issued", "finance.receipt.issued"]),
    ).count()
    return {
        "total_notifications": len(events),
        "queued": sum(1 for e in events if e.status in ("queued", "scheduled")),
        "sent": sum(1 for e in events if e.status in ("sent", "delivered")),
        "failed": failed,
        "outbox_pending_finance": outbox_pending,
        "open_escalations": await FinanceNotificationEscalation.find(
            Eq(FinanceNotificationEscalation.tenant_id, tenant_id),
            Eq(FinanceNotificationEscalation.status, "open"),
        ).count(),
    }


async def run_fee_due_reminders(scope: AccessScope) -> dict:
    authorize_finance_notify_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    policies = await FinanceReminderPolicy.find(
        Eq(FinanceReminderPolicy.tenant_id, tenant_id),
        Eq(FinanceReminderPolicy.active, True),
        Eq(FinanceReminderPolicy.category, "fee_due"),
    ).to_list()
    if not policies:
        return {"sent": 0, "note": "No active fee_due policy"}
    policy = policies[0]
    today = date.today()
    windows = [today + timedelta(days=policy.days_before_due)] if policy.days_before_due else [today]
    sent = 0
    for target_day in windows:
        demands = await StudentFeeDemand.find(
            Eq(StudentFeeDemand.tenant_id, tenant_id),
            Eq(StudentFeeDemand.due_date, target_day),
            In(StudentFeeDemand.status, [FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID]),
        ).to_list()
        for d in demands:
            dedupe = f"fee_due:{d.demand_id}:{target_day.isoformat()}"
            title = policy.template_subject
            body = policy.template_body.replace("{amount}", str(d.amount))
            await enqueue_finance_notification(
                tenant_id,
                category="fee_due",
                recipient_user_id=d.student_user_id,
                title=title,
                body=body,
                reference_type="student_fee_demand",
                reference_id=d.demand_id,
                dedupe_key=dedupe,
                channel=policy.channel,
                metadata={"amount": d.amount, "due_date": target_day.isoformat()},
            )
            sent += 1
    overdue = today - timedelta(days=policy.days_after_due or 1)
    overdue_demands = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        Eq(StudentFeeDemand.status, FeeDemandStatus.OVERDUE),
    ).to_list()
    for d in overdue_demands:
        if d.due_date <= overdue:
            dedupe = f"fee_overdue:{d.demand_id}:{today.isoformat()}"
            await enqueue_finance_notification(
                tenant_id,
                category="fee_overdue",
                recipient_user_id=d.student_user_id,
                title="Overdue fee reminder",
                body=f"Your fee obligation {d.demand_id} is overdue.",
                reference_type="student_fee_demand",
                reference_id=d.demand_id,
                dedupe_key=dedupe,
                channel=policy.channel,
            )
            sent += 1
            esc_id = f"fne_{uuid.uuid4().hex[:8]}"
            if not await FinanceNotificationEscalation.find_one(
                Eq(FinanceNotificationEscalation.tenant_id, tenant_id),
                Eq(FinanceNotificationEscalation.reference_id, d.demand_id),
            ):
                await FinanceNotificationEscalation(
                    tenant_id=tenant_id,
                    escalation_id=esc_id,
                    category="fee_overdue",
                    reference_id=d.demand_id,
                    level=policy.escalation_level,
                ).insert()
    schedule_id = f"sch_{uuid.uuid4().hex[:8]}"
    await FinanceScheduledReminder(
        tenant_id=tenant_id,
        schedule_id=schedule_id,
        policy_id=policy.policy_id,
        next_run_at=datetime.now(timezone.utc) + timedelta(days=1),
    ).insert()
    return {"reminders_queued": sent}