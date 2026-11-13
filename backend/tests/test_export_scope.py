"""Export scope and cross-tenant safety."""

import pytest

from app.modules.data_governance.enums import ALLOWED_EXPORT_MODULES, assert_offboarding_transition, OffboardingWorkflowStage


def test_unknown_module_not_allowed() -> None:
    assert "payment_cards" not in ALLOWED_EXPORT_MODULES


def test_offboarding_pending_to_approved() -> None:
    assert_offboarding_transition(OffboardingWorkflowStage.PENDING_APPROVAL, OffboardingWorkflowStage.APPROVED)


def test_offboarding_closed_terminal() -> None:
    with pytest.raises(ValueError):
        assert_offboarding_transition(OffboardingWorkflowStage.CLOSED, OffboardingWorkflowStage.APPROVED)
