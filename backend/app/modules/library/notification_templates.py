"""Library notification message templates."""

from app.modules.library.notification_enums import LibraryNotificationEvent

_TEMPLATES: dict[LibraryNotificationEvent, tuple[str, str]] = {
    LibraryNotificationEvent.ISSUE: (
        "Book issued",
        'You borrowed "{title}" (copy {copy_id}). Due: {due_date}.',
    ),
    LibraryNotificationEvent.RETURN_REMINDER: (
        "Return reminder",
        'Please return "{title}" by {due_date}.',
    ),
    LibraryNotificationEvent.DUE_UPCOMING: (
        "Due date approaching",
        '"{title}" is due on {due_date}.',
    ),
    LibraryNotificationEvent.OVERDUE: (
        "Overdue item",
        '"{title}" is overdue since {due_date}. Please return or renew.',
    ),
    LibraryNotificationEvent.RESERVATION_READY: (
        "Reservation ready",
        '"{title}" is ready for pickup{branch_suffix}.',
    ),
    LibraryNotificationEvent.RESERVATION_EXPIRY: (
        "Reservation expiring",
        'Your reservation for "{title}" expires on {expires_at}.',
    ),
    LibraryNotificationEvent.FINE: (
        "Library fine",
        "A fine of {amount} was assessed: {reason}.",
    ),
    LibraryNotificationEvent.MEMBERSHIP_EXPIRY: (
        "Membership expiring",
        "Your library membership expires on {expires_on}.",
    ),
    LibraryNotificationEvent.ANNOUNCEMENT: (
        "{title}",
        "{body}",
    ),
}


def render_library_notification(event: LibraryNotificationEvent, **kwargs: str) -> tuple[str, str]:
    title_t, body_t = _TEMPLATES[event]
    title = title_t.format(**kwargs)
    body = body_t.format(**kwargs)
    return title, body