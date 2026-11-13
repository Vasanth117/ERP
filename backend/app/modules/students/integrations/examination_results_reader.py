"""Central published semester results reads."""

from beanie import PydanticObjectId

from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.examinations.result_publication_models import SemesterResultPublication, SemesterResultSubjectMark


async def published_result_bundle(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str
) -> SemesterResultPublication | None:
    doc = await SemesterResultPublication.find_one(
        {"tenant_id": tenant_id, "student_user_id": user_id, "season_id": season_id}
    )
    if doc is None or doc.status != SemesterResultPublicationStatus.PUBLISHED:
        return None
    return doc


async def published_subject_marks(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, *, season_id: str | None = None
) -> list[SemesterResultSubjectMark]:
    filters: dict = {
        "tenant_id": tenant_id,
        "student_user_id": user_id,
        "published": True,
    }
    if season_id:
        filters["season_id"] = season_id
    return await SemesterResultSubjectMark.find(filters).sort([("season_id", -1), ("course_code", 1)]).to_list()


async def result_publication_status(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str
) -> SemesterResultPublication | None:
    return await SemesterResultPublication.find_one(
        {"tenant_id": tenant_id, "student_user_id": user_id, "season_id": season_id}
    )


async def arrear_results(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId,
) -> list[SemesterResultSubjectMark]:
    return await SemesterResultSubjectMark.find(
        {
            "tenant_id": tenant_id,
            "student_user_id": user_id,
            "is_arrear": True,
            "published": True,
        }
    ).sort("-published_at").to_list()
