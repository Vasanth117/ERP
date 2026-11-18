"""Circulation issue/return/renew enumerations."""

from enum import Enum


class ReturnDisposition(str, Enum):
    """How a physical copy is returned to inventory."""

    GOOD = "good"
    DAMAGED = "damaged"
    LOST = "lost"