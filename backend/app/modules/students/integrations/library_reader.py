"""Read central library data for a student."""

from beanie import PydanticObjectId

from app.modules.library.library_enums import LibraryCirculationStatus, LibraryCopyStatus, LibraryFineStatus
from app.modules.library.library_models import (
    LibraryCatalogItem,
    LibraryCirculation,
    LibraryCopy,
    LibraryDigitalResource,
    LibraryFine,
    LibraryReservation,
)


async def catalogue(tenant_id: PydanticObjectId, *, q: str | None = None, limit: int = 50) -> list[LibraryCatalogItem]:
    filters: dict = {"tenant_id": tenant_id, "published": True}
    if q:
        filters["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"isbn": q},
            {"authors": q},
        ]
    return await LibraryCatalogItem.find(filters).sort("title").limit(limit).to_list()


async def availability_counts(tenant_id: PydanticObjectId, book_ids: list[str]) -> dict[str, int]:
    if not book_ids:
        return {}
    copies = await LibraryCopy.find(
        {
            "tenant_id": tenant_id,
            "book_id": {"$in": book_ids},
            "status": LibraryCopyStatus.AVAILABLE,
        }
    ).to_list()
    counts: dict[str, int] = {}
    for c in copies:
        counts[c.book_id] = counts.get(c.book_id, 0) + 1
    return counts


async def circulations_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[LibraryCirculation]:
    return await LibraryCirculation.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort("-issued_at").to_list()


async def active_circulations(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[LibraryCirculation]:
    return await LibraryCirculation.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "status": {"$in": [LibraryCirculationStatus.ACTIVE, LibraryCirculationStatus.OVERDUE]},
        }
    ).sort("due_at").to_list()


async def reservations_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[LibraryReservation]:
    return await LibraryReservation.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort("-created_at").to_list()


async def fines_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[LibraryFine]:
    return await LibraryFine.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort("-created_at").to_list()


async def digital_resources(tenant_id: PydanticObjectId, limit: int = 50) -> list[LibraryDigitalResource]:
    return await LibraryDigitalResource.find({"tenant_id": tenant_id, "published": True}).sort("title").limit(limit).to_list()


async def borrowing_history(tenant_id: PydanticObjectId, user_id: PydanticObjectId, limit: int = 100) -> list[LibraryCirculation]:
    return (
        await LibraryCirculation.find({"tenant_id": tenant_id, "student_user_id": user_id})
        .sort("-issued_at")
        .limit(limit)
        .to_list()
    )
