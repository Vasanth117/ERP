"""Email/push dispatch stubs with delivery logging."""

from beanie import PydanticObjectId

from app.modules.faculty.communication_models import FacultyNotificationDeliveryLog


async def queue_faculty_notification(
    *,
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    channel: str,
    template: str,
    payload_ref: str | None,
    email_enabled: bool,
    push_enabled: bool,
) -> None:
    status = "skipped"
    error = None
    if channel == "email" and email_enabled:
        status = "queued"
    elif channel == "push" and push_enabled:
        status = "queued"
    elif channel in {"email", "push"}:
        status = "disabled"
    else:
        status = "queued"
    log = FacultyNotificationDeliveryLog(
        tenant_id=tenant_id,
        user_id=user_id,
        channel=channel,
        template=template,
        status=status,
        error=error,
        payload_ref=payload_ref,
    )
    await log.insert()


async def integration_available(provider_code: str) -> bool:
    from app.modules.integrations.models import IntegrationProvider

    row = await IntegrationProvider.find_one({"code": provider_code, "is_active": True})
    return row is not None
