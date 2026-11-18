"""BSON-safe time fields for MongoDB (Beanie cannot encode plain datetime.time)."""

from datetime import time
from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer


def _parse_time_value(value: Any) -> time:
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        parts = value.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(float(parts[2])) if len(parts) > 2 else 0
        return time(hour, minute, second)
    raise TypeError(f"Unsupported time value: {type(value)!r}")


def _serialize_time(value: time) -> str:
    return value.strftime("%H:%M:%S")


MongoTime = Annotated[time, BeforeValidator(_parse_time_value), PlainSerializer(_serialize_time, return_type=str)]