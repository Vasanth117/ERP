"""Onboarding state machine tests."""

import pytest

from app.modules.tenants.enums import OnboardingStage, assert_onboarding_transition


def test_valid_transition() -> None:
    assert_onboarding_transition(OnboardingStage.DRAFT, OnboardingStage.SUBMITTED)


def test_invalid_transition_raises() -> None:
    with pytest.raises(ValueError):
        assert_onboarding_transition(OnboardingStage.COMPLETED, OnboardingStage.DRAFT)
