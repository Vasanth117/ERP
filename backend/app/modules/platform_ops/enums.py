"""Platform operations enums."""

from enum import Enum


class IncidentStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BackgroundJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    RETRYING = "retrying"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


INCIDENT_TRANSITIONS: dict[IncidentStatus, frozenset[IncidentStatus]] = {
    IncidentStatus.OPEN: frozenset({IncidentStatus.ACKNOWLEDGED, IncidentStatus.CLOSED}),
    IncidentStatus.ACKNOWLEDGED: frozenset({IncidentStatus.INVESTIGATING, IncidentStatus.CLOSED}),
    IncidentStatus.INVESTIGATING: frozenset({IncidentStatus.IDENTIFIED, IncidentStatus.MONITORING, IncidentStatus.RESOLVED}),
    IncidentStatus.IDENTIFIED: frozenset({IncidentStatus.MONITORING, IncidentStatus.RESOLVED}),
    IncidentStatus.MONITORING: frozenset({IncidentStatus.RESOLVED, IncidentStatus.INVESTIGATING}),
    IncidentStatus.RESOLVED: frozenset({IncidentStatus.CLOSED, IncidentStatus.MONITORING}),
    IncidentStatus.CLOSED: frozenset(),
}


def assert_incident_transition(current: IncidentStatus, target: IncidentStatus) -> None:
    allowed = INCIDENT_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition incident from {current.value} to {target.value}")
