"""Demo mode header parsing for college admin showcase tenant."""

import pytest

from app.modules.demo.guard import demo_college_view_requested


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, False),
        ("", False),
        ("0", False),
        ("1", True),
        ("true", True),
        ("TRUE", True),
        ("yes", True),
        ("on", True),
    ],
)
def test_demo_college_view_requested(value: str | None, expected: bool) -> None:
    assert demo_college_view_requested(value) is expected