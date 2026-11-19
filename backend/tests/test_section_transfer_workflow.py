"""Section transfer approval chain (no Mongo)."""

from beanie import PydanticObjectId

from app.modules.department_admin.models import (
    DepartmentRequestStatus,
    SectionTransferApprovalRole,
    SectionTransferScenario,
)
from app.modules.department_admin.section_transfer_workflow import (
    all_steps_approved,
    classify_scenario,
    next_pending_step,
)


def test_classify_same_batch_section() -> None:
    dept = PydanticObjectId()
    assert (
        classify_scenario(
            source_department_id=dept,
            destination_department_id=None,
            from_batch_label="2024",
            to_batch_label="2024",
            tenant_match=True,
        )
        == SectionTransferScenario.SAME_BATCH_SECTION
    )


def test_classify_inter_batch() -> None:
    dept = PydanticObjectId()
    assert (
        classify_scenario(
            source_department_id=dept,
            destination_department_id=None,
            from_batch_label="2023",
            to_batch_label="2024",
            tenant_match=True,
        )
        == SectionTransferScenario.SAME_DEPT_INTER_BATCH
    )


def test_approval_progression() -> None:
    from app.modules.department_admin.models import SectionTransferApprovalRecord

    steps = [
        SectionTransferApprovalRecord(role=SectionTransferApprovalRole.SOURCE_DEPARTMENT_ADMIN),
        SectionTransferApprovalRecord(role=SectionTransferApprovalRole.COLLEGE_ADMIN),
    ]
    pending = next_pending_step(steps)
    assert pending is not None
    assert pending.role == SectionTransferApprovalRole.SOURCE_DEPARTMENT_ADMIN
    pending.status = DepartmentRequestStatus.APPROVED
    assert not all_steps_approved(steps)
    steps[1].status = DepartmentRequestStatus.APPROVED
    assert all_steps_approved(steps)