"""Institutional attendance percentage rules."""

from app.modules.attendance.enums import AttendanceMarkStatus
from app.modules.attendance.models import AttendancePolicyRules, AttendanceRecord


def weight_for_status(status: AttendanceMarkStatus, rules: AttendancePolicyRules) -> float:
    if status == AttendanceMarkStatus.PRESENT:
        return rules.present_weight
    if status == AttendanceMarkStatus.LATE:
        return rules.late_weight
    if status == AttendanceMarkStatus.EXCUSED:
        return rules.excused_weight
    return rules.absent_weight


def calculate_percentage(records: list[AttendanceRecord], rules: AttendancePolicyRules) -> float:
    if not records:
        return 0.0
    total = sum(weight_for_status(r.status, rules) for r in records)
    return round((total / len(records)) * 100, 2)
