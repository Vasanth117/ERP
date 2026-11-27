"""Communication create announcement page (CA 14.03)."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.communication_admin_models import (
    AnnouncementAudience,
    CommunicationProviderSettings,
    InstitutionAnnouncement,
)
from app.modules.college_admin.communication_admin_service import publish_announcement
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CommunicationCreateAnnouncementFormValues,
    CommunicationCreateAnnouncementPageRead,
    CommunicationCreateAnnouncementSave,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)

_PUBLISH_OPTIONS = [
    InstitutionFieldOption(value="now", label="Now"),
    InstitutionFieldOption(value="schedule", label="Schedule"),
]

_CHANNEL_OPTIONS = [
    InstitutionFieldOption(value="in_app", label="In-app"),
    InstitutionFieldOption(value="email", label="Email"),
    InstitutionFieldOption(value="sms", label="SMS"),
    InstitutionFieldOption(value="whatsapp", label="WhatsApp"),
]

_AUDIENCE_OPTIONS = [
    InstitutionFieldOption(value=AnnouncementAudience.ALL.value, label="Everyone"),
    InstitutionFieldOption(value=AnnouncementAudience.STUDENTS.value, label="All students"),
    InstitutionFieldOption(value=AnnouncementAudience.FACULTY.value, label="All faculty"),
    InstitutionFieldOption(value=AnnouncementAudience.PARENTS.value, label="Parents and guardians"),
    InstitutionFieldOption(value=AnnouncementAudience.DEPARTMENT.value, label="Department"),
    InstitutionFieldOption(value=AnnouncementAudience.CUSTOM.value, label="Custom group"),
]

_FIELD_META = [
    InstitutionFieldMeta(key="title", label="Title", field_type="text", required=True),
    InstitutionFieldMeta(key="body", label="Message", field_type="textarea", required=True),
    InstitutionFieldMeta(key="attachment_name", label="Attachment", field_type="text", required=False),
    InstitutionFieldMeta(key="audience", label="Audience", field_type="select", required=True),
    InstitutionFieldMeta(key="department_scope", label="Departments", field_type="select", required=False),
    InstitutionFieldMeta(key="publish_timing", label="Publish", field_type="select", required=True),
]


def _default_form() -> CommunicationCreateAnnouncementFormValues:
    return CommunicationCreateAnnouncementFormValues(
        announcement_id="",
        title="",
        body="",
        attachment_name="",
        audience=AnnouncementAudience.STUDENTS.value,
        department_scope="all",
        channels=["in_app", "email"],
        publish_timing="now",
        scheduled_for="",
        pin_to_dashboard=False,
    )


def _form_from_doc(doc: InstitutionAnnouncement) -> CommunicationCreateAnnouncementFormValues:
    scheduled = ""
    if doc.scheduled_for:
        local = doc.scheduled_for.astimezone() if doc.scheduled_for.tzinfo else doc.scheduled_for
        scheduled = local.isoformat(timespec="minutes")
    timing = "schedule" if doc.status == "scheduled" and doc.scheduled_for else "now"
    if doc.status == "draft":
        timing = "now"
    return CommunicationCreateAnnouncementFormValues(
        announcement_id=doc.announcement_id,
        title=doc.title,
        body=doc.body,
        attachment_name=doc.attachment_name or "",
        audience=doc.audience.value if hasattr(doc.audience, "value") else str(doc.audience),
        department_scope=doc.department_scope or "all",
        channels=list(doc.channels or ["in_app"]),
        publish_timing=timing,
        scheduled_for=scheduled,
        pin_to_dashboard=bool(doc.pin_to_dashboard),
    )


async def _department_options(tenant_id) -> list[InstitutionFieldOption]:
    rows = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).sort("name").to_list()
    options = [InstitutionFieldOption(value="all", label="All")]
    for dept in rows:
        code = (dept.department_code or dept.name or str(dept.id)).strip()
        label = (dept.name or code).strip()
        if code:
            options.append(InstitutionFieldOption(value=code, label=label))
    return options


async def _enabled_channels(tenant_id) -> list[InstitutionFieldOption]:
    providers = await CommunicationProviderSettings.find(Eq(CommunicationProviderSettings.tenant_id, tenant_id)).to_list()
    enabled = {p.channel for p in providers if p.push_enabled}
    options = [opt for opt in _CHANNEL_OPTIONS if opt.value == "in_app" or opt.value in enabled]
    if len(options) == 1:
        return list(_CHANNEL_OPTIONS)
    return options


async def get_communication_create_announcement_page(
    scope: AccessScope,
    *,
    announcement_id: str | None = None,
    audience: str | None = None,
    preset_channels: str | None = None,
    preset_publish_timing: str | None = None,
) -> CommunicationCreateAnnouncementPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    form = _default_form()
    if audience and not announcement_id:
        try:
            AnnouncementAudience(audience)
            form = form.model_copy(update={"audience": audience})
        except ValueError:
            pass
    if preset_channels and not announcement_id:
        channels = [part.strip() for part in preset_channels.split(",") if part.strip()]
        if channels:
            form = form.model_copy(update={"channels": channels})
    if preset_publish_timing and not announcement_id:
        timing = preset_publish_timing.strip().lower()
        if timing in {"schedule", "now"}:
            form = form.model_copy(update={"publish_timing": timing})
    if announcement_id:
        doc = await InstitutionAnnouncement.find_one(
            Eq(InstitutionAnnouncement.tenant_id, tenant_id),
            Eq(InstitutionAnnouncement.announcement_id, announcement_id.strip()),
        )
        if doc:
            form = _form_from_doc(doc)

    dept_options = await _department_options(tenant_id)
    channel_options = await _enabled_channels(tenant_id)

    return CommunicationCreateAnnouncementPageRead(
        page_title="Create Announcement",
        page_subtitle="Compose, target and schedule",
        back_href="/college-admin/communication/announcements-management",
        back_label="Announcements",
        cancel_label="Cancel",
        save_draft_label="Save draft",
        publish_label="Publish",
        message_section_title="Message",
        audience_section_title="Audience and delivery",
        pin_to_dashboard_label="Pin to dashboard",
        field_meta=_FIELD_META,
        audience_options=_AUDIENCE_OPTIONS,
        department_options=dept_options,
        channel_options=channel_options,
        publish_options=_PUBLISH_OPTIONS,
        form=form,
        generated_at=now,
    )


def _parse_schedule(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


async def save_communication_create_announcement_page(
    scope: AccessScope,
    payload: CommunicationCreateAnnouncementSave,
) -> CommunicationCreateAnnouncementPageRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    form = payload.form
    action = (payload.action or "draft").lower()

    aid = (form.announcement_id or "").strip() or f"ann_{uuid4().hex[:10]}"
    dept_id = None
    if form.department_scope and form.department_scope != "all":
        dept = await InstitutionDepartment.find_one(
            Eq(InstitutionDepartment.tenant_id, tenant_id),
            Eq(InstitutionDepartment.department_code, form.department_scope),
        )
        if dept:
            dept_id = dept.id

    try:
        audience = AnnouncementAudience(form.audience)
    except ValueError:
        raise AppError(code="VALIDATION_ERROR", message="Invalid audience", status_code=422) from None

    doc = await InstitutionAnnouncement.find_one(
        Eq(InstitutionAnnouncement.tenant_id, tenant_id),
        Eq(InstitutionAnnouncement.announcement_id, aid),
    )
    scheduled_for = _parse_schedule(form.scheduled_for) if form.publish_timing == "schedule" else None
    status = "scheduled" if form.publish_timing == "schedule" and scheduled_for else "draft"

    if doc is None:
        doc = InstitutionAnnouncement(
            tenant_id=tenant_id,
            announcement_id=aid,
            title=form.title.strip(),
            body=form.body.strip(),
            audience=audience,
            department_id=dept_id,
            channels=form.channels or ["in_app"],
            attachment_name=form.attachment_name.strip() or None,
            department_scope=form.department_scope or "all",
            pin_to_dashboard=form.pin_to_dashboard,
            status=status,
            scheduled_for=scheduled_for,
            actor_id=scope.user_id,
        )
        await doc.insert()
    else:
        doc.title = form.title.strip()
        doc.body = form.body.strip()
        doc.audience = audience
        doc.department_id = dept_id
        doc.channels = form.channels or ["in_app"]
        doc.attachment_name = form.attachment_name.strip() or None
        doc.department_scope = form.department_scope or "all"
        doc.pin_to_dashboard = form.pin_to_dashboard
        doc.scheduled_for = scheduled_for
        if doc.status != "published":
            doc.status = status if action != "publish" or form.publish_timing != "now" else doc.status
        doc.updated_at = utcnow()
        await doc.save()

    if action == "publish":
        if form.publish_timing == "now":
            await publish_announcement(scope, aid)
        elif form.publish_timing == "schedule" and scheduled_for:
            doc = await InstitutionAnnouncement.find_one(
                Eq(InstitutionAnnouncement.tenant_id, tenant_id),
                Eq(InstitutionAnnouncement.announcement_id, aid),
            )
            if doc and doc.status != "published":
                doc.status = "scheduled"
                doc.scheduled_for = scheduled_for
                doc.updated_at = utcnow()
                await doc.save()

    return await get_communication_create_announcement_page(scope, announcement_id=aid)