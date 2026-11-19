"""Fee structure persistence queries."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.modules.accounts_finance.enums import FeeStructureLifecycleStatus
from app.modules.accounts_finance.models import FinanceFeeStructure


async def find_conflicting_active_structure(
    tenant_id: PydanticObjectId,
    *,
    programme_code: str,
    academic_year_label: str,
    semester_label: str,
    exclude_structure_id: str | None = None,
) -> FinanceFeeStructure | None:
    query = FinanceFeeStructure.find(
        Eq(FinanceFeeStructure.tenant_id, tenant_id),
        Eq(FinanceFeeStructure.programme_code, programme_code.upper()),
        Eq(FinanceFeeStructure.academic_year_label, academic_year_label),
        Eq(FinanceFeeStructure.semester_label, semester_label),
        In(
            FinanceFeeStructure.status,
            [
                FeeStructureLifecycleStatus.ACTIVE,
                FeeStructureLifecycleStatus.APPROVED,
                FeeStructureLifecycleStatus.SCHEDULED,
            ],
        ),
    )
    rows = await query.to_list()
    for row in rows:
        if exclude_structure_id and row.structure_id == exclude_structure_id:
            continue
        return row
    return None


def validate_effective_period(effective_from: date | None, effective_to: date | None) -> None:
    if effective_from and effective_to and effective_to < effective_from:
        from app.core.exceptions import AppError

        raise AppError(code="VALIDATION_ERROR", message="effective_to must be on or after effective_from", status_code=422)