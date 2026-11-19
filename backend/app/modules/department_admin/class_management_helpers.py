"""Shared batch/section helpers (avoids circular imports with section transfers)."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.core.exceptions import AppError
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.department_admin.department_scope import department_programme_codes
from app.modules.department_admin.models import DepartmentBatch, DepartmentSection
from app.modules.students.models import StudentProfile


async def assert_programme_in_department(institution: InstitutionDepartment, programme_code: str) -> None:
    if programme_code.upper() not in await department_programme_codes(institution):
        raise AppError(code="FORBIDDEN", message="Programme is outside department", status_code=403)


async def section_enrolled_count(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    *,
    programme_code: str,
    batch_label: str,
    section_code: str,
) -> int:
    return await StudentProfile.find(
        {
            "tenant_id": tenant_id,
            "department_id": central_id,
            "programme_code": programme_code.upper(),
            "batch_label": batch_label,
            "section_code": section_code.upper(),
        }
    ).count()


async def resolve_section_def(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    programme_code: str,
    batch_label: str,
    section_code: str,
    *,
    session=None,
) -> DepartmentSection:
    batch = await DepartmentBatch.find_one(
        Eq(DepartmentBatch.tenant_id, tenant_id),
        Eq(DepartmentBatch.central_department_id, central_id),
        Eq(DepartmentBatch.programme_code, programme_code.upper()),
        Eq(DepartmentBatch.batch_label, batch_label),
        session=session,
    )
    if batch is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown batch for department", status_code=422)
    section = await DepartmentSection.find_one(
        Eq(DepartmentSection.tenant_id, tenant_id),
        Eq(DepartmentSection.department_batch_id, batch.id),
        Eq(DepartmentSection.section_code, section_code.upper()),
        session=session,
    )
    if section is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown section for batch", status_code=422)
    return section