"""Unit tests for department calendar conflict detection."""

from datetime import datetime, time, timezone

from beanie import PydanticObjectId

from app.modules.department_admin.calendar_conflict_detection import detect_calendar_conflicts


class _Peer:
    def __init__(self, *, id: str, title: str, starts_at, ends_at, room=None, organizer=None, status="published"):
        self.id = id
        self.title = title
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.room = room
        self.organizer_user_id = organizer
        self.status = status


class _Timetable:
    def __init__(self, *, id: str, day: int, start: time, end: time, course: str, section: str, faculty_id, room=None):
        self.id = id
        self.day_of_week = day
        self.start_time = start
        self.end_time = end
        self.course_code = course
        self.section = section
        self.faculty_user_id = faculty_id
        self.room = room


def test_invalid_duration():
    start = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc)
    out = detect_calendar_conflicts(
        event_id=None,
        starts_at=start,
        ends_at=end,
        room=None,
        laboratory=None,
        organizer_faculty_id=None,
        peer_events=[],
        timetable_rows=[],
        class_sessions=[],
    )
    assert out[0]["conflict_type"] == "invalid_duration"


def test_room_overlap_with_peer():
    start = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc)
    fid = PydanticObjectId()
    peer = _Peer(
        id="a",
        title="Other",
        starts_at=start,
        ends_at=end,
        room="A101",
        organizer=fid,
    )
    out = detect_calendar_conflicts(
        event_id=None,
        starts_at=start,
        ends_at=end,
        room="A101",
        laboratory=None,
        organizer_faculty_id=fid,
        peer_events=[peer],
        timetable_rows=[],
        class_sessions=[],
    )
    types = {c["conflict_type"] for c in out}
    assert "department_room_overlap" in types
    assert "organizer_overlap" in types


def test_timetable_overlap_same_day():
    start = datetime(2026, 1, 12, 10, 30, tzinfo=timezone.utc)  # Monday = 0
    end = datetime(2026, 1, 12, 11, 30, tzinfo=timezone.utc)
    fid = PydanticObjectId()
    row = _Timetable(
        id="t1",
        day=start.weekday(),
        start=time(10, 0),
        end=time(11, 0),
        course="CS101",
        section="A",
        faculty_id=fid,
        room="B202",
    )
    out = detect_calendar_conflicts(
        event_id=None,
        starts_at=start,
        ends_at=end,
        room="B202",
        laboratory=None,
        organizer_faculty_id=fid,
        peer_events=[],
        timetable_rows=[row],
        class_sessions=[],
    )
    types = {c["conflict_type"] for c in out}
    assert "published_timetable_overlap" in types
    assert "timetable_room_overlap" in types