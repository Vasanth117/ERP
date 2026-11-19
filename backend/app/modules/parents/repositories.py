"""Parent portal data access."""

from beanie import PydanticObjectId

from app.modules.parents.enums import (
    ACTIVE_RELATIONSHIP_STATUSES,
    PENDING_LINK_STATUSES,
    ParentLinkRequestStatus,
    ParentRelationshipStatus,
)
from app.modules.parents.models import (
    ParentProfile,
    ParentRelationshipPermissions,
    ParentStudentLinkRequest,
    ParentStudentRelationship,
)


class ParentProfileRepository:
    async def get_by_user(self, tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> ParentProfile | None:
        return await ParentProfile.find_one({"tenant_id": tenant_id, "user_id": user_id})


class ParentRelationshipRepository:
    async def get_pair(
        self,
        tenant_id: PydanticObjectId,
        parent_user_id: PydanticObjectId,
        student_user_id: PydanticObjectId,
    ) -> ParentStudentRelationship | None:
        return await ParentStudentRelationship.find_one(
            {"tenant_id": tenant_id, "parent_user_id": parent_user_id, "student_user_id": student_user_id}
        )

    async def list_for_parent(
        self,
        tenant_id: PydanticObjectId,
        parent_user_id: PydanticObjectId,
        *,
        statuses: frozenset[ParentRelationshipStatus] | None = None,
    ) -> list[ParentStudentRelationship]:
        filters: dict = {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
        if statuses is not None:
            filters["status"] = {"$in": [s.value for s in statuses]}
        return await ParentStudentRelationship.find(filters).sort("-updated_at").to_list()

    async def list_active_for_parent(
        self, tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId
    ) -> list[ParentStudentRelationship]:
        return await self.list_for_parent(tenant_id, parent_user_id, statuses=ACTIVE_RELATIONSHIP_STATUSES)

    async def permissions_for_relationship(
        self, tenant_id: PydanticObjectId, relationship_id: PydanticObjectId
    ) -> ParentRelationshipPermissions | None:
        return await ParentRelationshipPermissions.find_one(
            {"tenant_id": tenant_id, "relationship_id": relationship_id}
        )


class ParentLinkRequestRepository:
    async def pending_for_pair(
        self,
        tenant_id: PydanticObjectId,
        parent_user_id: PydanticObjectId,
        student_user_id: PydanticObjectId,
    ) -> ParentStudentLinkRequest | None:
        rows = await ParentStudentLinkRequest.find(
            {
                "tenant_id": tenant_id,
                "parent_user_id": parent_user_id,
                "student_user_id": student_user_id,
                "status": {"$in": [s.value for s in PENDING_LINK_STATUSES]},
            }
        ).to_list()
        return rows[0] if rows else None

    async def list_for_parent(
        self, tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId
    ) -> list[ParentStudentLinkRequest]:
        return await ParentStudentLinkRequest.find(
            {"tenant_id": tenant_id, "parent_user_id": parent_user_id}
        ).sort("-created_at").to_list()

    async def list_pending_for_tenant(self, tenant_id: PydanticObjectId, limit: int = 200) -> list[ParentStudentLinkRequest]:
        return await ParentStudentLinkRequest.find(
            {"tenant_id": tenant_id, "status": ParentLinkRequestStatus.PENDING_VERIFICATION.value}
        ).sort("-created_at").limit(limit).to_list()