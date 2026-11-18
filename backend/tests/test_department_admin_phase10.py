"""Department Admin phase 10 — unit tests (no Mongo)."""

from app.authorization.permissions import Permission, permissions_for_role
from app.common.roles import Role
from app.modules.department_admin.helpdesk_constants import (
    HELPDESK_CATEGORIES,
    PLACEMENT_ACTIVITY_TYPES,
    STATUS_TRANSITIONS,
)
from app.modules.department_admin.models import DepartmentHelpdeskStatus


def test_department_admin_phase10_permissions():
    perms = permissions_for_role(Role.DEPARTMENT_ADMIN)
    assert Permission.DEPARTMENT_HELPDESK_READ in perms
    assert Permission.DEPARTMENT_HELPDESK_MANAGE in perms
    assert Permission.DEPARTMENT_PLACEMENT_READ in perms
    assert Permission.DEPARTMENT_PLACEMENT_MANAGE in perms
    assert Permission.DEPARTMENT_RESEARCH_READ in perms
    assert Permission.DEPARTMENT_RESEARCH_MANAGE in perms


def test_helpdesk_categories_allowlist():
    assert "timetable" in HELPDESK_CATEGORIES
    assert len(HELPDESK_CATEGORIES) >= 10


def test_helpdesk_status_transitions_closed_reopen():
    assert DepartmentHelpdeskStatus.REOPENED in STATUS_TRANSITIONS[DepartmentHelpdeskStatus.CLOSED]


def test_placement_activity_types():
    assert "mock_interview" in PLACEMENT_ACTIVITY_TYPES