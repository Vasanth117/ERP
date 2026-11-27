"""Custom report builder field catalog (CA 16 Custom & scheduled)."""

from __future__ import annotations

from dataclasses import dataclass

_BUILDER_SOURCES: dict[str, dict] = {
    "students": {
        "label": "Students",
        "report_key": "enrollment",
        "fields": (
            ("name", "Name"),
            ("register_no", "Register no."),
            ("programme", "Programme"),
            ("section", "Section"),
            ("attendance", "Attendance"),
        ),
        "group_by": (("programme", "Programme"), ("section", "Section"), ("department", "Department")),
        "sort_by": (("register_no", "Register no."), ("name", "Name"), ("programme", "Programme")),
    },
    "attendance": {
        "label": "Attendance",
        "report_key": "attendance",
        "fields": (
            ("name", "Name"),
            ("programme", "Programme"),
            ("attendance_pct", "Att. %"),
            ("present_days", "Present days"),
        ),
        "group_by": (("programme", "Programme"), ("department", "Department")),
        "sort_by": (("attendance_pct", "Att. %"), ("name", "Name")),
    },
    "finance": {
        "label": "Fee collection",
        "report_key": "finance",
        "fields": (
            ("student_name", "Student"),
            ("invoice", "Invoice"),
            ("amount", "Amount"),
            ("status", "Status"),
        ),
        "group_by": (("programme", "Programme"), ("payment_mode", "Payment mode")),
        "sort_by": (("amount", "Amount"), ("student_name", "Student")),
    },
}


@dataclass(frozen=True)
class BuilderSourceMeta:
    source_key: str
    label: str
    report_key: str


def builder_sources() -> tuple[BuilderSourceMeta, ...]:
    return tuple(
        BuilderSourceMeta(source_key=key, label=meta["label"], report_key=meta["report_key"])
        for key, meta in _BUILDER_SOURCES.items()
    )


def source_config(source_key: str) -> dict | None:
    return _BUILDER_SOURCES.get(source_key)


def default_source_key() -> str:
    return "students"