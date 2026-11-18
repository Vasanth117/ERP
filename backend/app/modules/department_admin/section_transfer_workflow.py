"""Section transfer scenario classification and approval chain."""

from beanie import PydanticObjectId

from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.department_admin.models import (
    DepartmentRequestStatus,
    DepartmentSetting,
    SectionTransferApprovalRecord,
    SectionTransferApprovalRole,
    SectionTransferInitiator,
    SectionTransferScenario,
)
from app.authorization.permissions import Permission
from app.modules.college_admin.models import InstitutionSettings
from beanie.odm.operators.find.comparison import Eq


async def _institution_requires_college_approval_for_inter_batch(tenant_id: PydanticObjectId) -> bool:
    settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    if settings is None:
        return True
    value = settings.settings.get("inter_batch_section_transfer_requires_college_approval")
    if value is None:
        return True
    return bool(value)


async def _department_transfer_delegated(tenant_id: PydanticObjectId, institution_department_id: PydanticObjectId) -> bool:
    row = await DepartmentSetting.find_one(
        Eq(DepartmentSetting.tenant_id, tenant_id),
        Eq(DepartmentSetting.institution_department_id, institution_department_id),
        Eq(DepartmentSetting.setting_key, "delegation_enabled"),
    )
    if row is None:
        return False
    return bool(row.setting_value)


def classify_scenario(
    *,
    source_department_id: PydanticObjectId,
    destination_department_id: PydanticObjectId | None,
    from_batch_label: str,
    to_batch_label: str,
    tenant_match: bool,
) -> SectionTransferScenario:
    if not tenant_match:
        return SectionTransferScenario.CROSS_COLLEGE
    dest = destination_department_id or source_department_id
    if dest != source_department_id:
        return SectionTransferScenario.CROSS_DEPARTMENT
    if from_batch_label != to_batch_label:
        return SectionTransferScenario.SAME_DEPT_INTER_BATCH
    return SectionTransferScenario.SAME_BATCH_SECTION


async def build_approval_chain(
    *,
    tenant_id: PydanticObjectId,
    institution_department_id: PydanticObjectId,
    scenario: SectionTransferScenario,
) -> list[SectionTransferApprovalRecord]:
    if scenario == SectionTransferScenario.CROSS_COLLEGE:
        raise AppError(
            code="FORBIDDEN",
            message="Cross-college transfers must use college administration",
            status_code=403,
        )
    if scenario == SectionTransferScenario.CROSS_DEPARTMENT:
        return [
            SectionTransferApprovalRecord(role=SectionTransferApprovalRole.SOURCE_DEPARTMENT_ADMIN),
            SectionTransferApprovalRecord(role=SectionTransferApprovalRole.DESTINATION_DEPARTMENT_ADMIN),
            SectionTransferApprovalRecord(role=SectionTransferApprovalRole.COLLEGE_ADMIN),
        ]
    if scenario == SectionTransferScenario.SAME_DEPT_INTER_BATCH:
        steps = [SectionTransferApprovalRecord(role=SectionTransferApprovalRole.SOURCE_DEPARTMENT_ADMIN)]
        if await _institution_requires_college_approval_for_inter_batch(tenant_id):
            steps.append(SectionTransferApprovalRecord(role=SectionTransferApprovalRole.COLLEGE_ADMIN))
        return steps
    if await _department_transfer_delegated(tenant_id, institution_department_id):
        return [SectionTransferApprovalRecord(role=SectionTransferApprovalRole.SOURCE_DEPARTMENT_ADMIN)]
    return [SectionTransferApprovalRecord(role=SectionTransferApprovalRole.COLLEGE_ADMIN)]


def next_pending_step(steps: list[SectionTransferApprovalRecord]) -> SectionTransferApprovalRecord | None:
    for step in steps:
        if step.status == DepartmentRequestStatus.PENDING:
            return step
    return None


def all_steps_approved(steps: list[SectionTransferApprovalRecord]) -> bool:
    return bool(steps) and all(s.status == DepartmentRequestStatus.APPROVED for s in steps)


def assert_reviewer_may_act(
    *,
    scope: AccessScope,
    user_id: PydanticObjectId,
    requested_by: PydanticObjectId,
    initiator: SectionTransferInitiator,
    step_role: SectionTransferApprovalRole,
    source_central_id: PydanticObjectId,
    destination_central_id: PydanticObjectId | None,
    user_department_id: PydanticObjectId | None,
    user_role: Role,
) -> None:
    if step_role == SectionTransferApprovalRole.SOURCE_DEPARTMENT_ADMIN:
        if user_role != Role.DEPARTMENT_ADMIN or user_department_id != source_central_id:
            raise AppError(code="FORBIDDEN", message="Source department approval required", status_code=403)
        if initiator == SectionTransferInitiator.STUDENT and user_id == requested_by:
            raise AppError(code="FORBIDDEN", message="Requester cannot approve their own transfer request", status_code=403)
        if user_id == requested_by:
            raise AppError(code="FORBIDDEN", message="Separation of duties: requester cannot approve", status_code=403)
        return
    if step_role == SectionTransferApprovalRole.DESTINATION_DEPARTMENT_ADMIN:
        dest = destination_central_id or source_central_id
        if user_role != Role.DEPARTMENT_ADMIN or user_department_id != dest:
            raise AppError(code="FORBIDDEN", message="Destination department approval required", status_code=403)
        if user_id == requested_by:
            raise AppError(code="FORBIDDEN", message="Separation of duties: requester cannot approve", status_code=403)
        return
    if step_role == SectionTransferApprovalRole.COLLEGE_ADMIN:
        if user_role != Role.COLLEGE_ADMIN:
            raise AppError(code="FORBIDDEN", message="College admin approval required", status_code=403)
        if Permission.STUDENT_ADMIN_MANAGE not in scope.effective_permissions:
            raise AppError(code="FORBIDDEN", message="College admin student authority required", status_code=403)
        return
    raise AppError(code="FORBIDDEN", message="Invalid approval role", status_code=403)