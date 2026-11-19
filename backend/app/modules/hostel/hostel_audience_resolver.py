"""Resolve hostel announcement audiences from active residency."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.ids import to_object_id
from app.common.roles import Role
from app.modules.auth.models import User
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus


_ACTIVE_RESIDENT = frozenset(
    {
        HostelResidentStatus.CHECKED_IN.value,
        HostelResidentStatus.TEMPORARILY_OUTSIDE.value,
        HostelResidentStatus.AWAITING_CHECKIN.value,
    }
)


async def resolve_hostel_audience(tenant_id: PydanticObjectId, audience: dict) -> list[PydanticObjectId]:
    """Keys: all_residents, hostel_codes, building_codes, block_codes, floor_ids, resident_user_ids, staff_only."""
    if audience.get("staff_only"):
        admins = await User.find({"tenant_id": tenant_id, "role": Role.HOSTEL_ADMIN.value}).to_list()
        return [u.id for u in admins]

    user_ids: set[PydanticObjectId] = set()
    for raw in audience.get("resident_user_ids", []):
        user_ids.add(to_object_id(str(raw), "resident_user_id"))

    if audience.get("all_residents"):
        rows = await HostelResident.find({"tenant_id": tenant_id, "status": {"$in": list(_ACTIVE_RESIDENT)}}).to_list()
        return list({r.student_user_id for r in rows})

    q: dict = {"tenant_id": tenant_id, "status": {"$in": list(_ACTIVE_RESIDENT)}}
    hostel_codes = {c.upper() for c in audience.get("hostel_codes", [])}
    building_codes = {c.upper() for c in audience.get("building_codes", [])}
    block_codes = {c.upper() for c in audience.get("block_codes", [])}
    floor_ids = set(audience.get("floor_ids", []))

    rows = await HostelResident.find(q).to_list()
    for r in rows:
        if hostel_codes and (not r.hostel_code or r.hostel_code.upper() not in hostel_codes):
            continue
        if building_codes and r.building_code.upper() not in building_codes:
            continue
        if block_codes and r.block_code.upper() not in block_codes:
            continue
        if floor_ids and r.floor_id and r.floor_id not in floor_ids:
            continue
        user_ids.add(r.student_user_id)
    return list(user_ids)