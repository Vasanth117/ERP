"""Incident state machine tests."""

import pytest

from app.modules.platform_ops.enums import IncidentStatus, assert_incident_transition


def test_open_to_acknowledged() -> None:
    assert_incident_transition(IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED)


def test_closed_is_terminal() -> None:
    with pytest.raises(ValueError):
        assert_incident_transition(IncidentStatus.CLOSED, IncidentStatus.OPEN)
