"""College admin repositories."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.college_admin.models import (
    InstitutionActivityLog,
    InstitutionBranding,
    InstitutionCampus,
    InstitutionConfigurationVersion,
    InstitutionProfile,
    InstitutionSettings,
)


class InstitutionProfileRepository:
    async def get_by_tenant(self, tenant_id: PydanticObjectId) -> InstitutionProfile | None:
        return await InstitutionProfile.find_one(Eq(InstitutionProfile.tenant_id, tenant_id))

    async def save(self, doc: InstitutionProfile) -> InstitutionProfile:
        await doc.save()
        return doc


class InstitutionCampusRepository:
    async def list_for_tenant(self, tenant_id: PydanticObjectId, *, active_only: bool = False) -> list[InstitutionCampus]:
        query = InstitutionCampus.find(Eq(InstitutionCampus.tenant_id, tenant_id))
        if active_only:
            query = query.find(Eq(InstitutionCampus.is_active, True))
        return await query.sort("+campus_code").to_list()

    async def get_by_id(self, tenant_id: PydanticObjectId, campus_id: PydanticObjectId) -> InstitutionCampus | None:
        doc = await InstitutionCampus.get(campus_id)
        if doc is None or doc.tenant_id != tenant_id:
            return None
        return doc

    async def get_by_code(self, tenant_id: PydanticObjectId, campus_code: str) -> InstitutionCampus | None:
        return await InstitutionCampus.find_one(
            Eq(InstitutionCampus.tenant_id, tenant_id),
            Eq(InstitutionCampus.campus_code, campus_code),
        )


class InstitutionSettingsRepository:
    async def get_settings(self, tenant_id: PydanticObjectId) -> InstitutionSettings | None:
        return await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))

    async def get_branding(self, tenant_id: PydanticObjectId) -> InstitutionBranding | None:
        return await InstitutionBranding.find_one(Eq(InstitutionBranding.tenant_id, tenant_id))


class InstitutionHistoryRepository:
    async def list_history(self, tenant_id: PydanticObjectId, *, limit: int = 50) -> list[InstitutionConfigurationVersion]:
        return await (
            InstitutionConfigurationVersion.find(Eq(InstitutionConfigurationVersion.tenant_id, tenant_id))
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )

    async def insert_version(self, doc: InstitutionConfigurationVersion) -> None:
        await doc.insert()


class InstitutionActivityRepository:
    async def list_recent(self, tenant_id: PydanticObjectId, *, limit: int = 30) -> list[InstitutionActivityLog]:
        return await (
            InstitutionActivityLog.find(Eq(InstitutionActivityLog.tenant_id, tenant_id))
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )

    async def append(self, doc: InstitutionActivityLog) -> None:
        await doc.insert()
