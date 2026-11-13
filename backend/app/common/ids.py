"""ObjectId parsing for path and header values."""

from beanie import PydanticObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status


def to_object_id(value: str, field_name: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except (InvalidId, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {field_name}",
        ) from exc
