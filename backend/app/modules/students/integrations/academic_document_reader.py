"""Published academic document reads."""

from beanie import PydanticObjectId

from app.modules.examinations.academic_document_models import AcademicDocumentPublication, AcademicDocumentStatus, AcademicDocumentType


async def published_documents(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    document_type: AcademicDocumentType | None = None,
    season_id: str | None = None,
) -> list[AcademicDocumentPublication]:
    filters: dict = {
        "tenant_id": tenant_id,
        "student_user_id": user_id,
        "status": AcademicDocumentStatus.PUBLISHED,
    }
    if document_type is not None:
        filters["document_type"] = document_type
    if season_id:
        filters["season_id"] = season_id
    return await AcademicDocumentPublication.find(filters).sort("-published_at").to_list()


async def published_document(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, document_id: str
) -> AcademicDocumentPublication | None:
    doc = await AcademicDocumentPublication.find_one(
        {
            "tenant_id": tenant_id,
            "document_id": document_id,
            "student_user_id": user_id,
            "status": AcademicDocumentStatus.PUBLISHED,
        }
    )
    return doc


async def document_history_including_superseded(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, document_type: AcademicDocumentType | None = None
) -> list[AcademicDocumentPublication]:
    filters: dict = {"tenant_id": tenant_id, "student_user_id": user_id}
    if document_type:
        filters["document_type"] = document_type
    return await AcademicDocumentPublication.find(filters).sort("-published_at").to_list()
