"""Conflict hints for department calendar events (advisory)."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

from beanie import PydanticObjectId


def dt_ranges_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and start_b < end_a


def time_ranges_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return start_a < end_b and start_b < end_a


def detect_calendar_conflicts(
    *,
    event_id: str | None,
    starts_at: datetime,
    ends_at: datetime,
    room: str | None,
    laboratory: str | None,
    organizer_faculty_id: PydanticObjectId | None,
    peer_events: list[Any],
    timetable_rows: list[Any],
    class_sessions: list[Any],
) -> list[dict[str, str]]:
    if ends_at <= starts_at:
        return [{"conflict_type": "invalid_duration", "message": "End must be after start"}]
    conflicts: list[dict[str, str]] = []
    day = starts_at.weekday()
    ev_start = starts_at.time()
    ev_end = ends_at.time() if ends_at.date() == starts_at.date() else time(23, 59)
    for peer in peer_events:
        if event_id and str(getattr(peer, "id", "")) == event_id:
            continue
        if getattr(peer, "status", None) and str(peer.status) == "cancelled":
            continue
        if not dt_ranges_overlap(starts_at, ends_at, peer.starts_at, peer.ends_at):
            continue
        if room and peer.room and room.lower() == peer.room.lower():
            conflicts.append(
                {
                    "conflict_type": "department_room_overlap",
                    "message": f"Room {room} overlaps department event {peer.title}",
                    "event_id": str(peer.id),
                }
            )
        if organizer_faculty_id and peer.organizer_user_id == organizer_faculty_id:
            conflicts.append(
                {
                    "conflict_type": "organizer_overlap",
                    "message": f"Organizer has overlapping event {peer.title}",
                    "event_id": str(peer.id),
                }
            )
    for row in timetable_rows:
        if getattr(row, "day_of_week", None) != day:
            continue
        if organizer_faculty_id and row.faculty_user_id != organizer_faculty_id:
            continue
        if not time_ranges_overlap(ev_start, ev_end, row.start_time, row.end_time):
            continue
        conflicts.append(
            {
                "conflict_type": "published_timetable_overlap",
                "message": f"Timetable {row.course_code}/{row.section} on this slot",
                "reference_id": str(row.id),
            }
        )
        if room and row.room and room.lower() == row.room.lower():
            conflicts.append(
                {
                    "conflict_type": "timetable_room_overlap",
                    "message": f"Published timetable uses room {room}",
                    "reference_id": str(row.id),
                }
            )
    for session in class_sessions:
        if not dt_ranges_overlap(starts_at, ends_at, session.scheduled_start, session.scheduled_end):
            continue
        if organizer_faculty_id and session.faculty_user_id != organizer_faculty_id:
            continue
        conflicts.append(
            {
                "conflict_type": "class_session_overlap",
                "message": f"Class session {session.course_code}/{session.section}",
                "reference_id": str(session.id),
            }
        )
        if laboratory and session.laboratory and laboratory.lower() == session.laboratory.lower():
            conflicts.append(
                {
                    "conflict_type": "laboratory_overlap",
                    "message": f"Lab {laboratory} in use",
                    "reference_id": str(session.id),
                }
            )
    return conflicts