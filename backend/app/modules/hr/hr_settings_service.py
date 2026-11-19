"""HR general settings and policy lifecycle."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.hr.enums import HrPolicyLifecycleStatus, HrStaffActivityType
from app.modules.hr.hr_audit_integration import record_hr_audit
from app.modules.hr.hr_settings_models import (
    HrConfigurablePolicy,
    HrGeneralSettings,
    HrPolicyAcknowledgement,
    HrPolicyApproval,
    HrPolicyCategory,
    HrPolicyVersion,
)
from app.modules.hr.hr_settings_schemas import (
    GeneralSettingsRead,
    GeneralSettingsUpsert,
    PolicyAcknowledgeRequest,
    PolicyAcknowledgementRead,
    PolicyApprovalRead,
    PolicyCategoryRead,
    PolicyCategoryUpsert,
    PolicyRead,
    PolicyTransition,
    PolicyUpsert,
    PolicyVersionRead,
)
from app.modules.hr.hr_audience_resolver import resolve_hr_audience
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.hr_sod import assert_block_self_approval, assert_separation_of_duties
from app.modules.hr.policy import authorize_hr_settings_manage, authorize_hr_settings_read, require_hr_tenant_scope
from app.authorization.permissions import Permission

_TRANSITIONS: dict[HrPolicyLifecycleStatus, dict[str, HrPolicyLifecycleStatus]] = {
    HrPolicyLifecycleStatus.DRAFT: {"submit_review": HrPolicyLifecycleStatus.REVIEW},
    HrPolicyLifecycleStatus.REVIEW: {
        "approve": HrPolicyLifecycleStatus.APPROVED,
        "return_draft": HrPolicyLifecycleStatus.DRAFT,
    },
    HrPolicyLifecycleStatus.APPROVED: {
        "publish": HrPolicyLifecycleStatus.PUBLISHED,
        "schedule": HrPolicyLifecycleStatus.SCHEDULED,
    },
    HrPolicyLifecycleStatus.PUBLISHED: {"activate": HrPolicyLifecycleStatus.ACTIVE},
    HrPolicyLifecycleStatus.SCHEDULED: {"activate": HrPolicyLifecycleStatus.ACTIVE},
    HrPolicyLifecycleStatus.ACTIVE: {
        "suspend": HrPolicyLifecycleStatus.SUSPENDED,
        "expire": HrPolicyLifecycleStatus.EXPIRED,
        "supersede": HrPolicyLifecycleStatus.SUPERSEDED,
        "archive": HrPolicyLifecycleStatus.ARCHIVED,
    },
    HrPolicyLifecycleStatus.SUSPENDED: {"activate": HrPolicyLifecycleStatus.ACTIVE, "archive": HrPolicyLifecycleStatus.ARCHIVED},
}


async def get_general_settings(scope: AccessScope) -> GeneralSettingsRead:
    authorize_hr_settings_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrGeneralSettings.find_one(Eq(HrGeneralSettings.tenant_id, tenant_id))
    if doc is None:
        doc = HrGeneralSettings(tenant_id=tenant_id)
        await doc.insert()
    return GeneralSettingsRead.from_doc(doc)


async def upsert_general_settings(scope: AccessScope, payload: GeneralSettingsUpsert) -> GeneralSettingsRead:
    authorize_hr_settings_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrGeneralSettings.find_one(Eq(HrGeneralSettings.tenant_id, tenant_id))
    if doc is None:
        doc = HrGeneralSettings(tenant_id=tenant_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(doc, key, value)
    doc.actor_id = scope.user_id
    doc.updated_at = utcnow()
    if doc.id:
        await doc.save()
    else:
        await doc.insert()
    await record_hr_audit(
        tenant_id,
        HrStaffActivityType.POLICY_CHANGE,
        "General HR settings updated",
        actor_id=scope.user_id,
        resource_type="hr_general_settings",
        resource_id=str(doc.id),
    )
    return GeneralSettingsRead.from_doc(doc)


async def list_policy_categories(scope: AccessScope) -> list[PolicyCategoryRead]:
    authorize_hr_settings_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrPolicyCategory.find(Eq(HrPolicyCategory.tenant_id, tenant_id)).sort("sort_order").to_list()
    return [PolicyCategoryRead.from_doc(r) for r in rows]


async def upsert_policy_category(scope: AccessScope, payload: PolicyCategoryUpsert) -> PolicyCategoryRead:
    authorize_hr_settings_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    code = payload.category_code.strip().lower()
    doc = await HrPolicyCategory.find_one(Eq(HrPolicyCategory.tenant_id, tenant_id), Eq(HrPolicyCategory.category_code, code))
    if doc is None:
        doc = HrPolicyCategory(tenant_id=tenant_id, category_code=code, title=payload.title)
    doc.title = payload.title
    doc.description = payload.description
    doc.sort_order = payload.sort_order
    if doc.id:
        await doc.save()
    else:
        await doc.insert()
    return PolicyCategoryRead.from_doc(doc)


async def list_policies(scope: AccessScope, category_code: str | None = None) -> list[PolicyRead]:
    authorize_hr_settings_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    if category_code:
        rows = await HrConfigurablePolicy.find(
            Eq(HrConfigurablePolicy.tenant_id, tenant_id),
            Eq(HrConfigurablePolicy.category_code, category_code.strip().lower()),
        ).to_list()
    else:
        rows = await HrConfigurablePolicy.find(Eq(HrConfigurablePolicy.tenant_id, tenant_id)).to_list()
    return [PolicyRead.from_doc(r) for r in rows]


async def upsert_policy(scope: AccessScope, payload: PolicyUpsert) -> PolicyRead:
    authorize_hr_settings_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    code = payload.policy_code.strip().lower()
    cat = payload.category_code.strip().lower()
    cat_doc = await HrPolicyCategory.find_one(Eq(HrPolicyCategory.tenant_id, tenant_id), Eq(HrPolicyCategory.category_code, cat))
    if cat_doc is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown policy category", status_code=422)
    doc = await HrConfigurablePolicy.find_one(Eq(HrConfigurablePolicy.tenant_id, tenant_id), Eq(HrConfigurablePolicy.policy_code, code))
    new_version = False
    if doc is None:
        doc = HrConfigurablePolicy(
            tenant_id=tenant_id,
            policy_code=code,
            category_code=cat,
            title=payload.title,
            settings=payload.settings,
            requires_acknowledgement=payload.requires_acknowledgement,
            actor_id=scope.user_id,
        )
        await doc.insert()
        new_version = True
    else:
        if doc.status not in {HrPolicyLifecycleStatus.DRAFT, HrPolicyLifecycleStatus.REVIEW}:
            doc.current_version += 1
            new_version = True
        doc.title = payload.title
        doc.description = payload.description
        doc.settings = payload.settings
        doc.requires_acknowledgement = payload.requires_acknowledgement
        doc.actor_id = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    if new_version:
        ver = HrPolicyVersion(
            tenant_id=tenant_id,
            policy_id=doc.id,
            policy_code=code,
            version_number=doc.current_version,
            status=doc.status,
            settings=dict(payload.settings),
            change_summary=payload.change_summary,
            actor_id=scope.user_id,
        )
        await ver.insert()
    await record_hr_audit(
        tenant_id,
        HrStaffActivityType.POLICY_CHANGE,
        f"Policy {code} saved (v{doc.current_version})",
        actor_id=scope.user_id,
        resource_type="hr_policy",
        resource_id=code,
        metadata={"category": cat},
    )
    return PolicyRead.from_doc(doc)


async def get_policy(scope: AccessScope, policy_id: str) -> PolicyRead:
    authorize_hr_settings_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(policy_id, "policy_id")
    doc = await HrConfigurablePolicy.find_one(Eq(HrConfigurablePolicy.tenant_id, tenant_id), Eq(HrConfigurablePolicy.id, pid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Policy not found", status_code=404)
    return PolicyRead.from_doc(doc)


async def transition_policy(scope: AccessScope, policy_id: str, payload: PolicyTransition) -> PolicyRead:
    authorize_hr_settings_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(policy_id, "policy_id")
    doc = await HrConfigurablePolicy.find_one(Eq(HrConfigurablePolicy.tenant_id, tenant_id), Eq(HrConfigurablePolicy.id, pid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Policy not found", status_code=404)
    action = payload.action.strip().lower()
    mapping = _TRANSITIONS.get(doc.status, {})
    if action not in mapping:
        raise AppError(code="VALIDATION_ERROR", message="Invalid transition for current status", status_code=422)
    if action in {"approve", "publish"}:
        assert_separation_of_duties(scope, acting_permission=Permission.HR_SETTINGS_MANAGE)
    if action == "approve":
        await assert_block_self_approval(tenant_id, actor_id=scope.user_id, resource_owner_id=doc.actor_id)
    new_status = mapping[action]
    doc.status = new_status
    if payload.effective_from:
        doc.effective_from = payload.effective_from
    if payload.effective_to:
        doc.effective_to = payload.effective_to
    if new_status == HrPolicyLifecycleStatus.PUBLISHED:
        doc.published_at = utcnow()
        doc.approved_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await HrPolicyApproval(
        tenant_id=tenant_id,
        policy_id=doc.id,
        version_number=doc.current_version,
        action=action,
        note=payload.note,
        actor_id=scope.user_id,
    ).insert()
    ver = await HrPolicyVersion.find_one(
        Eq(HrPolicyVersion.tenant_id, tenant_id),
        Eq(HrPolicyVersion.policy_id, doc.id),
        Eq(HrPolicyVersion.version_number, doc.current_version),
    )
    if ver:
        ver.status = new_status
        if payload.effective_from:
            ver.effective_from = payload.effective_from
        if payload.effective_to:
            ver.effective_to = payload.effective_to
        await ver.save()
    await record_hr_audit(
        tenant_id,
        HrStaffActivityType.POLICY_CHANGE,
        f"Policy {doc.policy_code} -> {new_status.value}",
        actor_id=scope.user_id,
        resource_type="hr_policy",
        resource_id=doc.policy_code,
        metadata={"action": action},
    )
    if new_status in {HrPolicyLifecycleStatus.PUBLISHED, HrPolicyLifecycleStatus.ACTIVE} and doc.requires_acknowledgement:
        await _ensure_policy_acknowledgements(tenant_id, doc)
    return PolicyRead.from_doc(doc)


async def list_policy_versions(scope: AccessScope, policy_id: str) -> list[PolicyVersionRead]:
    authorize_hr_settings_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(policy_id, "policy_id")
    rows = await HrPolicyVersion.find(Eq(HrPolicyVersion.tenant_id, tenant_id), Eq(HrPolicyVersion.policy_id, pid)).sort("-version_number").to_list()
    return [PolicyVersionRead.from_doc(r) for r in rows]


async def list_policy_approvals(scope: AccessScope, policy_id: str) -> list[PolicyApprovalRead]:
    authorize_hr_settings_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(policy_id, "policy_id")
    rows = await HrPolicyApproval.find(Eq(HrPolicyApproval.tenant_id, tenant_id), Eq(HrPolicyApproval.policy_id, pid)).sort("-created_at").to_list()
    return [PolicyApprovalRead.from_doc(r) for r in rows]


async def list_pending_acknowledgements(scope: AccessScope, employee_user_id: str | None = None) -> list[PolicyAcknowledgementRead]:
    authorize_hr_settings_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    query: dict = {"tenant_id": tenant_id, "acknowledged_at": None}
    if employee_user_id:
        query["employee_user_id"] = to_object_id(employee_user_id, "employee_user_id")
    rows = await HrPolicyAcknowledgement.find(query).to_list()
    return [PolicyAcknowledgementRead.from_doc(r) for r in rows]


async def acknowledge_policy(
    scope: AccessScope,
    policy_id: str,
    payload: PolicyAcknowledgeRequest,
    *,
    employee_user_id: PydanticObjectId | None = None,
) -> PolicyAcknowledgementRead:
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(policy_id, "policy_id")
    subject = employee_user_id or scope.user_id
    if subject != scope.user_id:
        authorize_hr_settings_manage(scope)
    doc = await HrConfigurablePolicy.find_one(Eq(HrConfigurablePolicy.tenant_id, tenant_id), Eq(HrConfigurablePolicy.id, pid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Policy not found", status_code=404)
    if doc.status not in {HrPolicyLifecycleStatus.PUBLISHED, HrPolicyLifecycleStatus.ACTIVE}:
        raise AppError(code="VALIDATION_ERROR", message="Policy not published", status_code=422)
    ack = await HrPolicyAcknowledgement.find_one(
        Eq(HrPolicyAcknowledgement.tenant_id, tenant_id),
        Eq(HrPolicyAcknowledgement.policy_id, pid),
        Eq(HrPolicyAcknowledgement.employee_user_id, subject),
        Eq(HrPolicyAcknowledgement.version_number, doc.current_version),
    )
    now = utcnow()
    if ack is None:
        ack = HrPolicyAcknowledgement(
            tenant_id=tenant_id,
            policy_id=pid,
            policy_code=doc.policy_code,
            version_number=doc.current_version,
            employee_user_id=subject,
        )
    ack.viewed_at = ack.viewed_at or now
    if not payload.viewed_only:
        ack.acknowledged_at = now
    if ack.id:
        await ack.save()
    else:
        await ack.insert()
    return PolicyAcknowledgementRead.from_doc(ack)


async def _ensure_policy_acknowledgements(tenant_id: PydanticObjectId, policy: HrConfigurablePolicy) -> None:
    employee_ids = await resolve_hr_audience(tenant_id, {"all_employees": True})
    await seed_acknowledgement_for_publish(tenant_id, policy, employee_ids)
    for eid in employee_ids:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.policy.acknowledgement_required",
            aggregate_type="hr_policy",
            aggregate_id=f"{policy.policy_code}:v{policy.current_version}",
            title=f"Policy acknowledgement required: {policy.title}",
            body=f"Review and acknowledge {policy.title} ({policy.policy_code}, v{policy.current_version}).",
            recipient_user_id=eid,
            dedupe_key=f"hr-policy-ack-{policy.id}-{policy.current_version}-{eid}",
        )


async def list_policy_acknowledgements(scope: AccessScope, policy_id: str) -> list[PolicyAcknowledgementRead]:
    authorize_hr_settings_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(policy_id, "policy_id")
    rows = await HrPolicyAcknowledgement.find(
        Eq(HrPolicyAcknowledgement.tenant_id, tenant_id),
        Eq(HrPolicyAcknowledgement.policy_id, pid),
    ).sort("-created_at").to_list()
    return [PolicyAcknowledgementRead.from_doc(r) for r in rows]


async def send_acknowledgement_reminders(scope: AccessScope, policy_id: str | None = None) -> dict:
    authorize_hr_settings_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    query: dict = {"tenant_id": tenant_id, "acknowledged_at": None}
    if policy_id:
        query["policy_id"] = to_object_id(policy_id, "policy_id")
    pending = await HrPolicyAcknowledgement.find(query).to_list()
    sent = 0
    now = utcnow()
    for row in pending:
        row.reminder_count += 1
        await row.save()
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.policy.acknowledgement_reminder",
            aggregate_type="hr_policy",
            aggregate_id=f"{row.policy_code}:v{row.version_number}",
            title=f"Reminder: acknowledge policy {row.policy_code}",
            body=f"Policy {row.policy_code} (v{row.version_number}) is still pending your acknowledgement.",
            recipient_user_id=row.employee_user_id,
            dedupe_key=f"hr-policy-remind-{row.id}-{row.reminder_count}",
        )
        sent += 1
    await record_hr_audit(
        tenant_id,
        HrStaffActivityType.POLICY_CHANGE,
        f"Policy acknowledgement reminders sent ({sent})",
        actor_id=scope.user_id,
        resource_type="hr_policy_ack",
        resource_id=policy_id or "all",
        metadata={"sent": sent},
    )
    return {"reminders_sent": sent, "pending_total": len(pending)}


async def seed_acknowledgement_for_publish(tenant_id: PydanticObjectId, policy: HrConfigurablePolicy, employee_ids: list[PydanticObjectId]) -> None:
    for eid in employee_ids:
        existing = await HrPolicyAcknowledgement.find_one(
            Eq(HrPolicyAcknowledgement.tenant_id, tenant_id),
            Eq(HrPolicyAcknowledgement.policy_id, policy.id),
            Eq(HrPolicyAcknowledgement.employee_user_id, eid),
            Eq(HrPolicyAcknowledgement.version_number, policy.current_version),
        )
        if existing:
            continue
        await HrPolicyAcknowledgement(
            tenant_id=tenant_id,
            policy_id=policy.id,
            policy_code=policy.policy_code,
            version_number=policy.current_version,
            employee_user_id=eid,
        ).insert()